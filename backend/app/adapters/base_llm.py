"""
Abstract adapter interface for LLM text generation and embeddings.

Design rationale:
  Both GroqAdapter and GeminiAdapter implement this interface.
  Services call self.llm.generate() and self.embedder.embed() without
  knowing which provider is underneath — swapping providers is a single
  change in config.py, not a codebase-wide refactor.

  In practice:
    - GroqAdapter: implements generate() only; embed() raises NotImplementedError.
    - GeminiAdapter: implements embed() only; generate() raises NotImplementedError.
  The application layer uses them as two separate singletons
  (one for generation, one for embeddings) so neither adapter ever
  has to implement both methods.
"""

from abc import ABC, abstractmethod


class BaseLLMAdapter(ABC):
    """Abstract base for text-generation adapters."""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> str:
        """
        Send a prompt to the LLM and return the generated text.

        Args:
            prompt: The user / task message.
            system_prompt: Optional instruction for the model's behaviour.
            temperature: Sampling temperature (0 = deterministic, 1 = creative).
            max_tokens: Maximum tokens in the response.

        Returns:
            The model's text response as a plain string.

        Raises:
            LLMError: on any API-level failure (rate limit, network error, etc.)
        """
        ...


class BaseEmbeddingAdapter(ABC):
    """Abstract base for embedding adapters."""

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """
        Embed a string into a dense float vector.

        Args:
            text: The text to embed (e.g. a document chunk or a user query).

        Returns:
            A list of floats (length = embedding_dimensions, default 768).

        Raises:
            EmbeddingError: on any API-level failure.
        """
        ...


# ─── Custom exceptions ────────────────────────────────────────────────────────

class LLMError(Exception):
    """Raised when an LLM API call fails after retries."""
    pass


class EmbeddingError(Exception):
    """Raised when an embedding API call fails."""
    pass
