"""Base LLM provider with common functionality."""

from abc import abstractmethod
from typing import Optional, List, Callable, AsyncIterator

from ...core.interfaces.llm_provider import LLMProvider, LLMConfig, LLMResponse


class BaseLLMProvider(LLMProvider):
    """
    Base implementation for LLM providers with common functionality.
    """
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self._langchain_llm = None
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation)."""
        # Average ~4 characters per token for English
        return len(text) // 4
    
    def health_check(self) -> bool:
        """Check if provider is accessible."""
        try:
            response = self.complete("Hi", max_tokens=5)
            return bool(response.content)
        except Exception:
            return False
    
    def get_langchain_llm(self):
        """Return a LangChain-compatible LLM instance."""
        if self._langchain_llm is None:
            self._langchain_llm = self._create_langchain_llm()
        return self._langchain_llm
    
    @abstractmethod
    def _create_langchain_llm(self):
        """Create a LangChain LLM instance. Override in subclasses."""
        pass
    
    def _build_messages(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> List[dict]:
        """Build message list for chat completion."""
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        return messages
