"""Tor circuit management for identity rotation."""

import socket
from typing import Optional
from datetime import datetime
from dataclasses import dataclass

from .manager import TorConfig


@dataclass
class CircuitInfo:
    """Information about a Tor circuit."""
    circuit_id: str
    created_at: datetime
    exit_fingerprint: Optional[str] = None
    path: Optional[str] = None


class CircuitManager:
    """
    Manages Tor circuit rotation via the control port.
    
    Requires Tor control port to be enabled and accessible.
    """
    
    def __init__(self, config: TorConfig):
        """
        Initialize circuit manager.
        
        Args:
            config: Tor configuration with control port settings
        """
        self.config = config
        self._last_rotation: Optional[datetime] = None
        self._rotation_count = 0
    
    def new_identity(self) -> bool:
        """
        Request a new Tor identity (new exit node).
        
        Returns:
            True if successful
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((self.config.socks_host, self.config.control_port))
                sock.settimeout(10)
                
                # Authenticate
                if self.config.control_password:
                    auth_cmd = f'AUTHENTICATE "{self.config.control_password}"\r\n'
                else:
                    auth_cmd = 'AUTHENTICATE\r\n'
                
                sock.send(auth_cmd.encode())
                response = sock.recv(1024).decode()
                
                if "250 OK" not in response:
                    return False
                
                # Request new identity
                sock.send(b'SIGNAL NEWNYM\r\n')
                response = sock.recv(1024).decode()
                
                if "250 OK" in response:
                    self._last_rotation = datetime.utcnow()
                    self._rotation_count += 1
                    return True
                
                return False
                
        except Exception:
            return False
    
    def get_circuit_info(self) -> Optional[CircuitInfo]:
        """
        Get information about the current circuit.
        
        Returns:
            CircuitInfo if available
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((self.config.socks_host, self.config.control_port))
                sock.settimeout(10)
                
                # Authenticate
                if self.config.control_password:
                    auth_cmd = f'AUTHENTICATE "{self.config.control_password}"\r\n'
                else:
                    auth_cmd = 'AUTHENTICATE\r\n'
                
                sock.send(auth_cmd.encode())
                response = sock.recv(1024).decode()
                
                if "250 OK" not in response:
                    return None
                
                # Get circuit status
                sock.send(b'GETINFO circuit-status\r\n')
                response = sock.recv(4096).decode()
                
                # Parse response (simplified)
                if "250+" in response:
                    lines = response.split('\n')
                    for line in lines:
                        if line.startswith('250-circuit-status='):
                            parts = line.split()
                            if len(parts) >= 2:
                                return CircuitInfo(
                                    circuit_id=parts[0].split('=')[1] if '=' in parts[0] else parts[0],
                                    created_at=datetime.utcnow(),
                                    path=parts[1] if len(parts) > 1 else None
                                )
                
                return None
                
        except Exception:
            return None
    
    @property
    def last_rotation(self) -> Optional[datetime]:
        """Get timestamp of last circuit rotation."""
        return self._last_rotation
    
    @property
    def rotation_count(self) -> int:
        """Get total number of rotations performed."""
        return self._rotation_count
    
    def should_rotate(self, interval_seconds: int = 600) -> bool:
        """
        Check if circuit should be rotated based on interval.
        
        Args:
            interval_seconds: Minimum seconds between rotations
            
        Returns:
            True if rotation is recommended
        """
        if not self._last_rotation:
            return True
        
        elapsed = (datetime.utcnow() - self._last_rotation).total_seconds()
        return elapsed >= interval_seconds


class RotatingTorSession:
    """
    A requests Session that automatically rotates Tor circuits.
    """
    
    def __init__(
        self,
        config: TorConfig,
        rotate_after_requests: int = 10,
        rotate_after_seconds: int = 600
    ):
        """
        Initialize rotating session.
        
        Args:
            config: Tor configuration
            rotate_after_requests: Rotate after this many requests
            rotate_after_seconds: Rotate after this many seconds
        """
        self.config = config
        self.rotate_after_requests = rotate_after_requests
        self.rotate_after_seconds = rotate_after_seconds
        
        self._circuit_manager = CircuitManager(config)
        self._request_count = 0
        self._session_start = datetime.utcnow()
    
    def _maybe_rotate(self) -> None:
        """Rotate circuit if needed."""
        should_rotate = False
        
        # Check request count
        if self._request_count >= self.rotate_after_requests:
            should_rotate = True
        
        # Check time elapsed
        elapsed = (datetime.utcnow() - self._session_start).total_seconds()
        if elapsed >= self.rotate_after_seconds:
            should_rotate = True
        
        if should_rotate:
            if self._circuit_manager.new_identity():
                self._request_count = 0
                self._session_start = datetime.utcnow()
    
    def get(self, url: str, **kwargs) -> "requests.Response":
        """Make a GET request with automatic rotation."""
        import requests
        
        self._maybe_rotate()
        self._request_count += 1
        
        proxies = {
            "http": f"socks5h://{self.config.socks_host}:{self.config.socks_port}",
            "https": f"socks5h://{self.config.socks_host}:{self.config.socks_port}",
        }
        
        return requests.get(url, proxies=proxies, **kwargs)
    
    def post(self, url: str, **kwargs) -> "requests.Response":
        """Make a POST request with automatic rotation."""
        import requests
        
        self._maybe_rotate()
        self._request_count += 1
        
        proxies = {
            "http": f"socks5h://{self.config.socks_host}:{self.config.socks_port}",
            "https": f"socks5h://{self.config.socks_host}:{self.config.socks_port}",
        }
        
        return requests.post(url, proxies=proxies, **kwargs)
