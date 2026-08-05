import logging
from typing import Optional, Protocol

import httpx

from src.config import settings

logger = logging.getLogger(__name__)


class LLMClient(Protocol):
    """
    Protocol defining the async LLM completion interface.
    """

    async def generate_completion(
        self, system_prompt: str, user_prompt: str
    ) -> str:
        ...


class GroqClient:
    """
    Groq implementation supporting AsyncGroq (or AsyncOpenAI with Groq base URL)
    and JSON response format.
    """

    def __init__(
        self,
        api_key: str = settings.GROQ_API_KEY,
        model: str = settings.GROQ_MODEL,
    ):
        self.api_key = api_key
        self.model = model
        self._client = None

        if self.api_key:
            try:
                from groq import AsyncGroq

                self._client = AsyncGroq(api_key=self.api_key)
            except ImportError:
                try:
                    from openai import AsyncOpenAI

                    self._client = AsyncOpenAI(
                        api_key=self.api_key,
                        base_url="https://api.groq.com/openai/v1",
                    )
                except ImportError:
                    logger.warning(
                        "Neither groq nor openai package is installed. "
                        "GroqClient disabled."
                    )


    async def generate_completion(
        self, system_prompt: str, user_prompt: str
    ) -> str:
        if not self.api_key or not self._client:
            raise RuntimeError(
                "GROQ_API_KEY is not configured or client library missing."
            )

        response = await self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
        )
        return response.choices[0].message.content or "{}"


class OpenAIClient:
    """
    OpenAI implementation supporting AsyncOpenAI and JSON mode.
    """

    def __init__(
        self,
        api_key: str = settings.OPENAI_API_KEY,
        model: str = settings.OPENAI_MODEL,
    ):
        self.api_key = api_key
        self.model = model
        self._client = None

        if self.api_key:
            try:
                from openai import AsyncOpenAI

                self._client = AsyncOpenAI(api_key=self.api_key)
            except ImportError:
                logger.warning(
                    "openai package not installed. OpenAIClient disabled."
                )

    async def generate_completion(
        self, system_prompt: str, user_prompt: str
    ) -> str:
        if not self.api_key or not self._client:
            raise RuntimeError(
                "OPENAI_API_KEY is not configured or openai package missing."
            )

        response = await self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
        )
        return response.choices[0].message.content or "{}"


class OllamaClient:
    """
    Ollama implementation for offline local LLM inference.
    """

    def __init__(
        self, base_url: str = "http://localhost:11434", model: str = "llama3"
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def generate_completion(
        self, system_prompt: str, user_prompt: str
    ) -> str:
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "format": "json",
            "stream": False,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.post(url, json=payload)
            res.raise_for_status()
            data = res.json()
            return data.get("message", {}).get("content", "{}")


class MockLLMClient:
    """
    Mock LLM client returning configurable JSON responses for unit testing.
    """

    def __init__(self, default_response: Optional[str] = None):
        self.default_response = default_response or "{}"

    async def generate_completion(
        self, system_prompt: str, user_prompt: str
    ) -> str:
        return self.default_response


def get_llm_client() -> LLMClient:
    """
    Factory function returning the configured LLMClient.
    """
    provider = settings.LLM_PROVIDER.lower().strip()
    if provider == "groq":
        return GroqClient()
    elif provider == "openai":
        return OpenAIClient()
    elif provider == "ollama":
        return OllamaClient()
    elif provider == "mock":
        return MockLLMClient()
    else:
        logger.warning(
            f"Unknown LLM_PROVIDER '{provider}'. Falling back to MockLLMClient."
        )
        return MockLLMClient()
