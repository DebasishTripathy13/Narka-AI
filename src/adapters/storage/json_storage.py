"""JSON file storage adapter."""

from typing import Optional, List, Any
from datetime import datetime
import json
from pathlib import Path

from ...core.interfaces.storage import StorageProvider


class JSONFileStorage(StorageProvider):
    """
    JSON file-based storage implementation.
    
    Simple storage for small-scale usage or testing.
    Each key is stored as a separate JSON file.
    """
    
    def __init__(self, base_path: str = "./data"):
        self._base_path = Path(base_path)
    
    def initialize(self) -> None:
        """Initialize the storage directory."""
        self._base_path.mkdir(parents=True, exist_ok=True)
    
    def _get_file_path(self, key: str) -> Path:
        """Get file path for a key."""
        # Sanitize key to be a valid filename
        safe_key = "".join(c if c.isalnum() or c in "-_." else "_" for c in key)
        return self._base_path / f"{safe_key}.json"
    
    def save(self, key: str, data: Any) -> bool:
        """Save data to a JSON file."""
        try:
            file_path = self._get_file_path(key)
            
            wrapper = {
                "key": key,
                "data": data,
                "saved_at": datetime.now().isoformat(),
            }
            
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(wrapper, f, indent=2, default=str)
            
            return True
        except Exception:
            return False
    
    def load(self, key: str) -> Optional[Any]:
        """Load data from a JSON file."""
        try:
            file_path = self._get_file_path(key)
            
            if not file_path.exists():
                return None
            
            with open(file_path, "r", encoding="utf-8") as f:
                wrapper = json.load(f)
            
            return wrapper.get("data")
        except Exception:
            return None
    
    def delete(self, key: str) -> bool:
        """Delete a JSON file."""
        try:
            file_path = self._get_file_path(key)
            
            if file_path.exists():
                file_path.unlink()
                return True
            return False
        except Exception:
            return False
    
    def list_keys(self, prefix: Optional[str] = None) -> List[str]:
        """List all keys (file names without extension)."""
        try:
            keys = []
            
            for file_path in self._base_path.glob("*.json"):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        wrapper = json.load(f)
                        key = wrapper.get("key", file_path.stem)
                        
                        if prefix is None or key.startswith(prefix):
                            keys.append(key)
                except Exception:
                    continue
            
            return keys
        except Exception:
            return []
    
    def exists(self, key: str) -> bool:
        """Check if a key exists."""
        return self._get_file_path(key).exists()
    
    def get_size(self) -> int:
        """Get total size of all stored files."""
        total = 0
        for file_path in self._base_path.glob("*.json"):
            total += file_path.stat().st_size
        return total
