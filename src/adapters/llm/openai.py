"""OpenAI LLM provider."""

from typing import Optional, List, Callable, AsyncIterator
import os

from .base import BaseLLMProvider
from ...core.interfaces.llm_provider import LLMConfig, LLMResponse


class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI LLM provider implementation.
    
    Supports GPT-4, GPT-4 Turbo, GPT-3.5, GPT-5 series and newer models.
    
    New API (2025):
        import OpenAI from "openai"
        client = OpenAI()
        response = client.responses.create(
            model="gpt-5.1",
            input="..."
        )
        print(response.output_text)
    
    Note: Both responses.create() (new) and chat.completions.create() (legacy) are supported.
    """
    
    SUPPORTED_MODELS = [
        # GPT-5 series (2025) - New flagship models
        "gpt-5.1",        # Best for coding and agentic tasks with configurable reasoning
        "gpt-5-mini",     # Faster, cost-efficient for well-defined tasks
        "gpt-5-nano",     # Fastest, most cost-efficient GPT-5
        # GPT-4 series
        "gpt-4.1",
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4-turbo",
        "gpt-4",
        # Legacy
        "gpt-3.5-turbo",
        # Specialized models
        "gpt-image-1",    # Image generation
        "o1",             # Reasoning model
        "o1-mini",        # Mini reasoning model
    ]
    
    @property
    def provider_name(self) -> str:
        return "openai"
    
    @property
    def supported_models(self) -> List[str]:
        return self.SUPPORTED_MODELS
    
    def initialize(self) -> None:
        """Initialize the OpenAI client."""
        try:
            from openai import OpenAI
            
            api_key = self.config.api_key or os.getenv("OPENAI_API_KEY")
            
            self._client = OpenAI(
                api_key=api_key,
                timeout=self.config.timeout,
            )
        except ImportError:
            raise ImportError("openai package not installed. Run: pip install openai")
    
    def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate a completion.
        
        Supports both new responses.create() API (GPT-5+) and 
        legacy chat.completions.create() API.
        """
        if self._client is None:
            self.initialize()
        
        use_new_api = kwargs.get("use_responses_api", False) or self.config.model_name.startswith("gpt-5")
        
        if use_new_api:
            # New responses.create() API for GPT-5 models
            return self._complete_with_responses_api(prompt, system_prompt, **kwargs)
        else:
            # Legacy chat.completions.create() API
            return self._complete_with_chat_api(prompt, system_prompt, **kwargs)
    
    def _complete_with_responses_api(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """Use new responses.create() API (2025)."""
        full_input = prompt
        if system_prompt:
            full_input = f"{system_prompt}\n\n{prompt}"
        
        response = self._client.responses.create(
            model=self.config.model_name,
            input=full_input,
            temperature=kwargs.get("temperature", self.config.temperature),
            max_output_tokens=kwargs.get("max_tokens", self.config.max_tokens),
        )
        
        return LLMResponse(
            content=response.output_text or "",
            model=self.config.model_name,
            tokens_used=getattr(response, 'usage', {}).get('total_tokens', 0) if hasattr(response, 'usage') else 0,
            finish_reason="stop",
        )
    
    def _complete_with_chat_api(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """Use legacy chat.completions.create() API."""
        messages = self._build_messages(prompt, system_prompt)
        
        response = self._client.chat.completions.create(
            model=self.config.model_name,
            messages=messages,
            temperature=kwargs.get("temperature", self.config.temperature),
            max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
            top_p=kwargs.get("top_p", self.config.top_p),
        )
        
        choice = response.choices[0]
        
        return LLMResponse(
            content=choice.message.content or "",
            model=response.model,
            tokens_used=response.usage.total_tokens if response.usage else 0,
            prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
            completion_tokens=response.usage.completion_tokens if response.usage else 0,
            finish_reason=choice.finish_reason,
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
        
        messages = self._build_messages(prompt, system_prompt)
        
        response = self._client.chat.completions.create(
            model=self.config.model_name,
            messages=messages,
            temperature=kwargs.get("temperature", self.config.temperature),
            max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
            stream=True,
        )
        
        full_content = ""
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                full_content += content
                if callback:
                    callback(content)
        
        return full_content
    
    async def acomplete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """Async completion."""
        from openai import AsyncOpenAI
        
        api_key = self.config.api_key or os.getenv("OPENAI_API_KEY")
        client = AsyncOpenAI(api_key=api_key)
        
        messages = self._build_messages(prompt, system_prompt)
        
        response = await client.chat.completions.create(
            model=self.config.model_name,
            messages=messages,
            temperature=kwargs.get("temperature", self.config.temperature),
            max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
        )
        
        choice = response.choices[0]
        
        return LLMResponse(
            content=choice.message.content or "",
            model=response.model,
            tokens_used=response.usage.total_tokens if response.usage else 0,
            prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
            completion_tokens=response.usage.completion_tokens if response.usage else 0,
            finish_reason=choice.finish_reason,
        )
    
    async def astream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """Async streaming."""
        from openai import AsyncOpenAI
        
        api_key = self.config.api_key or os.getenv("OPENAI_API_KEY")
        client = AsyncOpenAI(api_key=api_key)
        
        messages = self._build_messages(prompt, system_prompt)
        
        response = await client.chat.completions.create(
            model=self.config.model_name,
            messages=messages,
            temperature=kwargs.get("temperature", self.config.temperature),
            max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
            stream=True,
        )
        
        async for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    def _create_langchain_llm(self):
        """Create LangChain OpenAI instance."""
        from langchain_openai import ChatOpenAI
        
        return ChatOpenAI(
            model_name=self.config.model_name,
            temperature=self.config.temperature,
            streaming=self.config.streaming,
        )
