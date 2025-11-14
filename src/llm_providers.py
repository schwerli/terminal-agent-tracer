"""
LLM provider implementations for failure analysis.
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import os
import json


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    def __init__(self, model_name: str, api_key: Optional[str] = None):
        self.model_name = model_name
        self.api_key = api_key or self._get_api_key_from_env()
    
    @abstractmethod
    def _get_api_key_from_env(self) -> Optional[str]:
        """Get API key from environment variable."""
        pass
    
    @abstractmethod
    async def analyze(self, prompt: str) -> str:
        """Send analysis request to LLM and return response."""
        pass
    
    @abstractmethod
    def analyze_sync(self, prompt: str) -> str:
        """Synchronous version of analyze."""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI API provider."""
    
    def _get_api_key_from_env(self) -> Optional[str]:
        return os.getenv("OPENAI_API_KEY")
    
    async def analyze(self, prompt: str) -> str:
        """Async analysis using OpenAI API."""
        try:
            import openai
            client = openai.AsyncOpenAI(api_key=self.api_key)
            
            response = await client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing AI agent failures and debugging complex systems."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"OpenAI API error: {str(e)}")
    
    def analyze_sync(self, prompt: str) -> str:
        """Synchronous analysis using OpenAI API."""
        try:
            import openai
            client = openai.OpenAI(api_key=self.api_key)
            
            response = client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing AI agent failures and debugging complex systems."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"OpenAI API error: {str(e)}")


class AnthropicProvider(LLMProvider):
    """Anthropic (Claude) API provider."""
    
    def _get_api_key_from_env(self) -> Optional[str]:
        return os.getenv("ANTHROPIC_API_KEY")
    
    async def analyze(self, prompt: str) -> str:
        """Async analysis using Anthropic API."""
        try:
            import anthropic
            client = anthropic.AsyncAnthropic(api_key=self.api_key)
            
            response = await client.messages.create(
                model=self.model_name,
                system="You are an expert at analyzing AI agent failures and debugging complex systems.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return response.content[0].text
        except Exception as e:
            raise RuntimeError(f"Anthropic API error: {str(e)}")
    
    def analyze_sync(self, prompt: str) -> str:
        """Synchronous analysis using Anthropic API."""
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.api_key)
            
            response = client.messages.create(
                model=self.model_name,
                system="You are an expert at analyzing AI agent failures and debugging complex systems.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return response.content[0].text
        except Exception as e:
            raise RuntimeError(f"Anthropic API error: {str(e)}")


class CustomProvider(LLMProvider):
    """Custom API provider with OpenAI-compatible interface."""
    
    def __init__(self, model_name: str, api_key: Optional[str] = None, 
                 base_url: Optional[str] = None):
        super().__init__(model_name, api_key)
        self.base_url = base_url or os.getenv("CUSTOM_API_BASE_URL", "http://localhost:8000/v1")
    
    def _get_api_key_from_env(self) -> Optional[str]:
        return os.getenv("CUSTOM_API_KEY", "dummy-key")
    
    async def analyze(self, prompt: str) -> str:
        """Async analysis using custom API."""
        try:
            import openai
            client = openai.AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
            
            response = await client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing AI agent failures and debugging complex systems."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"Custom API error: {str(e)}")
    
    def analyze_sync(self, prompt: str) -> str:
        """Synchronous analysis using custom API."""
        try:
            import openai
            client = openai.OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
            
            response = client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing AI agent failures and debugging complex systems."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"Custom API error: {str(e)}")


def get_provider(provider_name: str, model_name: str, 
                 api_key: Optional[str] = None, 
                 base_url: Optional[str] = None) -> LLMProvider:
    """Factory function to get appropriate provider."""
    provider_name = provider_name.lower()
    
    if provider_name == "openai":
        return OpenAIProvider(model_name, api_key)
    elif provider_name == "anthropic":
        return AnthropicProvider(model_name, api_key)
    elif provider_name == "custom":
        return CustomProvider(model_name, api_key, base_url)
    else:
        raise ValueError(f"Unknown provider: {provider_name}. Use 'openai', 'anthropic', or 'custom'.")

