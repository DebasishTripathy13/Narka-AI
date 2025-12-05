"""Ollama LLM provider for local models."""

from typing import Optional, List, Callable, AsyncIterator
import os

from .base import BaseLLMProvider
from ...core.interfaces.llm_provider import LLMConfig, LLMResponse


class OllamaProvider(BaseLLMProvider):
    """
    Ollama LLM provider implementation.
    
    Supports local models via Ollama.
    """
    
    SUPPORTED_MODELS = [
        "llama3.2",
        "llama3.1",
        "llama3",
        "llama2",
        "mistral",
        "mixtral",
        "codellama",
        "gemma3",
        "gemma2",
        "qwen2.5",
        "deepseek-r1",
        "phi3",
    ]
    
    @property
    def provider_name(self) -> str:
        return "ollama"
    
    @property
    def supported_models(self) -> List[str]:
        return self.SUPPORTED_MODELS
    
    def initialize(self) -> None:
        """Initialize the Ollama client."""
        try:
            import ollama
            
            base_url = self.config.base_url or os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
            
            # Set the host
            self._base_url = base_url
            self._client = ollama
        except ImportError:
            raise ImportError("ollama package not installed. Run: pip install ollama")
    
    def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate a completion."""
        if self._client is None:
            self.initialize()
        
        messages = self._build_messages(prompt, system_prompt)
        
        # Add :latest suffix if not present
        model_name = self.config.model_name
        if ":" not in model_name:
            model_name = f"{model_name}:latest"
        
        response = self._client.chat(
            model=model_name,
            messages=messages,
            options={
                "temperature": kwargs.get("temperature", self.config.temperature),
            }
        )
        
        return LLMResponse(
            content=response['message']['content'],
            model=model_name,
            tokens_used=response.get('eval_count', 0) + response.get('prompt_eval_count', 0),
            prompt_tokens=response.get('prompt_eval_count', 0),
            completion_tokens=response.get('eval_count', 0),
            finish_reason="stop",
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
        
        model_name = self.config.model_name
        if ":" not in model_name:
            model_name = f"{model_name}:latest"
        
        full_content = ""
        
        stream = self._client.chat(
            model=model_name,
            messages=messages,
            options={
                "temperature": kwargs.get("temperature", self.config.temperature),
            },
            stream=True
        )
        
        for chunk in stream:
            content = chunk['message']['content']
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
        import ollama
        
        messages = self._build_messages(prompt, system_prompt)
        
        model_name = self.config.model_name
        if ":" not in model_name:
            model_name = f"{model_name}:latest"
        
        response = await ollama.AsyncClient().chat(
            model=model_name,
            messages=messages,
            options={
                "temperature": kwargs.get("temperature", self.config.temperature),
            }
        )
        
        return LLMResponse(
            content=response['message']['content'],
            model=model_name,
            tokens_used=response.get('eval_count', 0) + response.get('prompt_eval_count', 0),
            prompt_tokens=response.get('prompt_eval_count', 0),
            completion_tokens=response.get('eval_count', 0),
            finish_reason="stop",
        )
    
    async def astream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """Async streaming."""
        import ollama
        
        messages = self._build_messages(prompt, system_prompt)
        
        model_name = self.config.model_name
        if ":" not in model_name:
            model_name = f"{model_name}:latest"
        
        async for chunk in await ollama.AsyncClient().chat(
            model=model_name,
            messages=messages,
            options={
                "temperature": kwargs.get("temperature", self.config.temperature),
            },
            stream=True
        ):
            yield chunk['message']['content']
    
    def _create_langchain_llm(self):
        """Create LangChain Ollama instance."""
        from langchain_ollama import ChatOllama
        
        base_url = self.config.base_url or os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
        
        model_name = self.config.model_name
        if ":" not in model_name:
            model_name = f"{model_name}:latest"
        
        return ChatOllama(
            model=model_name,
            base_url=base_url,
            temperature=self.config.temperature,
        )
    
    def list_models(self) -> List[str]:
        """List available models on the Ollama server."""
        if self._client is None:
            self.initialize()
        
        try:
            models = self._client.list()
            return [m['name'] for m in models.get('models', [])]
        except Exception:
            return []
    
    def pull_model(self, model_name: str) -> bool:
        """Pull a model from the Ollama library."""
        if self._client is None:
            self.initialize()
        
        try:
            self._client.pull(model_name)
            return True
        except Exception:
            return False
