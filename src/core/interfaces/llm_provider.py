"""Abstract interface for LLM providers."""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, Callable, AsyncIterator
from dataclasses import dataclass


@dataclass
class LLMResponse:
    """Response from an LLM provider."""
    content: str
    model: str
    tokens_used: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    finish_reason: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class LLMConfig:
    """Configuration for LLM providers."""
    model_name: str
    temperature: float = 0.0
    max_tokens: Optional[int] = None
    top_p: float = 1.0
    streaming: bool = True
    timeout: int = 60
    retry_attempts: int = 3
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.
    
    Implementations should handle specific LLM APIs (OpenAI, Anthropic, etc.)
    """
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self._client = None
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the name of this provider (e.g., 'openai', 'anthropic')."""
        pass
    
    @property
    @abstractmethod
    def supported_models(self) -> List[str]:
        """Return list of supported model names."""
        pass
    
    @abstractmethod
    def initialize(self) -> None:
        """Initialize the LLM client/connection."""
        pass
    
    @abstractmethod
    def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate a completion for the given prompt.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            **kwargs: Additional provider-specific parameters
            
        Returns:
            LLMResponse with the completion
        """
        pass
    
    @abstractmethod
    def stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        callback: Optional[Callable[[str], None]] = None,
        **kwargs
    ) -> str:
        """
        Stream a completion, calling callback for each chunk.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            callback: Function to call with each streamed chunk
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Complete response text
        """
        pass
    
    @abstractmethod
    async def acomplete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """Async version of complete."""
        pass
    
    @abstractmethod
    async def astream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """Async streaming generator."""
        pass
    
    def validate_model(self, model_name: str) -> bool:
        """Check if a model is supported by this provider."""
        return model_name.lower() in [m.lower() for m in self.supported_models]
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate the number of tokens in text.
        Default implementation uses rough word-based estimate.
        Override for more accurate provider-specific counting.
        """
        # Rough estimate: ~4 chars per token for English
        return len(text) // 4
    
    def health_check(self) -> bool:
        """
        Check if the provider is healthy and accessible.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            # Simple test completion
            response = self.complete("Hello", max_tokens=5)
            return bool(response.content)
        except Exception:
            return False
    
    def get_langchain_llm(self):
        """
        Return a LangChain-compatible LLM instance.
        Override in implementations that support LangChain.
        """
        raise NotImplementedError("LangChain integration not implemented for this provider")
