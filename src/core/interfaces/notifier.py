"""Abstract interface for notification providers."""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum


class NotificationChannel(Enum):
    """Supported notification channels."""
    EMAIL = "email"
    WEBHOOK = "webhook"
    SLACK = "slack"
    DISCORD = "discord"
    TELEGRAM = "telegram"
    SMS = "sms"
    PUSH = "push"


class NotificationPriority(Enum):
    """Notification priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class NotificationMessage:
    """A notification message to be sent."""
    title: str
    body: str
    priority: NotificationPriority = NotificationPriority.NORMAL
    channel: NotificationChannel = NotificationChannel.WEBHOOK
    recipient: Optional[str] = None  # Email, webhook URL, channel ID, etc.
    metadata: Dict[str, Any] = None
    
    # Rich content
    html_body: Optional[str] = None
    attachments: List[Dict[str, Any]] = None
    
    # Tracking
    investigation_id: Optional[str] = None
    alert_id: Optional[str] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.attachments is None:
            self.attachments = []


@dataclass
class NotificationResult:
    """Result of a notification send attempt."""
    success: bool
    channel: NotificationChannel
    recipient: Optional[str] = None
    message_id: Optional[str] = None
    error_message: Optional[str] = None
    response_data: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.response_data is None:
            self.response_data = {}


class NotificationProvider(ABC):
    """
    Abstract base class for notification providers.
    
    Each implementation handles a specific notification channel.
    """
    
    @property
    @abstractmethod
    def channel(self) -> NotificationChannel:
        """Return the notification channel this provider handles."""
        pass
    
    @abstractmethod
    def initialize(self) -> None:
        """Initialize the notification provider."""
        pass
    
    @abstractmethod
    def send(self, message: NotificationMessage) -> NotificationResult:
        """
        Send a notification message.
        
        Args:
            message: The notification to send
            
        Returns:
            NotificationResult indicating success/failure
        """
        pass
    
    @abstractmethod
    async def asend(self, message: NotificationMessage) -> NotificationResult:
        """Async version of send."""
        pass
    
    @abstractmethod
    def validate_recipient(self, recipient: str) -> bool:
        """
        Validate that a recipient is valid for this channel.
        
        Args:
            recipient: The recipient identifier
            
        Returns:
            True if valid, False otherwise
        """
        pass
    
    def send_batch(self, messages: List[NotificationMessage]) -> List[NotificationResult]:
        """
        Send multiple notifications.
        Override for batch optimization.
        
        Args:
            messages: List of messages to send
            
        Returns:
            List of results for each message
        """
        return [self.send(msg) for msg in messages]
    
    async def asend_batch(self, messages: List[NotificationMessage]) -> List[NotificationResult]:
        """Async version of send_batch."""
        import asyncio
        return await asyncio.gather(*[self.asend(msg) for msg in messages])
    
    def health_check(self) -> bool:
        """
        Check if the notification provider is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        return True


class NotificationManager:
    """
    Manages multiple notification providers.
    
    Routes messages to the appropriate provider based on channel.
    """
    
    def __init__(self):
        self._providers: Dict[NotificationChannel, NotificationProvider] = {}
    
    def register_provider(self, provider: NotificationProvider) -> None:
        """Register a notification provider."""
        self._providers[provider.channel] = provider
    
    def unregister_provider(self, channel: NotificationChannel) -> None:
        """Unregister a notification provider."""
        self._providers.pop(channel, None)
    
    def get_provider(self, channel: NotificationChannel) -> Optional[NotificationProvider]:
        """Get a registered provider by channel."""
        return self._providers.get(channel)
    
    def send(self, message: NotificationMessage) -> NotificationResult:
        """Send a notification using the appropriate provider."""
        provider = self._providers.get(message.channel)
        if not provider:
            return NotificationResult(
                success=False,
                channel=message.channel,
                error_message=f"No provider registered for channel: {message.channel.value}"
            )
        return provider.send(message)
    
    async def asend(self, message: NotificationMessage) -> NotificationResult:
        """Async send."""
        provider = self._providers.get(message.channel)
        if not provider:
            return NotificationResult(
                success=False,
                channel=message.channel,
                error_message=f"No provider registered for channel: {message.channel.value}"
            )
        return await provider.asend(message)
    
    def broadcast(
        self,
        message: NotificationMessage,
        channels: Optional[List[NotificationChannel]] = None
    ) -> List[NotificationResult]:
        """
        Send a message to multiple channels.
        
        Args:
            message: The message to send
            channels: Specific channels to send to (None = all registered)
            
        Returns:
            List of results for each channel
        """
        target_channels = channels or list(self._providers.keys())
        results = []
        
        for channel in target_channels:
            msg_copy = NotificationMessage(
                title=message.title,
                body=message.body,
                priority=message.priority,
                channel=channel,
                recipient=message.recipient,
                metadata=message.metadata.copy() if message.metadata else {},
                html_body=message.html_body,
                attachments=message.attachments.copy() if message.attachments else [],
                investigation_id=message.investigation_id,
                alert_id=message.alert_id,
            )
            results.append(self.send(msg_copy))
        
        return results
    
    @property
    def available_channels(self) -> List[NotificationChannel]:
        """Get list of available notification channels."""
        return list(self._providers.keys())
