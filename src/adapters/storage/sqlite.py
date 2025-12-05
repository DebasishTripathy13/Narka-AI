"""SQLite storage adapter for investigations and results."""

from typing import Optional, List, Any, Dict
from datetime import datetime
import sqlite3
import json
import threading
from pathlib import Path

from ...core.interfaces.storage import StorageProvider
from ...core.entities.investigation import Investigation, InvestigationStatus
from ...core.entities.search_result import SearchResult
from ...core.entities.scraped_content import ScrapedContent


class SQLiteStorage(StorageProvider):
    """
    SQLite-based storage implementation.
    
    Provides persistent storage for investigations, search results,
    and scraped content with full-text search capabilities.
    """
    
    def __init__(self, db_path: str = "robin_data.db"):
        self._db_path = db_path
        self._local = threading.local()
        self._initialized = False
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local database connection."""
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            self._local.connection = sqlite3.connect(
                self._db_path,
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
            )
            self._local.connection.row_factory = sqlite3.Row
        return self._local.connection
    
    def initialize(self) -> None:
        """Initialize the database schema."""
        if self._initialized:
            return
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Investigations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS investigations (
                id TEXT PRIMARY KEY,
                query TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                metadata TEXT,
                search_results_count INTEGER DEFAULT 0,
                scraped_pages_count INTEGER DEFAULT 0,
                entities_count INTEGER DEFAULT 0,
                summary TEXT,
                tags TEXT
            )
        """)
        
        # Search results table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS search_results (
                id TEXT PRIMARY KEY,
                investigation_id TEXT,
                url TEXT NOT NULL,
                title TEXT,
                description TEXT,
                source_engine TEXT,
                query TEXT,
                discovered_at TIMESTAMP,
                relevance_score REAL DEFAULT 0.0,
                is_scraped INTEGER DEFAULT 0,
                raw_html TEXT,
                metadata TEXT,
                FOREIGN KEY (investigation_id) REFERENCES investigations(id)
            )
        """)
        
        # Scraped content table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scraped_content (
                id TEXT PRIMARY KEY,
                search_result_id TEXT,
                investigation_id TEXT,
                url TEXT NOT NULL,
                title TEXT,
                raw_html TEXT,
                clean_text TEXT,
                scraped_at TIMESTAMP,
                status_code INTEGER,
                content_type TEXT,
                content_length INTEGER,
                language TEXT,
                metadata TEXT,
                FOREIGN KEY (search_result_id) REFERENCES search_results(id),
                FOREIGN KEY (investigation_id) REFERENCES investigations(id)
            )
        """)
        
        # Extracted entities table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS extracted_entities (
                id TEXT PRIMARY KEY,
                investigation_id TEXT,
                scraped_content_id TEXT,
                entity_type TEXT NOT NULL,
                value TEXT NOT NULL,
                confidence REAL DEFAULT 1.0,
                context TEXT,
                source_url TEXT,
                discovered_at TIMESTAMP,
                metadata TEXT,
                FOREIGN KEY (investigation_id) REFERENCES investigations(id),
                FOREIGN KEY (scraped_content_id) REFERENCES scraped_content(id)
            )
        """)
        
        # Search history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                results_count INTEGER DEFAULT 0,
                engines_used TEXT,
                duration_seconds REAL
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_investigations_status ON investigations(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_investigations_created ON investigations(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_search_results_investigation ON search_results(investigation_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_search_results_url ON search_results(url)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_scraped_content_investigation ON scraped_content(investigation_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_entities_type ON extracted_entities(entity_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_entities_value ON extracted_entities(value)")
        
        # Full-text search
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS search_results_fts USING fts5(
                title, description, content='search_results', content_rowid='rowid'
            )
        """)
        
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS scraped_content_fts USING fts5(
                title, clean_text, content='scraped_content', content_rowid='rowid'
            )
        """)
        
        conn.commit()
        self._initialized = True
    
    def save(self, key: str, data: Any) -> bool:
        """Save data with a key."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO key_value_store (key, value, updated_at)
                VALUES (?, ?, ?)
            """, (key, json.dumps(data), datetime.now()))
            conn.commit()
            return True
        except Exception:
            return False
    
    def load(self, key: str) -> Optional[Any]:
        """Load data by key."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT value FROM key_value_store WHERE key = ?", (key,))
            row = cursor.fetchone()
            if row:
                return json.loads(row[0])
            return None
        except Exception:
            return None
    
    def delete(self, key: str) -> bool:
        """Delete data by key."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM key_value_store WHERE key = ?", (key,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception:
            return False
    
    def list_keys(self, prefix: Optional[str] = None) -> List[str]:
        """List all keys with optional prefix filter."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            if prefix:
                cursor.execute(
                    "SELECT key FROM key_value_store WHERE key LIKE ?",
                    (f"{prefix}%",)
                )
            else:
                cursor.execute("SELECT key FROM key_value_store")
            
            return [row[0] for row in cursor.fetchall()]
        except Exception:
            return []
    
    # Investigation-specific methods
    
    def save_investigation(self, investigation: Investigation) -> bool:
        """Save an investigation."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO investigations (
                    id, query, status, created_at, updated_at, completed_at,
                    metadata, search_results_count, scraped_pages_count,
                    entities_count, summary, tags
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                investigation.id,
                investigation.query,
                investigation.status.value,
                investigation.created_at,
                investigation.updated_at,
                investigation.completed_at,
                json.dumps(investigation.metadata),
                len(investigation.search_results),
                len(investigation.scraped_content),
                len(investigation.extracted_entities),
                investigation.summary,
                json.dumps(investigation.tags),
            ))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error saving investigation: {e}")
            return False
    
    def load_investigation(self, investigation_id: str) -> Optional[Investigation]:
        """Load an investigation by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "SELECT * FROM investigations WHERE id = ?",
                (investigation_id,)
            )
            row = cursor.fetchone()
            
            if not row:
                return None
            
            return Investigation(
                id=row["id"],
                query=row["query"],
                status=InvestigationStatus(row["status"]),
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                completed_at=row["completed_at"],
                metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                summary=row["summary"],
                tags=json.loads(row["tags"]) if row["tags"] else [],
            )
        except Exception as e:
            print(f"Error loading investigation: {e}")
            return None
    
    def list_investigations(
        self,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Investigation]:
        """List investigations with optional filtering."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            if status:
                cursor.execute("""
                    SELECT * FROM investigations
                    WHERE status = ?
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                """, (status, limit, offset))
            else:
                cursor.execute("""
                    SELECT * FROM investigations
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                """, (limit, offset))
            
            investigations = []
            for row in cursor.fetchall():
                investigations.append(Investigation(
                    id=row["id"],
                    query=row["query"],
                    status=InvestigationStatus(row["status"]),
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                    completed_at=row["completed_at"],
                    metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                    summary=row["summary"],
                    tags=json.loads(row["tags"]) if row["tags"] else [],
                ))
            
            return investigations
        except Exception:
            return []
    
    def save_search_result(
        self,
        result: SearchResult,
        investigation_id: Optional[str] = None
    ) -> bool:
        """Save a search result."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO search_results (
                    id, investigation_id, url, title, description,
                    source_engine, query, discovered_at, relevance_score,
                    is_scraped, raw_html, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result.id,
                investigation_id,
                result.url,
                result.title,
                result.description,
                result.source_engine,
                result.query,
                result.discovered_at,
                result.relevance_score,
                1 if result.is_scraped else 0,
                result.raw_html,
                json.dumps(result.metadata),
            ))
            conn.commit()
            return True
        except Exception:
            return False
    
    def save_scraped_content(
        self,
        content: ScrapedContent,
        investigation_id: Optional[str] = None
    ) -> bool:
        """Save scraped content."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO scraped_content (
                    id, search_result_id, investigation_id, url, title,
                    raw_html, clean_text, scraped_at, status_code,
                    content_type, content_length, language, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                content.id,
                content.search_result_id,
                investigation_id,
                content.url,
                content.title,
                content.raw_html,
                content.clean_text,
                content.scraped_at,
                content.status_code,
                content.content_type,
                content.content_length,
                content.language,
                json.dumps(content.metadata),
            ))
            conn.commit()
            return True
        except Exception:
            return False
    
    def search_full_text(self, query: str, table: str = "search_results") -> List[Dict]:
        """Perform full-text search."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            fts_table = f"{table}_fts"
            cursor.execute(f"""
                SELECT rowid, * FROM {fts_table}
                WHERE {fts_table} MATCH ?
                ORDER BY rank
                LIMIT 100
            """, (query,))
            
            return [dict(row) for row in cursor.fetchall()]
        except Exception:
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get storage statistics."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        try:
            cursor.execute("SELECT COUNT(*) FROM investigations")
            stats["total_investigations"] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM search_results")
            stats["total_search_results"] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM scraped_content")
            stats["total_scraped_pages"] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM extracted_entities")
            stats["total_entities"] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM search_history")
            stats["total_searches"] = cursor.fetchone()[0]
            
            # Database file size
            db_file = Path(self._db_path)
            if db_file.exists():
                stats["database_size_bytes"] = db_file.stat().st_size
            
        except Exception:
            pass
        
        return stats
    
    def close(self) -> None:
        """Close the database connection."""
        if hasattr(self._local, 'connection') and self._local.connection:
            self._local.connection.close()
            self._local.connection = None
