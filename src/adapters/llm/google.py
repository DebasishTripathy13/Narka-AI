"""Google LLM provider (Gemini)."""

from typing import Optional, List, Callable, AsyncIterator
import os

from google import genai
from google.genai import types

from .base import BaseLLMProvider
from ...core.interfaces.llm_provider import LLMConfig, LLMResponse


class GoogleProvider(BaseLLMProvider):
    """
    Google LLM provider implementation.
    
    Supports Gemini models using the new google.genai Client API with Google Search.
    
    New API (2025):
        from google import genai
        from google.genai import types
        
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-flash-latest",
            contents=[types.Content(...)],
            config=types.GenerateContentConfig(
                tools=[types.Tool(googleSearch=types.GoogleSearch())]
            )
        )
    """
    
    SUPPORTED_MODELS = [
        # Latest models (2025)
        "gemini-flash-latest",    # Latest Flash model with Google Search
        "gemini-pro-latest",      # Latest Pro model
        "gemini-3-pro",           # Most intelligent, best multimodal understanding
        "gemini-2.5-pro",         # Powerful reasoning, excels at coding
        "gemini-2.5-flash",       # Balanced, 1M token context
        "gemini-2.5-flash-lite",  # Fastest, most cost-efficient
        # Media models
        "veo-3.1",                # Video generation with native audio
        "nano-banana",            # Image generation
        "nano-banana-pro",        # Advanced image generation/editing
        # Legacy models
        "gemini-2.0-flash",
        "gemini-1.5-pro",
        "gemini-1.5-flash",
        "gemini-pro",
        "gemini-pro-vision",
    ]
    
    @property
    def provider_name(self) -> str:
        return "google"
    
    @property
    def supported_models(self) -> List[str]:
        return self.SUPPORTED_MODELS
    
    def initialize(self) -> None:
        """Initialize the Google AI client using new genai.Client() API."""
        try:
            api_key = self.config.api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
            
            if not api_key:
                raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY environment variable not set")
            
            # New Client-based API (2025)
            self._client = genai.Client(api_key=api_key)
            self._model_name = self.config.model_name
        except ImportError:
            raise ImportError("google-genai package not installed. Run: pip install google-genai")
    
    def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate a completion using new client.models.generate_content() API with Google Search."""
        if self._client is None:
            self.initialize()
        
        # Build content with proper types
        user_message = prompt
        if system_prompt:
            user_message = f"{system_prompt}\n\n{prompt}"
        
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=user_message),
                ],
            ),
        ]
        
        # Add Google Search tool
        tools = [
            types.Tool(googleSearch=types.GoogleSearch()),
        ]
        
        # Configure generation with thinking and Google Search
        config = types.GenerateContentConfig(
            temperature=kwargs.get("temperature", self.config.temperature),
            max_output_tokens=kwargs.get("max_tokens", self.config.max_tokens),
            tools=tools,
            thinking_config=types.ThinkingConfig(
                thinking_budget=-1,  # Unlimited thinking
            ) if kwargs.get("enable_thinking", True) else None,
        )
        
        # Generate content
        response = self._client.models.generate_content(
            model=self._model_name,
            contents=contents,
            config=config
        )
        
        # Extract token usage if available
        tokens_used = 0
        if hasattr(response, 'usage_metadata'):
            tokens_used = getattr(response.usage_metadata, 'total_token_count', 0)
        
        return LLMResponse(
            content=response.text,
            model=self._model_name,
            tokens_used=tokens_used,
            finish_reason="stop",
        )
    
    def stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        callback: Optional[Callable[[str], None]] = None,
        **kwargs
    ) -> str:
        """Stream a completion using new API with Google Search."""
        if self._client is None:
            self.initialize()
        
        # Build content with proper types
        user_message = prompt
        if system_prompt:
            user_message = f"{system_prompt}\n\n{prompt}"
        
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=user_message),
                ],
            ),
        ]
        
        # Add Google Search tool
        tools = [
            types.Tool(googleSearch=types.GoogleSearch()),
        ]
        
        # Configure generation
        config = types.GenerateContentConfig(
            temperature=kwargs.get("temperature", self.config.temperature),
            max_output_tokens=kwargs.get("max_tokens", self.config.max_tokens),
            tools=tools,
            thinking_config=types.ThinkingConfig(
                thinking_budget=-1,
            ) if kwargs.get("enable_thinking", True) else None,
        )
        
        # Stream content
        full_content = ""
        for chunk in self._client.models.generate_content_stream(
            model=self._model_name,
            contents=contents,
            config=config
        ):
            if hasattr(chunk, 'text') and chunk.text:
                full_content += chunk.text
                if callback:
                    callback(chunk.text)
        
        return full_content
    
    async def acomplete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """Async completion."""
        # Google's SDK doesn't have native async, run sync version
        return self.complete(prompt, system_prompt, **kwargs)
    
    async def astream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """Async streaming using new API."""
        if self._client is None:
            self.initialize()
        
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        config = {
            "temperature": kwargs.get("temperature", self.config.temperature),
            "max_output_tokens": kwargs.get("max_tokens", self.config.max_tokens),
        }
        
        # New async streaming API
        response = await self._client.aio.models.generate_content_stream(
            model=self._model_name,
            contents=full_prompt,
            config=config
        )
        
        async for chunk in response:
            if hasattr(chunk, 'text') and chunk.text:
                yield chunk.text
    
    def _create_langchain_llm(self):
        """Create LangChain Google instance."""
        from langchain_google_genai import ChatGoogleGenerativeAI
        
        return ChatGoogleGenerativeAI(
            model=self._model_name,
            temperature=self.config.temperature,
        )
