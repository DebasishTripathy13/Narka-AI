"""Abstract interface for storage providers."""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, TypeVar, Generic
from datetime import datetime


T = TypeVar('T')


class StorageProvider(ABC, Generic[T]):
    """
    Abstract base class for storage providers.
    
    Implementations can use SQLite, PostgreSQL, MongoDB, etc.
    """
    
    @abstractmethod
    def initialize(self) -> None:
        """Initialize the storage (create tables, indexes, etc.)."""
        pass
    
    @abstractmethod
    def close(self) -> None:
        """Close the storage connection."""
        pass
    
    @abstractmethod
    def save(self, item: T) -> str:
        """
        Save an item to storage.
        
        Args:
            item: The item to save
            
        Returns:
            The ID of the saved item
        """
        pass
    
    @abstractmethod
    def get(self, item_id: str) -> Optional[T]:
        """
        Get an item by ID.
        
        Args:
            item_id: The ID to look up
            
        Returns:
            The item if found, None otherwise
        """
        pass
    
    @abstractmethod
    def update(self, item_id: str, item: T) -> bool:
        """
        Update an existing item.
        
        Args:
            item_id: The ID of the item to update
            item: The updated item data
            
        Returns:
            True if updated, False if not found
        """
        pass
    
    @abstractmethod
    def delete(self, item_id: str) -> bool:
        """
        Delete an item by ID.
        
        Args:
            item_id: The ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        pass
    
    @abstractmethod
    def list(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0,
        order_by: Optional[str] = None,
        descending: bool = True
    ) -> List[T]:
        """
        List items with optional filtering and pagination.
        
        Args:
            filters: Key-value filters to apply
            limit: Maximum number of items to return
            offset: Number of items to skip
            order_by: Field to sort by
            descending: Sort direction
            
        Returns:
            List of matching items
        """
        pass
    
    @abstractmethod
    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count items matching filters.
        
        Args:
            filters: Key-value filters to apply
            
        Returns:
            Count of matching items
        """
        pass
    
    def exists(self, item_id: str) -> bool:
        """Check if an item exists."""
        return self.get(item_id) is not None
    
    def save_many(self, items: List[T]) -> List[str]:
        """Save multiple items. Override for batch optimization."""
        return [self.save(item) for item in items]
    
    def delete_many(self, item_ids: List[str]) -> int:
        """Delete multiple items. Override for batch optimization."""
        return sum(1 for id in item_ids if self.delete(id))


class InvestigationStorage(StorageProvider):
    """Storage interface specifically for Investigation entities."""
    
    @abstractmethod
    def get_by_query(self, query: str) -> List[Any]:
        """Find investigations by original query."""
        pass
    
    @abstractmethod
    def get_recent(self, limit: int = 10) -> List[Any]:
        """Get most recent investigations."""
        pass
    
    @abstractmethod
    def get_by_status(self, status: str) -> List[Any]:
        """Get investigations by status."""
        pass
    
    @abstractmethod
    def get_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[Any]:
        """Get investigations within a date range."""
        pass


class EntityStorage(StorageProvider):
    """Storage interface for extracted entities."""
    
    @abstractmethod
    def get_by_type(self, entity_type: str, limit: int = 100) -> List[Any]:
        """Get entities by type."""
        pass
    
    @abstractmethod
    def get_by_value(self, value: str) -> Optional[Any]:
        """Find entity by exact value."""
        pass
    
    @abstractmethod
    def search(self, pattern: str, entity_type: Optional[str] = None) -> List[Any]:
        """Search entities by pattern."""
        pass
    
    @abstractmethod
    def get_statistics(self) -> Dict[str, int]:
        """Get count of entities by type."""
        pass


class AlertStorage(StorageProvider):
    """Storage interface for alerts and alert rules."""
    
    @abstractmethod
    def get_pending_alerts(self) -> List[Any]:
        """Get all pending alerts."""
        pass
    
    @abstractmethod
    def get_active_rules(self) -> List[Any]:
        """Get all active alert rules."""
        pass
    
    @abstractmethod
    def get_alerts_by_rule(self, rule_id: str) -> List[Any]:
        """Get alerts triggered by a specific rule."""
        pass
