"""Anthropic LLM provider."""

from typing import Optional, List, Callable, AsyncIterator
import os

from .base import BaseLLMProvider
from ...core.interfaces.llm_provider import LLMConfig, LLMResponse


class AnthropicProvider(BaseLLMProvider):
    """
    Anthropic LLM provider implementation.
    
    Supports Claude 3 and Claude 4 models.
    """
    
    SUPPORTED_MODELS = [
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229",
        "claude-3-haiku-20240307",
        "claude-3-5-sonnet-latest",
        "claude-sonnet-4-5",
        "claude-sonnet-4-0",
    ]
    
    @property
    def provider_name(self) -> str:
        return "anthropic"
    
    @property
    def supported_models(self) -> List[str]:
        return self.SUPPORTED_MODELS
    
    def initialize(self) -> None:
        """Initialize the Anthropic client."""
        try:
            from anthropic import Anthropic
            
            api_key = self.config.api_key or os.getenv("ANTHROPIC_API_KEY")
            
            self._client = Anthropic(
                api_key=api_key,
                timeout=self.config.timeout,
            )
        except ImportError:
            raise ImportError("anthropic package not installed. Run: pip install anthropic")
    
    def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate a completion."""
        if self._client is None:
            self.initialize()
        
        message_kwargs = {
            "model": self.config.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens or 4096),
            "temperature": kwargs.get("temperature", self.config.temperature),
        }
        
        if system_prompt:
            message_kwargs["system"] = system_prompt
        
        response = self._client.messages.create(**message_kwargs)
        
        content = ""
        if response.content:
            content = response.content[0].text if response.content else ""
        
        return LLMResponse(
            content=content,
            model=response.model,
            tokens_used=response.usage.input_tokens + response.usage.output_tokens,
            prompt_tokens=response.usage.input_tokens,
            completion_tokens=response.usage.output_tokens,
            finish_reason=response.stop_reason,
        )
    
    def stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        callback: Optional[Callable[[str], None]] = None,
        **kwargs
    ) -> str:
        """Stream a completion."""
        if self._client is None:
            self.initialize()
        
        message_kwargs = {
            "model": self.config.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens or 4096),
            "temperature": kwargs.get("temperature", self.config.temperature),
        }
        
        if system_prompt:
            message_kwargs["system"] = system_prompt
        
        full_content = ""
        
        with self._client.messages.stream(**message_kwargs) as stream:
            for text in stream.text_stream:
                full_content += text
                if callback:
                    callback(text)
        
        return full_content
    
    async def acomplete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """Async completion."""
        from anthropic import AsyncAnthropic
        
        api_key = self.config.api_key or os.getenv("ANTHROPIC_API_KEY")
        client = AsyncAnthropic(api_key=api_key)
        
        message_kwargs = {
            "model": self.config.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens or 4096),
            "temperature": kwargs.get("temperature", self.config.temperature),
        }
        
        if system_prompt:
            message_kwargs["system"] = system_prompt
        
        response = await client.messages.create(**message_kwargs)
        
        content = response.content[0].text if response.content else ""
        
        return LLMResponse(
            content=content,
            model=response.model,
            tokens_used=response.usage.input_tokens + response.usage.output_tokens,
            prompt_tokens=response.usage.input_tokens,
            completion_tokens=response.usage.output_tokens,
            finish_reason=response.stop_reason,
        )
    
    async def astream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """Async streaming."""
        from anthropic import AsyncAnthropic
        
        api_key = self.config.api_key or os.getenv("ANTHROPIC_API_KEY")
        client = AsyncAnthropic(api_key=api_key)
        
        message_kwargs = {
            "model": self.config.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens or 4096),
            "temperature": kwargs.get("temperature", self.config.temperature),
        }
        
        if system_prompt:
            message_kwargs["system"] = system_prompt
        
        async with client.messages.stream(**message_kwargs) as stream:
            async for text in stream.text_stream:
                yield text
    
    def _create_langchain_llm(self):
        """Create LangChain Anthropic instance."""
        from langchain_anthropic import ChatAnthropic
        
        return ChatAnthropic(
            model=self.config.model_name,
            temperature=self.config.temperature,
            streaming=self.config.streaming,
        )
