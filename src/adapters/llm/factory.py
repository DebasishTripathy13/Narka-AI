"""LLM provider factory."""

from typing import Optional, Dict, Type
import os

from .base import BaseLLMProvider
from .openai import OpenAIProvider
from .anthropic import AnthropicProvider
from .google import GoogleProvider
from .ollama import OllamaProvider
from ...core.interfaces.llm_provider import LLMConfig


# Model to provider mapping
MODEL_PROVIDER_MAP: Dict[str, Type[BaseLLMProvider]] = {
    # OpenAI models - GPT-5 series (2025)
    "gpt-5.1": OpenAIProvider,        # Best for coding and agentic tasks
    "gpt-5-mini": OpenAIProvider,     # Faster, cost-efficient
    "gpt-5-nano": OpenAIProvider,     # Fastest, most cost-efficient
    # OpenAI models - GPT-4 series
    "gpt-4.1": OpenAIProvider,
    "gpt-4o": OpenAIProvider,
    "gpt-4o-mini": OpenAIProvider,
    "gpt-4-turbo": OpenAIProvider,
    "gpt-4": OpenAIProvider,
    "gpt-3.5-turbo": OpenAIProvider,
    # OpenAI specialized models
    "gpt-image-1": OpenAIProvider,    # Image generation
    "o1": OpenAIProvider,             # Reasoning model
    "o1-mini": OpenAIProvider,        # Mini reasoning model
    
    # Anthropic models
    "claude-3-opus-20240229": AnthropicProvider,
    "claude-3-sonnet-20240229": AnthropicProvider,
    "claude-3-haiku-20240307": AnthropicProvider,
    "claude-3-5-sonnet-latest": AnthropicProvider,
    "claude-sonnet-4-5": AnthropicProvider,
    "claude-sonnet-4-0": AnthropicProvider,
    
    # Google models - Gemini 3 (2025)
    "gemini-3-pro": GoogleProvider,       # Most intelligent, best multimodal
    # Google models - Gemini 2.5
    "gemini-2.5-pro": GoogleProvider,     # Powerful reasoning, coding
    "gemini-2.5-flash": GoogleProvider,   # Balanced, 1M token context
    "gemini-2.5-flash-lite": GoogleProvider,  # Fastest, cost-efficient
    # Google models - Media generation
    "veo-3.1": GoogleProvider,            # Video generation with audio
    "nano-banana": GoogleProvider,        # Image generation
    "nano-banana-pro": GoogleProvider,    # Advanced image generation
    # Google models - Legacy
    "gemini-2.0-flash": GoogleProvider,
    "gemini-1.5-pro": GoogleProvider,
    "gemini-1.5-flash": GoogleProvider,
    "gemini-pro": GoogleProvider,
    
    # Ollama models (local)
    "llama3.2": OllamaProvider,
    "llama3.1": OllamaProvider,
    "llama3": OllamaProvider,
    "llama2": OllamaProvider,
    "mistral": OllamaProvider,
    "mixtral": OllamaProvider,
    "codellama": OllamaProvider,
    "gemma3": OllamaProvider,
    "gemma2": OllamaProvider,
    "qwen2.5": OllamaProvider,
    "deepseek-r1": OllamaProvider,
    "phi3": OllamaProvider,
}


class LLMFactory:
    """
    Factory for creating LLM provider instances.
    """
    
    @staticmethod
    def get_provider_class(model_name: str) -> Type[BaseLLMProvider]:
        """Get the provider class for a model."""
        model_lower = model_name.lower()
        
        # Direct lookup
        if model_lower in MODEL_PROVIDER_MAP:
            return MODEL_PROVIDER_MAP[model_lower]
        
        # Prefix matching
        if model_lower.startswith("gpt"):
            return OpenAIProvider
        elif model_lower.startswith("claude"):
            return AnthropicProvider
        elif model_lower.startswith("gemini"):
            return GoogleProvider
        else:
            # Default to Ollama for unknown models (assume local)
            return OllamaProvider
    
    @staticmethod
    def create(
        model_name: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.0,
        streaming: bool = True,
        **kwargs
    ) -> BaseLLMProvider:
        """
        Create an LLM provider instance.
        
        Args:
            model_name: Name of the model
            api_key: Optional API key (will use env var if not provided)
            base_url: Optional base URL (for Ollama)
            temperature: Temperature setting
            streaming: Enable streaming
            **kwargs: Additional config options
            
        Returns:
            Configured LLM provider instance
        """
        provider_class = LLMFactory.get_provider_class(model_name)
        
        config = LLMConfig(
            model_name=model_name,
            api_key=api_key,
            base_url=base_url,
            temperature=temperature,
            streaming=streaming,
            **kwargs
        )
        
        provider = provider_class(config)
        provider.initialize()
        
        return provider
    
    @staticmethod
    def list_supported_models() -> Dict[str, list]:
        """List all supported models by provider."""
        return {
            "openai": OpenAIProvider.SUPPORTED_MODELS,
            "anthropic": AnthropicProvider.SUPPORTED_MODELS,
            "google": GoogleProvider.SUPPORTED_MODELS,
            "ollama": OllamaProvider.SUPPORTED_MODELS,
        }


def get_llm_provider(
    model_name: str,
    **kwargs
) -> BaseLLMProvider:
    """
    Convenience function to get an LLM provider.
    
    Args:
        model_name: Name of the model
        **kwargs: Additional configuration
        
    Returns:
        Configured LLM provider instance
    """
    return LLMFactory.create(model_name, **kwargs)
