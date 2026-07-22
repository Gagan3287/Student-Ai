"""
Groq adapter — PRIMARY text-generation adapter.

Uses Groq's free-tier LLM API (OpenAI-compatible REST endpoint).
Default model: llama-3.3-70b-versatile (GPT-4-class quality, extremely fast).
Fallback model: llama-3.1-8b-instant (higher rate-limit quota, lower quality).

Why Groq?
  - LPU (Language Processing Unit) hardware: 5–10× faster token generation
    than GPU-based providers for the same model size.
  - Free tier: rate-limited per minute/day, NOT token-metered — very generous
    for a development and demo workload.
  - OpenAI-compatible API: minimal adapter code, easy to maintain.

Rate-limit handling:
  If the primary model returns HTTP 429, this adapter automatically retries
  once with the fallback model (llama-3.1-8b-instant). If that also fails,
  a LLMError is raised and the caller returns a user-facing error message
  (never a server crash — see ARCHITECTURE.md for the graceful-degradation design).
"""

import logging
import httpx

from app.adapters.base_llm import BaseLLMAdapter, LLMError
from app.config import settings

logger = logging.getLogger(__name__)

GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"


class GroqAdapter(BaseLLMAdapter):
    def __init__(self):
        self._headers = {
            "Authorization": f"Bearer {settings.groq_api_key}",
            "Content-Type": "application/json",
        }

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> str:
        """
        Call Groq's chat completions endpoint.
        Retries once with the fallback model on HTTP 429 (rate limit).
        """
        for model in (settings.groq_model_primary, settings.groq_model_fallback):
            try:
                response_text = await self._call(model, prompt, system_prompt, temperature, max_tokens)
                return response_text
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 429 and model == settings.groq_model_primary:
                    logger.warning(
                        f"Groq rate limit hit on {model}, retrying with fallback model "
                        f"{settings.groq_model_fallback}"
                    )
                    continue
                raise LLMError(
                    f"Groq API error ({exc.response.status_code}): {exc.response.text}"
                ) from exc
            except httpx.RequestError as exc:
                raise LLMError(f"Network error calling Groq API: {exc}") from exc

        raise LLMError("Groq API rate limit exceeded on both primary and fallback models.")

    async def _call(
        self,
        model: str,
        prompt: str,
        system_prompt: str | None,
        temperature: float,
        max_tokens: int,
    ) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(GROQ_CHAT_URL, headers=self._headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        return data["choices"][0]["message"]["content"]


# Module-level singleton — import this in services
groq_adapter = GroqAdapter()
