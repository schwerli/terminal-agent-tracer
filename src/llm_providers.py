"""
LLM provider implementations for failure analysis.

This module defines a single OpenAI-compatible provider. All calls are made
through the OpenAI Python SDK using:
- model_name
- api_key
- base_url (for any OpenAI-compatible endpoint, e.g. ChatAnywhere)
"""
from abc import ABC, abstractmethod
from typing import Optional
import os


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
    """
    Simplified OpenAI-compatible provider.

    Uses the OpenAI Python SDK and supports any OpenAI-compatible endpoint
    by configuring api_key and base_url.
    """

    def __init__(self, model_name: str, api_key: Optional[str] = None,
                 base_url: Optional[str] = None):
        super().__init__(model_name, api_key)
        self.base_url = (
            base_url
            or os.getenv("OPENAI_BASE_URL")
            or "https://api.openai.com/v1"
        )

    def _get_api_key_from_env(self) -> Optional[str]:
        return os.getenv("OPENAI_API_KEY")

    async def analyze(self, prompt: str) -> str:
        """Async analysis using an OpenAI-compatible API."""
        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
            )

            response = await client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at analyzing AI agent failures and debugging complex systems.",
                    },
                    {"role": "user", "content": prompt},
                ],
            )

            return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"OpenAI API error: {str(e)}")

    def analyze_sync(self, prompt: str) -> str:
        """Synchronous analysis using an OpenAI-compatible API."""
        try:
            from openai import OpenAI

            client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
            )

            response = client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at analyzing AI agent failures and debugging complex systems.",
                    },
                    {"role": "user", "content": prompt},
                ],
            )

            return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"OpenAI API error: {str(e)}")


def get_provider(provider_name: str, model_name: str,
                 api_key: Optional[str] = None,
                 base_url: Optional[str] = None) -> LLMProvider:
    """
    Factory function for the OpenAI-compatible provider.

    The provider_name argument is accepted for backward compatibility but
    is ignored. All calls use OpenAIProvider with the given model_name,
    api_key, and base_url.
    """
    return OpenAIProvider(model_name, api_key, base_url)


