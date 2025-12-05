"""Tor connection management."""

import socket
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime


class TorStatus(Enum):
    """Tor connection status."""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    CHECKING = "checking"


@dataclass
class TorConfig:
    """Configuration for Tor connection."""
    socks_host: str = "127.0.0.1"
    socks_port: int = 9050
    control_port: int = 9051
    control_password: Optional[str] = None
    connection_timeout: int = 30
    retry_attempts: int = 3
    retry_delay: float = 1.0


@dataclass
class TorConnectionInfo:
    """Information about the current Tor connection."""
    status: TorStatus
    exit_ip: Optional[str] = None
    exit_country: Optional[str] = None
    circuit_id: Optional[str] = None
    last_check: Optional[datetime] = None
    latency_ms: Optional[float] = None
    error_message: Optional[str] = None


class TorManager:
    """
    Manages Tor SOCKS proxy connections.
    
    Provides:
    - Connection health checking
    - Circuit rotation
    - Proxy configuration
    """
    
    # Tor check service URL
    CHECK_URL = "https://check.torproject.org/api/ip"
    
    def __init__(self, config: Optional[TorConfig] = None):
        """
        Initialize Tor manager.
        
        Args:
            config: Tor configuration
        """
        self.config = config or TorConfig()
        self._connection_info = TorConnectionInfo(status=TorStatus.DISCONNECTED)
        self._circuit_manager = None
    
    @property
    def proxy_url(self) -> str:
        """Get the SOCKS5 proxy URL."""
        return f"socks5h://{self.config.socks_host}:{self.config.socks_port}"
    
    @property
    def proxies(self) -> Dict[str, str]:
        """Get proxy dict for requests library."""
        return {
            "http": self.proxy_url,
            "https": self.proxy_url,
        }
    
    @property
    def status(self) -> TorStatus:
        """Get current connection status."""
        return self._connection_info.status
    
    @property
    def connection_info(self) -> TorConnectionInfo:
        """Get full connection information."""
        return self._connection_info
    
    def check_connection(self) -> TorConnectionInfo:
        """
        Check if Tor is running and accessible.
        
        Returns:
            TorConnectionInfo with current status
        """
        import time
        import requests
        
        self._connection_info.status = TorStatus.CHECKING
        self._connection_info.last_check = datetime.utcnow()
        
        # First check if SOCKS port is open
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((self.config.socks_host, self.config.socks_port))
            sock.close()
            
            if result != 0:
                self._connection_info.status = TorStatus.DISCONNECTED
                self._connection_info.error_message = f"SOCKS port {self.config.socks_port} is not open"
                return self._connection_info
                
        except Exception as e:
            self._connection_info.status = TorStatus.ERROR
            self._connection_info.error_message = str(e)
            return self._connection_info
        
        # Check actual Tor connectivity
        try:
            start_time = time.time()
            response = requests.get(
                self.CHECK_URL,
                proxies=self.proxies,
                timeout=self.config.connection_timeout
            )
            latency = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                self._connection_info.status = TorStatus.CONNECTED
                self._connection_info.exit_ip = data.get("IP")
                self._connection_info.latency_ms = latency
                self._connection_info.error_message = None
                
                # Check if actually using Tor
                if not data.get("IsTor", False):
                    self._connection_info.status = TorStatus.ERROR
                    self._connection_info.error_message = "Traffic not going through Tor"
            else:
                self._connection_info.status = TorStatus.ERROR
                self._connection_info.error_message = f"Check returned HTTP {response.status_code}"
                
        except requests.Timeout:
            self._connection_info.status = TorStatus.ERROR
            self._connection_info.error_message = "Connection timeout"
        except Exception as e:
            self._connection_info.status = TorStatus.ERROR
            self._connection_info.error_message = str(e)
        
        return self._connection_info
    
    def is_connected(self) -> bool:
        """Check if Tor is connected (quick check)."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((self.config.socks_host, self.config.socks_port))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    def wait_for_connection(self, timeout: int = 60) -> bool:
        """
        Wait for Tor to become available.
        
        Args:
            timeout: Maximum seconds to wait
            
        Returns:
            True if connected, False if timeout
        """
        import time
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.is_connected():
                info = self.check_connection()
                if info.status == TorStatus.CONNECTED:
                    return True
            time.sleep(self.config.retry_delay)
        
        return False
    
    def get_new_identity(self) -> bool:
        """
        Request a new Tor identity (new circuit).
        
        Requires control port access with authentication.
        
        Returns:
            True if successful
        """
        if not self._circuit_manager:
            from .circuit import CircuitManager
            self._circuit_manager = CircuitManager(self.config)
        
        return self._circuit_manager.new_identity()
    
    def get_session(self) -> "requests.Session":
        """
        Get a requests Session configured for Tor.
        
        Returns:
            Configured requests.Session
        """
        import requests
        
        session = requests.Session()
        session.proxies.update(self.proxies)
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; rv:109.0) Gecko/20100101 Firefox/115.0"
        })
        
        return session
    
    async def acheck_connection(self) -> TorConnectionInfo:
        """Async version of check_connection."""
        import aiohttp
        import time
        
        self._connection_info.status = TorStatus.CHECKING
        self._connection_info.last_check = datetime.utcnow()
        
        try:
            from aiohttp_socks import ProxyConnector
            connector = ProxyConnector.from_url(self.proxy_url)
            
            start_time = time.time()
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(
                    self.CHECK_URL,
                    timeout=aiohttp.ClientTimeout(total=self.config.connection_timeout)
                ) as response:
                    latency = (time.time() - start_time) * 1000
                    
                    if response.status == 200:
                        data = await response.json()
                        self._connection_info.status = TorStatus.CONNECTED
                        self._connection_info.exit_ip = data.get("IP")
                        self._connection_info.latency_ms = latency
                        self._connection_info.error_message = None
                        
                        if not data.get("IsTor", False):
                            self._connection_info.status = TorStatus.ERROR
                            self._connection_info.error_message = "Traffic not going through Tor"
                    else:
                        self._connection_info.status = TorStatus.ERROR
                        self._connection_info.error_message = f"HTTP {response.status}"
                        
        except Exception as e:
            self._connection_info.status = TorStatus.ERROR
            self._connection_info.error_message = str(e)
        
        return self._connection_info
