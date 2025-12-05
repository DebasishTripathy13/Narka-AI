"""Pytest configuration and fixtures."""

import pytest
import tempfile
import os


@pytest.fixture
def temp_dir():
    """Create a temporary directory."""
    path = tempfile.mkdtemp()
    yield path
    # Cleanup
    import shutil
    shutil.rmtree(path, ignore_errors=True)


@pytest.fixture
def temp_db():
    """Create a temporary database file."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    os.unlink(path)


@pytest.fixture
def sample_text():
    """Sample text with various entities."""
    return """
    Contact: admin@darkweb.onion
    Bitcoin: 1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2
    Ethereum: 0x742d35Cc6634C0532925a3b844Bc9e7595f5e2a1
    
    Server: 192.168.1.100
    Domain: http://abcdefghijklmnop.onion/market
    
    Call: +1-555-123-4567
    
    Vulnerability: CVE-2021-44228
    Hash: d41d8cd98f00b204e9800998ecf8427e
    """


@pytest.fixture
def mock_search_results():
    """Mock search results."""
    return [
        {
            "id": "result1",
            "url": "http://example1.onion/page",
            "title": "Example Result 1",
            "description": "This is the first example result",
            "source_engine": "ahmia",
        },
        {
            "id": "result2",
            "url": "http://example2.onion/page",
            "title": "Example Result 2",
            "description": "This is the second example result",
            "source_engine": "torch",
        },
    ]
