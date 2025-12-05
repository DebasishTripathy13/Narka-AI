"""Tests for investigation entity."""

import pytest
from datetime import datetime

from src.core.entities.investigation import Investigation, InvestigationStatus


class TestInvestigation:
    """Tests for Investigation entity."""
    
    def test_create_investigation(self):
        """Test creating an investigation."""
        inv = Investigation(query="test query")
        
        assert inv.query == "test query"
        assert inv.status == InvestigationStatus.PENDING
        assert inv.id is not None
        assert inv.created_at is not None
    
    def test_investigation_status_transitions(self):
        """Test investigation status transitions."""
        inv = Investigation(query="test")
        
        assert inv.status == InvestigationStatus.PENDING
        
        inv.status = InvestigationStatus.SEARCHING
        assert inv.status == InvestigationStatus.SEARCHING
        
        inv.status = InvestigationStatus.COMPLETED
        assert inv.status == InvestigationStatus.COMPLETED
    
    def test_investigation_with_results(self):
        """Test investigation with search results."""
        inv = Investigation(query="test")
        
        # Add mock results
        inv.search_results = [{"url": "http://example.onion"}]
        
        assert len(inv.search_results) == 1
    
    def test_investigation_metadata(self):
        """Test investigation metadata."""
        inv = Investigation(
            query="test",
            metadata={"source": "api", "priority": "high"}
        )
        
        assert inv.metadata["source"] == "api"
        assert inv.metadata["priority"] == "high"
    
    def test_investigation_tags(self):
        """Test investigation tags."""
        inv = Investigation(
            query="test",
            tags=["ransomware", "threat-actor"]
        )
        
        assert "ransomware" in inv.tags
        assert "threat-actor" in inv.tags
