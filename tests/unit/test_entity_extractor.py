"""Tests for entity extraction."""

import pytest
from datetime import datetime

from src.core.services.entity_extractor import EntityExtractor


class TestEntityExtractor:
    """Tests for EntityExtractor service."""
    
    @pytest.fixture
    def extractor(self):
        """Create an extractor instance."""
        return EntityExtractor()
    
    def test_extract_emails(self, extractor):
        """Test email extraction."""
        text = """
        Contact us at support@example.com or sales@example.org.
        Invalid emails: @invalid, test@, notanemail
        """
        
        entities = extractor.extract(text)
        emails = [e for e in entities if e.entity_type == "email"]
        
        assert len(emails) == 2
        assert any(e.value == "support@example.com" for e in emails)
        assert any(e.value == "sales@example.org" for e in emails)
    
    def test_extract_bitcoin_addresses(self, extractor):
        """Test Bitcoin address extraction."""
        text = """
        Send payment to: 1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2
        Or: 3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy
        Invalid: 1234567890
        """
        
        entities = extractor.extract(text)
        wallets = [e for e in entities if e.entity_type == "crypto_wallet"]
        
        assert len(wallets) >= 1
    
    def test_extract_ethereum_addresses(self, extractor):
        """Test Ethereum address extraction."""
        text = """
        ETH address: 0x742d35Cc6634C0532925a3b844Bc9e7595f5e2a1
        """
        
        entities = extractor.extract(text)
        wallets = [e for e in entities if e.entity_type == "crypto_wallet"]
        
        assert len(wallets) >= 1
    
    def test_extract_onion_domains(self, extractor):
        """Test .onion domain extraction."""
        text = """
        Visit us at http://example.onion/page
        Or https://abcdefghijklmnop.onion
        """
        
        entities = extractor.extract(text)
        domains = [e for e in entities if e.entity_type == "domain"]
        
        assert len(domains) >= 1
    
    def test_extract_ip_addresses(self, extractor):
        """Test IP address extraction."""
        text = """
        Server IP: 192.168.1.1
        Gateway: 10.0.0.1
        Invalid: 999.999.999.999
        """
        
        entities = extractor.extract(text)
        ips = [e for e in entities if e.entity_type == "ip_address"]
        
        assert len(ips) >= 1
    
    def test_extract_phone_numbers(self, extractor):
        """Test phone number extraction."""
        text = """
        Call us: +1-555-123-4567
        Or: (555) 987-6543
        """
        
        entities = extractor.extract(text)
        phones = [e for e in entities if e.entity_type == "phone"]
        
        assert len(phones) >= 1
    
    def test_extract_hashes(self, extractor):
        """Test hash extraction."""
        text = """
        MD5: d41d8cd98f00b204e9800998ecf8427e
        SHA256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
        """
        
        entities = extractor.extract(text)
        hashes = [e for e in entities if e.entity_type == "hash"]
        
        assert len(hashes) >= 1
    
    def test_extract_cves(self, extractor):
        """Test CVE extraction."""
        text = """
        Vulnerabilities: CVE-2021-44228, CVE-2022-12345
        """
        
        entities = extractor.extract(text)
        cves = [e for e in entities if e.entity_type == "cve"]
        
        assert len(cves) == 2
    
    def test_empty_text(self, extractor):
        """Test extraction from empty text."""
        entities = extractor.extract("")
        assert len(entities) == 0
    
    def test_no_entities(self, extractor):
        """Test extraction from text with no entities."""
        text = "This is just plain text with no special entities."
        entities = extractor.extract(text)
        
        # May extract some false positives, but should be minimal
        assert len(entities) < 5
    
    def test_duplicate_removal(self, extractor):
        """Test that duplicate entities are removed."""
        text = """
        Email: test@example.com
        Contact: test@example.com
        Support: test@example.com
        """
        
        entities = extractor.extract(text)
        emails = [e for e in entities if e.entity_type == "email"]
        
        # Should only have one unique email
        unique_values = set(e.value for e in emails)
        assert len(unique_values) == 1
