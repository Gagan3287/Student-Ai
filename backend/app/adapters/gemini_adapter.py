"""
Gemini adapter — EMBEDDINGS ONLY.

Uses the Gemini REST API to produce 768-dimensional embedding vectors
from text. These vectors are stored in the pgvector column on document_chunks
and used for cosine-similarity RAG retrieval.

Why Gemini for embeddings (and not Groq)?
  Groq does not expose an embeddings endpoint — it is a pure text-generation
  API. Gemini's embedding API is free, accurate, and returns a consistent
  768-dimensional space when called with output_dimensionality=768.

Model: gemini-embedding-001
  This is the current recommended Gemini embedding model (as of mid-2025).
  `models/text-embedding-004` is deprecated and should not be used.
  We fix output_dimensionality=768 to match the VECTOR(768) column and the
  HNSW index built with vector_cosine_ops.
"""

import logging
import httpx

from app.adapters.base_llm import BaseEmbeddingAdapter, EmbeddingError
from app.config import settings

logger = logging.getLogger(__name__)

GEMINI_EMBED_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "{model}:embedContent?key={api_key}"
)


class GeminiAdapter(BaseEmbeddingAdapter):
    def __init__(self):
        self._model = settings.gemini_embedding_model
        self._dimensions = settings.gemini_embedding_dimensions
        self._api_key = settings.gemini_api_key

    async def embed(self, text: str) -> list[float]:
        """
        Embed text using the Gemini embedding API.

        The 'RETRIEVAL_DOCUMENT' task type tells Gemini to optimise the
        embedding for document retrieval (versus semantic similarity or
        classification). Use 'RETRIEVAL_QUERY' for user query embeddings
        so that queries and documents are in the same vector space.
        """
        url = GEMINI_EMBED_URL.format(model=self._model, api_key=self._api_key)
        payload = {
            "model": f"models/{self._model}",
            "content": {"parts": [{"text": text}]},
            "taskType": "RETRIEVAL_DOCUMENT",
            "outputDimensionality": self._dimensions,
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()

            return data["embedding"]["values"]

        except httpx.HTTPStatusError as exc:
            raise EmbeddingError(
                f"Gemini embedding API error ({exc.response.status_code}): {exc.response.text}"
            ) from exc
        except httpx.RequestError as exc:
            raise EmbeddingError(f"Network error calling Gemini API: {exc}") from exc

    async def embed_query(self, text: str) -> list[float]:
        """
        Embed a user query using RETRIEVAL_QUERY task type.
        Use this (not embed()) when embedding a chat question for RAG retrieval.
        """
        url = GEMINI_EMBED_URL.format(model=self._model, api_key=self._api_key)
        payload = {
            "model": f"models/{self._model}",
            "content": {"parts": [{"text": text}]},
            "taskType": "RETRIEVAL_QUERY",
            "outputDimensionality": self._dimensions,
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()

            return data["embedding"]["values"]

        except httpx.HTTPStatusError as exc:
            raise EmbeddingError(
                f"Gemini embedding API error ({exc.response.status_code}): {exc.response.text}"
            ) from exc
        except httpx.RequestError as exc:
            raise EmbeddingError(f"Network error calling Gemini API: {exc}") from exc


# Module-level singleton — import this in document_service and chat_service
gemini_adapter = GeminiAdapter()
