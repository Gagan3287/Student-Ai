"""
Document service — handles parsing, chunking, embedding generation,
concept extraction, and database persistence in background tasks.
"""

import asyncio
import io
import json
import logging
import re
import uuid
import pypdf

from app.adapters.gemini_adapter import gemini_adapter
from app.adapters.groq_adapter import groq_adapter
from app.database import SessionLocal
from app.models.document import Document
from app.models.chunk import DocumentChunk
from app.models.concept import Concept, ConceptLink

logger = logging.getLogger(__name__)

# ─── Constants ────────────────────────────────────────────────────────────────

# Maximum number of chunks embedded per document to avoid Gemini quota exhaustion.
# Large PDFs (8MB+) can produce 500+ chunks — we cap at 300 and surface this
# to the user via a note appended to the document summary.
MAX_CHUNKS = 300

# Delay between consecutive Gemini embedding calls (seconds).
# 0.5 s is conservative enough to stay under the free-tier RPM limit for
# gemini-embedding-001 (which is ~1500 RPM / ~25 RPS as of mid-2025).
EMBEDDING_INTER_CALL_DELAY = 0.5


# ─── Text Extraction Helpers ──────────────────────────────────────────────────

def extract_text_from_pdf(file_bytes: bytes) -> tuple[list[str], int]:
    """
    Extract text page-by-page from PDF bytes.
    Returns (list of page texts, total page count).
    """
    try:
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        pages_text = []
        for i, page in enumerate(reader.pages):
            try:
                text = page.extract_text()
                pages_text.append(text or "")
            except Exception as exc:
                logger.warning(f"Failed to extract text from PDF page {i}: {exc}")
                pages_text.append("")
        return pages_text, len(reader.pages)
    except Exception as exc:
        logger.error(f"Failed to parse PDF file bytes: {exc}")
        raise ValueError(f"Invalid PDF file structure: {exc}") from exc


def extract_text_from_txt(file_bytes: bytes) -> tuple[list[str], int]:
    """
    Decode TXT bytes as UTF-8 or latin-1 fallback.
    Returns (list of length 1, 1 page count).
    """
    try:
        text = file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        logger.warning("UTF-8 decoding failed, falling back to latin-1")
        text = file_bytes.decode("latin-1")
    return [text], 1


# ─── Chunking Helper ─────────────────────────────────────────────────────────

def chunk_text(pages_text: list[str], chunk_size: int = 1500, overlap: int = 200) -> list[dict]:
    """
    Chunk text page-by-page to preserve page numbers.
    If page text is longer than chunk_size, use a sliding window.
    Returns [{\"content\": str, \"page_number\": int, \"chunk_index\": int}].
    """
    chunks = []
    chunk_index = 0

    for i, page_text in enumerate(pages_text):
        page_number = i + 1
        text = page_text.strip()
        if not text:
            continue

        if len(text) <= chunk_size:
            chunks.append({
                "content": text,
                "page_number": page_number,
                "chunk_index": chunk_index
            })
            chunk_index += 1
        else:
            start = 0
            while start < len(text):
                end = start + chunk_size
                chunk_content = text[start:end].strip()
                if chunk_content:
                    chunks.append({
                        "content": chunk_content,
                        "page_number": page_number,
                        "chunk_index": chunk_index
                    })
                    chunk_index += 1
                start += (chunk_size - overlap)

    return chunks


# ─── DB Insertion Helpers ─────────────────────────────────────────────────────

def update_document_status(
    document_id: uuid.UUID,
    status: str,
    page_count: int | None = None,
    summary: str | None = None,
) -> None:
    """Synchronous database operation to update a document's status, page count, and summary."""
    db = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if doc:
            doc.status = status
            if page_count is not None:
                doc.page_count = page_count
            if summary is not None:
                doc.summary = summary
            db.commit()
    except Exception as exc:
        db.rollback()
        logger.error(f"Failed to update document status for {document_id}: {exc}")
        raise
    finally:
        db.close()


def save_document_chunks(document_id: uuid.UUID, chunks_data: list[dict]) -> None:
    """Synchronous database operation to insert document chunks and delete any old ones."""
    db = SessionLocal()
    try:
        # Avoid duplicate chunks by purging first
        db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).delete()

        for chunk in chunks_data:
            db_chunk = DocumentChunk(
                document_id=document_id,
                chunk_index=chunk["chunk_index"],
                page_number=chunk["page_number"],
                content=chunk["content"],
                embedding=chunk["embedding"]
            )
            db.add(db_chunk)
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.error(f"Failed to save document chunks for {document_id}: {exc}")
        raise
    finally:
        db.close()


def save_concepts_to_db(
    document_id: uuid.UUID,
    user_id: uuid.UUID,
    concepts_list: list[str],
    links_list: list[dict],
) -> None:
    """
    Persist extracted concept nodes and edges for this document.
    Replaces any previously extracted concepts for the same document.
    """
    db = SessionLocal()
    try:
        # Remove stale concepts (and cascade-delete their links via FK)
        db.query(Concept).filter(Concept.document_id == document_id).delete()
        db.commit()

        # Insert concept nodes
        concept_map: dict[str, Concept] = {}
        for name in concepts_list:
            clean_name = name.strip()[:490]
            if not clean_name or clean_name in concept_map:
                continue
            c = Concept(
                id=uuid.uuid4(),
                user_id=user_id,
                document_id=document_id,
                name=clean_name,
            )
            db.add(c)
            concept_map[clean_name] = c
        db.flush()

        # Insert edges — deduplicate by (source, target) pair to respect UniqueConstraint
        added_pairs: set[tuple[str, str]] = set()
        for link in links_list:
            src_name = link.get("source", "").strip()
            tgt_name = link.get("target", "").strip()
            if (
                src_name in concept_map
                and tgt_name in concept_map
                and src_name != tgt_name
                and (src_name, tgt_name) not in added_pairs
            ):
                added_pairs.add((src_name, tgt_name))
                label = (link.get("label") or "relates to")[:255]
                cl = ConceptLink(
                    id=uuid.uuid4(),
                    source_id=concept_map[src_name].id,
                    target_id=concept_map[tgt_name].id,
                    relation_label=label,
                )
                db.add(cl)

        db.commit()
        logger.info(
            f"Saved {len(concept_map)} concepts and {len(added_pairs)} links for document {document_id}"
        )
    except Exception as exc:
        db.rollback()
        logger.error(f"Failed to save concepts for {document_id}: {exc}")
        raise
    finally:
        db.close()


# ─── AI Call Helpers ──────────────────────────────────────────────────────────

async def generate_embeddings_with_retry(chunks: list[dict]) -> list[list[float]]:
    """
    Generate Gemini embeddings sequentially with per-call delay and dynamic
    backoff retry to respect API rate limits (handling 429 17s+ quota delays).

    Two distinct 429 scenarios are handled differently:
      - Per-minute RPM quota: retryDelay is small (seconds). We wait and retry.
      - Daily quota exhaustion (RESOURCE_EXHAUSTED / PerDay quotaId): irrecoverable
        until the quota resets (~midnight PST). We fail fast — no retries — and
        surface a clear, actionable error message to the user.
    """
    embeddings = []
    for i, chunk in enumerate(chunks):
        max_attempts = 5
        delay = 3.0
        embedding = None
        last_exc: Exception | None = None

        for attempt in range(max_attempts):
            try:
                embedding = await gemini_adapter.embed(chunk["content"])
                break
            except Exception as exc:
                last_exc = exc
                remaining = max_attempts - attempt - 1
                exc_str = str(exc)

                # ── Daily quota exhaustion — fail fast, do NOT retry ──────────
                # Gemini returns RESOURCE_EXHAUSTED with a quotaId containing
                # "PerDay" when the daily free-tier cap (1000 requests/day) is
                # hit.  Retrying is pointless — the quota resets at midnight PST.
                if "RESOURCE_EXHAUSTED" in exc_str or (
                    "429" in exc_str and "PerDay" in exc_str
                ):
                    logger.error(
                        f"Gemini daily embedding quota exhausted for document "
                        f"(chunk {i}). Failing fast — no retries will help until "
                        f"the quota resets (~midnight PST): {exc}"
                    )
                    raise RuntimeError(
                        "Gemini embedding quota exhausted for today (free-tier limit: "
                        "1,000 embed calls/day). Please retry tomorrow once the quota "
                        "resets, or upgrade your Gemini API plan. "
                        "No data was lost — click Retry after the quota resets."
                    ) from exc

                # ── Per-minute rate limit — backoff and retry ─────────────────
                wait_time = delay
                if "429" in exc_str:
                    delay_match = re.search(r'"retryDelay":\s*"(\d+(?:\.\d+)?)s"', exc_str)
                    if delay_match:
                        wait_time = float(delay_match.group(1)) + 1.5
                    else:
                        wait_time = max(delay, 15.0)

                logger.warning(
                    f"Gemini embedding failed for chunk {i}, attempt {attempt + 1}/{max_attempts} "
                    f"({remaining} retries left). Waiting {wait_time:.1f}s: {exc}"
                )
                if remaining > 0:
                    await asyncio.sleep(wait_time)
                    delay = min(delay * 2.0, 30.0)

        if embedding is None:
            raise last_exc  # propagate to outer handler → sets status='error'

        embeddings.append(embedding)
        # Throttle between successful calls to stay under RPM limit
        await asyncio.sleep(EMBEDDING_INTER_CALL_DELAY)

    return embeddings


async def generate_summary(chunks: list[dict]) -> str:
    """Generate summary using Groq API llama-3.3-70b-versatile model."""
    summary_chunks = chunks[:3]
    combined_text = "\n\n".join([c["content"] for c in summary_chunks])

    prompt = (
        "You are an expert engineering study assistant.\n"
        "Provide a concise summary (around 3-5 sentences) of the following course materials or notes, "
        "highlighting the core topics covered:\n\n"
        f"{combined_text}\n\n"
        "Summary:"
    )

    system_prompt = "You are a helpful academic study companion."
    try:
        summary = await groq_adapter.generate(prompt, system_prompt=system_prompt)
        return summary.strip()
    except Exception as exc:
        logger.error(f"Summary generation failed: {exc}")
        return "Summary could not be generated due to an AI service rate limit or error."


async def extract_and_save_concepts(
    document_id: uuid.UUID,
    user_id: uuid.UUID,
    chunks: list[dict],
) -> None:
    """
    Use Groq to extract key concepts and relationships from the document chunks,
    then persist them so the Knowledge Graph can display them.

    Samples the first 10 chunks (up to 4000 chars each) for the prompt to stay
    within Groq's context window.  Failure is non-fatal — if this step errors,
    the document still transitions to 'ready'.
    """
    # Sample chunks: first 10 to keep prompt size manageable
    sample_chunks = chunks[:10]
    combined_text = "\n\n---\n\n".join(c["content"] for c in sample_chunks)
    # Trim combined text to 5000 chars to stay within context limits
    combined_text = combined_text[:5000]

    prompt = (
        "You are an expert at extracting structured knowledge from academic documents.\n"
        "Analyse the following text and extract:\n"
        "1. The 15-20 most important technical concepts, topics, or terms.\n"
        "2. Meaningful relationships between those concepts.\n\n"
        "Return ONLY valid JSON in this exact format (no explanation, no markdown fences):\n"
        '{"concepts": ["Concept A", "Concept B", ...], '
        '"links": [{"source": "Concept A", "target": "Concept B", "label": "is a type of"}]}\n\n'
        "TEXT:\n"
        f"{combined_text}"
    )

    try:
        raw = await groq_adapter.generate(prompt, temperature=0.1, max_tokens=1500)
        # Extract the JSON object even if the model adds surrounding text
        json_match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not json_match:
            logger.warning(f"Concept extraction for {document_id}: no JSON found in model output.")
            return

        data = json.loads(json_match.group())
        concepts_list: list[str] = data.get("concepts", [])
        links_list: list[dict] = data.get("links", [])

        if not concepts_list:
            logger.info(f"Concept extraction for {document_id}: model returned 0 concepts.")
            return

        await asyncio.to_thread(save_concepts_to_db, document_id, user_id, concepts_list, links_list)
        logger.info(f"Concept extraction complete for document {document_id}.")

    except json.JSONDecodeError as exc:
        logger.warning(f"Concept extraction JSON parse error for {document_id}: {exc}")
    except Exception as exc:
        logger.warning(f"Concept extraction failed for {document_id} (non-fatal): {exc}")


# ─── Main Background Task ─────────────────────────────────────────────────────

async def process_document_background(document_id: uuid.UUID, file_bytes: bytes, content_type: str):
    """
    FastAPI BackgroundTask entry point. Runs CPU-bound text extraction/chunking and blocking
    DB transactions inside worker threads, while executing async network API calls on the event loop.

    Any unhandled exception in Steps 1-8 is caught by the outer try/except, which
    sets status='error' and writes the error message to the summary field.
    This guarantees the document NEVER hangs in 'processing' forever.
    """
    logger.info(f"Background processing started for document {document_id}")
    try:
        # Step 1: Set status to processing
        await asyncio.to_thread(update_document_status, document_id, "processing")

        # Step 2: Extract text (CPU-bound)
        if content_type == "application/pdf":
            pages_text, page_count = await asyncio.to_thread(extract_text_from_pdf, file_bytes)
        else:
            pages_text, page_count = await asyncio.to_thread(extract_text_from_txt, file_bytes)

        # Step 3: Chunk text (CPU-bound)
        all_chunks = await asyncio.to_thread(chunk_text, pages_text)
        if not all_chunks:
            raise ValueError("No readable text content found in document.")

        # Step 4: Apply MAX_CHUNKS cap — surface truncation in summary if hit
        original_chunk_count = len(all_chunks)
        truncation_note = ""
        if original_chunk_count > MAX_CHUNKS:
            logger.warning(
                f"Document {document_id} produced {original_chunk_count} chunks, "
                f"truncating to {MAX_CHUNKS} for indexing."
            )
            all_chunks = all_chunks[:MAX_CHUNKS]
            truncation_note = (
                f"\n\n⚠️ Large document notice: This file produced {original_chunk_count} text sections. "
                f"Only the first {MAX_CHUNKS} sections were indexed for AI search and chat. "
                f"Content beyond that point cannot be retrieved in the Doubt Solver."
            )

        # Step 5: Generate embeddings (Async API — rate-limited, with retry backoff)
        embeddings = await generate_embeddings_with_retry(all_chunks)

        # Attach embeddings to chunk dicts
        for chunk, embedding in zip(all_chunks, embeddings):
            chunk["embedding"] = embedding

        # Step 6: Save chunks to DB (Blocking DB I/O)
        await asyncio.to_thread(save_document_chunks, document_id, all_chunks)

        # Step 7: Generate summary (Async API)
        summary = await generate_summary(all_chunks)
        if truncation_note:
            summary = summary + truncation_note

        # Step 8: Extract concepts for Knowledge Graph (non-fatal — wrapped in own try/except)
        try:
            # Retrieve user_id from DB so we can associate concepts with the user
            db = SessionLocal()
            try:
                doc = db.query(Document).filter(Document.id == document_id).first()
                user_id = doc.user_id if doc else None
            finally:
                db.close()

            if user_id:
                await extract_and_save_concepts(document_id, user_id, all_chunks)
            else:
                logger.warning(f"Could not resolve user_id for concept extraction on {document_id}")
        except Exception as concept_exc:
            # Concept extraction failing must NOT prevent the document from becoming ready
            logger.warning(f"Concept extraction step failed for {document_id} (non-fatal): {concept_exc}")

        # Step 9: Mark document as ready
        await asyncio.to_thread(update_document_status, document_id, "ready", page_count, summary)
        logger.info(f"Background processing successfully completed for document {document_id}")

    except Exception as exc:
        # Catch-all: any unhandled exception sets status='error' so the document
        # never hangs in 'processing' forever.
        logger.error(f"Error processing document {document_id}: {exc}", exc_info=True)
        try:
            error_msg = f"Failed to process document. Error: {str(exc)}"
            await asyncio.to_thread(update_document_status, document_id, "error", None, error_msg)
        except Exception as db_exc:
            logger.error(f"Failed to record error state to DB for document {document_id}: {db_exc}")
