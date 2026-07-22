"""
Scratch script to verify Phase 2 Document Processing logic.
Tests text extraction, chunking, Gemini embedding integration, and Groq summary generation.
"""

import sys
import os
import asyncio

# Add backend directory to system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.document_service import (
    extract_text_from_txt,
    chunk_text,
    generate_embeddings_with_retry,
    generate_summary,
)
from app.adapters.gemini_adapter import gemini_adapter
from app.adapters.groq_adapter import groq_adapter


async def run_verification():
    print("=== Verification Phase 2: Document Processing ===")

    # 1. Test Text Extraction (TXT)
    print("\nTesting text extraction from TXT...")
    sample_text = "StudyMate AI is a placement preparation companion. It uses RAG and spaced repetition."
    sample_bytes = sample_text.encode("utf-8")
    
    extracted_pages, page_count = extract_text_from_txt(sample_bytes)
    assert page_count == 1, "Page count for TXT should be 1"
    assert extracted_pages[0] == sample_text, "Extracted text does not match input"
    print("[OK] TXT extraction succeeded.")

    # 2. Test Text Chunking
    print("\nTesting paragraph-aware chunking...")
    # Generate text larger than chunk_size (1500) to verify split
    large_text = " ".join(["Word" for _ in range(500)])  # Approx 2500 characters
    chunks = chunk_text([large_text], chunk_size=1000, overlap=100)
    
    assert len(chunks) > 1, "Should have split text into multiple chunks"
    for idx, chunk in enumerate(chunks):
        assert chunk["page_number"] == 1, "Page number should be 1"
        assert chunk["chunk_index"] == idx, f"Chunk index should be {idx}"
        assert len(chunk["content"]) > 0, "Chunk content should not be empty"
    print(f"[OK] Chunking succeeded. Split large text into {len(chunks)} chunks.")

    # 3. Test Gemini Embeddings Integration
    print("\nTesting Gemini embedding generation (External API call)...")
    test_chunk = {"content": "Machine Learning and Neural Networks.", "page_number": 1, "chunk_index": 0}
    try:
        embeddings = await generate_embeddings_with_retry([test_chunk])
        assert len(embeddings) == 1, "Should return 1 embedding"
        assert len(embeddings[0]) == 768, f"Gemini embedding should be 768-dimensional, got {len(embeddings[0])}"
        print("[OK] Gemini embedding integration succeeded (768 dimensions verified).")
    except Exception as exc:
        print(f"[FAILED] Gemini embedding integration failed: {exc}")
        print("Please check your GEMINI_API_KEY in backend/.env")
        return

    # 4. Test Groq Summarization Integration
    print("\nTesting Groq summary generation (External API call)...")
    test_chunks = [
        {"content": "Deep learning is a subset of machine learning that is based on artificial neural networks with representation learning.", "page_number": 1, "chunk_index": 0},
        {"content": "Gradient descent is an optimization algorithm used to minimize some function by iteratively moving in the direction of steepest descent.", "page_number": 1, "chunk_index": 1}
    ]
    try:
        summary = await generate_summary(test_chunks)
        assert len(summary) > 10, "Summary should be a non-trivial string"
        print(f"[OK] Groq summarization integration succeeded. Summary output:\n--> {summary}")
    except Exception as exc:
        print(f"[FAILED] Groq summarization integration failed: {exc}")
        print("Please check your GROQ_API_KEY in backend/.env")
        return

    print("\n=== ALL PHASE 2 DOCUMENT SERVICE UNIT TESTS PASSED SUCCESSFULLY! ===")


if __name__ == "__main__":
    asyncio.run(run_verification())
