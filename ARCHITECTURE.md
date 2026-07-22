# StudyMate AI — Architecture Reference

*This document exists so you can defend every technology choice in your viva and in job interviews.*

---

## 1. System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT (Browser)                          │
│          Next.js 14 App Router — hosted on Vercel               │
│   SSR public pages (SEO) + CSR authenticated app (dashboard)    │
└─────────────────────┬───────────────────────────────────────────┘
                      │ HTTPS REST (JSON)
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│              BACKEND API — FastAPI (Python)                      │
│                   hosted on Render free tier                     │
│                                                                  │
│  ┌──────────┐  ┌───────────┐  ┌─────────────┐  ┌───────────┐  │
│  │  Auth    │  │ Documents │  │  Chat (RAG) │  │ Concepts  │  │
│  │  Router  │  │  Router   │  │   Router    │  │  Router   │  │
│  └──────────┘  └───────────┘  └─────────────┘  └───────────┘  │
│            │           │              │                │         │
│       ┌────▼───────────▼──────────────▼────────────────▼────┐   │
│       │              Services Layer                          │   │
│       │  auth_service  document_service  chat_service  ...  │   │
│       └────────────────────────┬──────────────────────────┘   │
│                                │                                 │
│            ┌───────────────────┼───────────────────┐            │
│            ▼                   ▼                   ▼            │
│     ┌─────────────┐   ┌──────────────┐   ┌──────────────────┐  │
│     │ Groq Adapter│   │Gemini Adapter│   │ Storage Adapter  │  │
│     │  (text gen) │   │(embeddings)  │   │(Supabase Storage)│  │
│     └──────┬──────┘   └──────┬───────┘   └──────────────────┘  │
└────────────│─────────────────│────────────────────────────────┘
             │                 │
             ▼                 ▼
     ┌──────────────┐  ┌─────────────────────────────────────────┐
     │   Groq API   │  │         Supabase (PostgreSQL)           │
     │ llama-3.3-   │  │  ┌──────────────┐  ┌────────────────┐  │
     │ 70b-versatile│  │  │  Core Tables │  │ document_chunks│  │
     └──────────────┘  │  │  users       │  │ VECTOR(768)    │  │
                        │  │  documents   │  │ pgvector HNSW  │  │
     ┌──────────────┐  │  │  flashcards  │  │ cosine index   │  │
     │  Gemini API  │  │  │  quiz_...    │  └────────────────┘  │
     │ gemini-      │  │  │  chat_...    │                       │
     │ embedding-001│  │  │  concepts    │                       │
     └──────────────┘  │  └──────────────┘                       │
                        └─────────────────────────────────────────┘
```

---

## 2. Technology Choices — The Full Explanation

### 2.1 Why FastAPI (not Flask or Django)?

FastAPI is the right choice here for three concrete reasons:

1. **Async-native:** FastAPI is built on Starlette and supports Python's `async/await` throughout. Because every AI call in this app is an outbound HTTPS request (to Groq, Gemini, Supabase Storage), the backend spends almost all its time waiting for I/O — not computing. Async lets a single-threaded process handle tens of concurrent requests during that wait time, which matters a lot on a 0.1-CPU free instance.

2. **Pydantic is built in:** every request body and response is automatically validated and serialised via Pydantic schemas. No manual `request.get_json()` + manual validation like Flask.

3. **Tiny runtime footprint:** a bare FastAPI app with our requirements.txt consumes ~60–80 MB RSS at startup. Render's free tier gives you 512 MB — that leaves over 400 MB of headroom for request processing and the scikit-learn model loaded in Phase 6.

### 2.2 Why Groq for text generation?

Groq provides a free API to inference open-weight LLMs (Llama, Mistral, etc.) on custom LPU (Language Processing Unit) hardware. Key properties relevant to this project:

- **Speed:** Groq's LPU generates tokens 5–10× faster than GPU-based APIs for the same model size. This matters for the RAG chatbot UX — slow responses feel like broken software.
- **Free tier that isn't token-metered:** Groq's free tier is rate-limited by requests-per-minute and requests-per-day, not by tokens consumed. A single day's free quota is more than sufficient for a development and demo workload.
- **`llama-3.3-70b-versatile`:** a 70B parameter Llama 3.3 model that matches GPT-4-class instruction-following quality at zero API cost. It reliably returns structured JSON (crucial for quiz/flashcard generation).
- **Fallback to `llama-3.1-8b-instant`:** if the primary model hits a per-minute rate limit, the adapter automatically retries with this smaller, faster, higher-quota model.

The adapter implements the same `BaseLLMAdapter` abstract interface as the Gemini adapter, so swapping providers is a one-line change in `config.py`.

### 2.3 Why Gemini for embeddings (and why not Groq)?

**Groq does not offer an embeddings endpoint** — it is a pure text-generation API. An embedding is a fixed-size vector representation of a text fragment, used to measure semantic similarity (the core of RAG retrieval). This is a fundamentally different ML operation from auto-regressive text generation, and Groq does not expose it.

**`gemini-embedding-001`** (Google Gemini) is the current recommended embedding model on the Gemini platform. We call it with `output_dimensionality=768` to match the `VECTOR(768)` column in pgvector. This is not `models/text-embedding-004` (deprecated) — `gemini-embedding-001` is the replacement and is what the Gemini documentation currently recommends.

The call is a simple HTTPS POST, so it adds no library weight beyond `httpx`.

### 2.4 Why PostgreSQL + pgvector (not a separate vector DB)?

A dedicated vector database (Pinecone, Weaviate, Qdrant) would be another service to manage, another free-tier limit to watch, and another moving part to explain. Supabase's PostgreSQL includes the `pgvector` extension, which stores embedding vectors directly in a normal Postgres column and supports similarity search via SQL operators.

For our scale (hundreds of chunks per student on a free account), pgvector with an **HNSW (Hierarchical Navigable Small World)** index provides sub-millisecond approximate nearest-neighbour queries — fast enough that users don't notice it.

The HNSW index is created with:
```sql
CREATE INDEX ON document_chunks USING hnsw (embedding vector_cosine_ops);
```

`vector_cosine_ops` means similarity is measured by cosine distance, which is the standard for comparing embedding vectors (it's direction-invariant, so magnitude differences from normalisation don't affect ranking).

### 2.5 Why Supabase (not Neon + separate storage)?

Supabase gives us four things in one free project:
1. **PostgreSQL** with the `vector` extension pre-available
2. **A SQL editor** in the web dashboard (useful for debugging the schema)
3. **Row-Level Security** (not used in this project since we do auth ourselves, but worth knowing)
4. **Storage** (S3-compatible object storage for uploaded PDFs)

Neon would give us a slightly better Postgres free tier (no 30-day auto-pause for inactive projects), but we'd need a separate file storage service (Cloudinary free tier, for example). One service is simpler.

### 2.6 Why JWT auth (not Supabase Auth / Clerk / Auth0)?

This is explicitly a **learning project** whose goal is understanding how auth works end-to-end. Building JWT auth from scratch forces you to understand:
- What a JWT is (a base64-encoded JSON payload + a signature)
- Why bcrypt for password hashing (salted, adaptive cost factor — more rounds = slower brute force)
- What the access-token pattern is (stateless, the server holds no session)
- How `Authorization: Bearer <token>` headers work

The implementation is a single file (`services/auth_service.py`) using `python-jose` (JWT encode/decode) and `passlib[bcrypt]` (password hashing). In an interview, you can explain every line.

### 2.7 Why Next.js 14 (App Router)?

1. **Server-Side Rendering:** the public landing page and blog posts are rendered on the server, so search engines get fully-formed HTML with text content. A plain Vite/React SPA gives search engines a blank `<div id="root"></div>` — real SEO is impossible.
2. **Metadata API:** Next.js 14's `metadata` export (per-page `title`, `description`, Open Graph, Twitter card) is the cleanest way to implement SEO without a separate Helmet-style library.
3. **Route Groups:** `(auth)` and `(app)` group pages under different layouts without affecting URLs.
4. **Deployable on Vercel for free:** Vercel is the company that created Next.js; the free tier supports personal projects permanently.
5. **Industry standard:** Next.js is the most in-demand React framework in 2024–2025 job postings for full-stack roles.

### 2.8 Why scikit-learn for Phase 6 (not PyTorch / TensorFlow)?

The retention prediction model in Phase 6 is a tabular regression problem with 6 engineered features. For tabular regression, `GradientBoostingRegressor` from scikit-learn routinely outperforms neural networks, requires no GPU, and trains in seconds on a laptop.

**RAM budget arithmetic:**
- scikit-learn installed: ~50 MB disk
- scikit-learn at runtime (imported): ~15–20 MB RSS
- Trained GradientBoostingRegressor serialised with joblib: ~1–3 MB file, ~5 MB RSS when loaded
- Total overhead added to the FastAPI process: ~25 MB

This comfortably fits within the 512 MB Render limit.

PyTorch would add ~800 MB of disk and ~200 MB of runtime RSS — 4× over the limit before a single request is served.

---

## 3. Phase 6: Self-Trained Retention Model

### 3.1 Why a self-trained model?

The SM-2 spaced-repetition algorithm (used in Phase 2 as the baseline scheduler) is a hand-crafted heuristic from 1987 with fixed interval multipliers. It does not adapt to individual students or card difficulty. A machine-learning model that predicts *"what is the probability this student still remembers this flashcard today?"* is both more accurate and a genuine ML contribution — it answers the evaluator question *"where's the AI/ML you built yourself?"*

### 3.2 Why synthetic training data?

At project submission time, no real longitudinal user-review data exists — the app is new. This is the **cold-start problem**, standard in ML engineering.

The solution is to generate synthetic data grounded in published memory-science literature:

**Ebbinghaus Forgetting Curve:** `R = e^(-t/S)` where:
- `R` = retention (probability of recall, 0–1)
- `t` = time elapsed since last review (days)
- `S` = memory strength (a function of review history and item difficulty)

By sampling plausible review histories across thousands of simulated students, we can generate (features → label) pairs where the label is the probability of recall on a given day. The model learns from this distribution.

This approach is documented in the training notebook with markdown cells explaining the forgetting-curve parameters — this is what you show in your viva as evidence of literature grounding.

### 3.3 Features used

| Feature | Description |
|---|---|
| `review_count` | Total number of times this card has been reviewed |
| `correct_count` | Number of correct recalls |
| `incorrect_count` | Number of incorrect recalls |
| `avg_response_time_s` | Average seconds taken to answer |
| `days_since_last_review` | Days elapsed since the most recent review |
| `question_difficulty` | Estimated difficulty (0.0–1.0), from SM-2 easiness factor |

### 3.4 Evaluation metrics

The notebook prints Mean Absolute Error (MAE) and Root Mean Squared Error (RMSE) on a held-out test split. These metrics measure, in probability units, how wrong the model's predictions are on average. A well-trained model on synthetic data typically achieves MAE < 0.08 — meaning predictions are within 8 percentage points of the true retention probability.

In the viva, be ready to explain: *"Our MAE of X means the model is on average X probability-units wrong. In practice, this is sufficient precision for scheduling — a card predicted at 0.6 retention will be reviewed before a card at 0.9."*

### 3.5 Retraining pipeline (production path)

As real users review cards, the `flashcards` table accumulates ground-truth review outcomes. A production retraining pipeline would:
1. Query all past review events with their features at review time and the actual recall outcome
2. Combine with the synthetic bootstrap data (or phase it out once real data is sufficient)
3. Retrain the GradientBoostingRegressor and re-export the joblib file
4. Re-deploy the FastAPI service so the new model is loaded at startup

This is described in the training notebook's final cell.

---

## 4. Render + Vercel Free Tier Constraints and How We Designed Around Them

| Constraint | Impact | Design decision |
|---|---|---|
| Render: 512 MB RAM | No heavy ML libs | All LLM/embedding calls via HTTPS to external APIs; scikit-learn is the only local ML lib, kept to ~25 MB overhead |
| Render: 0.1 CPU | No CPU-intensive workloads | PDF parsing is fast (pypdf); chunking is string ops; all heavy work is delegated to APIs |
| Render: cold start ~30–60 s after 15 min inactivity | Bad demo experience | Documented in README; resolved by hitting the URL 60 s before demo |
| Render: Postgres free tier deletes after 30 days | Persistent data loss | DB hosted on Supabase (no expiry), not on Render |
| Groq: rate-limited per minute/day | Occasional 429 errors | Adapter retries with fallback model (`llama-3.1-8b-instant`); all errors returned as user-facing messages, never server crashes |
| Gemini embeddings: free quota | Occasional 429 errors | Caught and returned as user-facing error; embedding step is only triggered on document upload (not per chat message) |
| Vercel: free tier, no custom server | SSR only through Next.js | App Router handles SSR/SSG natively; no Express/custom server needed |

---

## 5. Phase 7: Resume vs Job-Description Skill-Gap Analyzer

### 5.1 Overview & Architecture
Phase 7 adds an intelligent career and placement skill-gap analysis pipeline. The user inputs their current resume text alongside a target job description. The FastAPI backend calls Groq LLM (`llama-3.3-70b-versatile`) with a structured extraction prompt to compute:
1. **Matched Skills**: Overlapping competencies present in both the resume and target job.
2. **Missing Skills / Gaps**: Critical technical skills requested by the employer but absent or weak on the candidate's resume.
3. **Actionable Learning Roadmap**: A 4-6 step personalized study and project plan to bridge the gap.

### 5.2 Defensive Parsing & Fallback
To ensure high availability and zero application crashes:
- The Groq response is parsed for strict JSON.
- If JSON parsing fails or rate limits occur, a fallback keyword-matching algorithm runs locally in `resume_service.py` to extract skill overlap against standard computer science topic dictionaries.
- Frontend rendering handles error visibility cleanly using standard card/tag UI components matching the app design system.

