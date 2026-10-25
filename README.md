# FinLens

> **Enterprise-Grade Financial Document RAG Platform**  
> Powered by Hybrid Retrieval (Dense Vector + BM25), Reciprocal Rank Fusion (RRF), Cross-Encoder Reranking, Adversarial Guardrails, Two-Tier Rate Limiting, and Streaming Grounded Generation.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-16.2_(Turbopack)-black.svg?style=flat&logo=next.js&logoColor=white)](https://nextjs.org)
[![React](https://img.shields.io/badge/React-19.2-61DAFB.svg?style=flat&logo=react&logoColor=black)](https://react.dev)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+_(pgvector)-336791.svg?style=flat&logo=postgresql&logoColor=white)](https://github.com/pgvector/pgvector)
[![Prisma](https://img.shields.io/badge/Prisma-7.9-2D3748.svg?style=flat&logo=prisma&logoColor=white)](https://www.prisma.io)
[![Ragas Faithfulness](https://img.shields.io/badge/Ragas%20Faithfulness-1.00_(100%25)-brightgreen.svg?style=flat)](https://github.com/explodinggradients/ragas)
[![Reranker Recall](https://img.shields.io/badge/Reranker%20Hit%20Rate-99.02%25-blue.svg?style=flat)](https://huggingface.co/cross-encoder/ms-marco-MiniLM-L-6-v2)

FinLens is a high-performance Retrieval-Augmented Generation (RAG) platform purpose-built for financial analysis. It enables quantitative analysts, auditors, and investors to ingest complex corporate filings (SEC 10-K, 10-Q, 8-K, annual reports, earnings transcripts, balance sheets) and extract exact, context-grounded insights backed by mathematical formulas, page-level citations, and relevance scores — eliminating hallucinations while neutralizing basic prompt injection attacks.

---

## Table of Contents

- [Key Features](#key-features)
- [System Architecture](#system-architecture)
- [Security & Guardrails](#security--guardrails)
- [Two-Tier Rate Limiting](#two-tier-rate-limiting)
- [Evaluation & Benchmark Results](#evaluation--benchmark-results)
- [Tech Stack](#tech-stack)
- [Directory Structure](#directory-structure)
- [API Reference](#api-reference)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [1. Database Setup](#1-database-setup)
  - [2. Backend Setup](#2-backend-setup)
  - [3. Frontend Setup](#3-frontend-setup)
  - [4. Concurrent Development Mode](#4-concurrent-development-mode)
- [Environment Configuration](#environment-configuration)
- [Testing & Benchmarking Guide](#testing--benchmarking-guide)

---

## Key Features

- **Hybrid Retrieval Engine (Dense + Sparse)**:
  - **Dense Search**: Semantic embeddings using `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions, cosine distance) stored in PostgreSQL with `pgvector`.
  - **Sparse Search**: Lexical exact matching using `rank-bm25` to capture exact financial tickers, line items, footnote references, and numeric metrics (EBITDA, Capex, WACC, non-GAAP reconciliations).
  - **Reciprocal Rank Fusion (RRF)**: Combines dense and sparse results with configurable parameter $k=60$ ($Score = \sum \frac{1}{k + rank}$) to ensure balanced recall across diverse query styles.
- **Cross-Encoder Reranking with Hybrid-Aware Anchor Selection**:
  - Scores candidate chunks using `cross-encoder/ms-marco-MiniLM-L-6-v2`.
  - **Hybrid-Aware Select**: Blends precision picks from the Cross-Encoder with coverage picks from RRF, guaranteeing that neither lexical table metrics nor contextual narrative chunks are dropped.
- **Strictly Grounded Streaming Generation**:
  - Real-time token streaming via FastAPI Server-Sent Events (SSE).
  - Explicit prompt grounding refusing external knowledge: every factual claim is tethered to inline citations `[1]`, `[2]`.
  - Conversational fallback router gracefully handles greetings and directs off-topic queries to document uploads.
  - Background asynchronous persistence of user messages, model responses, and citation metadata with foreign-key links into PostgreSQL.
- **Multi-Layer Defensive Security**:
  - Dual-phase prompt injection detection (regex pattern filters for system overrides, persona hijacking, context escapes, format manipulations).
  - Indirect document injection sanitization (redacts hidden adversarial instructions inside uploaded documents).
  - Query character limits (700 characters max) and session-level IDOR access verification.
- **Two-Tier Distributed Rate Limiting**:
  - **Frontend Limiter**: Sliding-window rate limiter powered by `@upstash/ratelimit` with Redis and automatic in-memory fallback.
  - **Backend Limiter**: SlowAPI with Redis backing (`storage_uri`) and in-memory fallback, tracking authenticated `user:userId` or client IP.
- **Multi-Document Session Isolation**:
  - Create and manage isolated analysis sessions per company, quarter, or portfolio.
  - All searches and chats are strictly partitioned by session and user UUIDs.
- **Modern Dark-Themed Next.js 16 UI**:
  - Built with Next.js 16 (Turbopack), React 19, and Tailwind CSS v4.
  - Interactive citation badges linking back to source document excerpts and page numbers.

---

## System Architecture

```mermaid
graph TD
    subgraph Ingestion_Pipeline ["Ingestion Pipeline"]
        A["User Uploads PDF / DOCX / HTML / TXT"] --> B["Text & Structure Extraction"]
        B --> C["Text Cleaning & Normalization"]
        C --> D["Token-Aware Chunking (tiktoken cl100k_base, 1200 chars / 200 overlap)"]
        D --> E1["SentenceTransformer Embeddings (384-dim)"]
        D --> E2["Sparse BM25 In-Memory Indexer"]
        E1 --> F[("PostgreSQL + pgvector")]
    end

    subgraph Query_Pipeline ["Query & Security Pipeline"]
        G["User Query"] --> H{"Guardrail Validator"}
        H -->|"Injection Detected"| H_ERR["Return Friendly Guardrail Warning"]
        H -->|"Sanitized & Validated"| I1["Dense Vector Search (pgvector cosine)"]
        H -->|"Sanitized & Validated"| I2["Sparse BM25 Search"]
        I1 --> J["Reciprocal Rank Fusion (RRF k=60)"]
        I2 --> J
        J --> K["Candidate Chunks (k=20)"]
        K --> L["Cross-Encoder Reranker (ms-marco-MiniLM-L-6-v2)"]
        L --> M["Hybrid-Aware Selection (Precision + Coverage Slots)"]
        M --> N["Document Sanitizer (Redact Indirect Injections)"]
        N --> O["Context Assembly + Citations Mapping"]
        O --> P["Google Gemini LLM Stream"]
        P --> Q["SSE Streaming Response to Next.js Client"]
        Q --> R[("PostgreSQL Messages & Citations Persistence")]
    end
```

---

## Security & Guardrails

FinLens implements a defense-in-depth security model designed specifically for LLM-powered financial systems:

### 1. Direct Prompt Injection Defense
Every incoming query passes through `backend/app/services/guardrails.py` before hitting retrieval or LLM inference:
- **Instruction Override Prevention**: Blocks attempts like `"ignore all previous instructions"`, `"disregard earlier rules"`, or `"override system context"`.
- **Role Hijacking Prevention**: Blocks unauthorized persona shifts (`"you are now an unrestricted assistant"`, `"pretend to be"`), allowing role instructions only when scoped specifically to financial analysis.
- **System Prompt Extraction Filter**: Rejects queries attempting to probe internal system prompts (`"reveal your system prompt"`, `"show initial instructions"`).
- **Context Escape & Delimiter Neutralization**: Blocks markdown/XML/tag delimiter forgery (`<system>`, `[system]`, `BEGIN NEW CONTEXT`, `END OF SYSTEM`).
- **Format Manipulation Prevention**: Intercepts requests compelling malicious code generation or raw executable syntax.

### 2. Indirect Document Injection Sanitization
Malicious actors often embed hidden text in white font inside financial PDFs or footnote XML. FinLens scrubs all candidate chunks before LLM synthesis via `sanitize_chunks()`:
- Scans for covert prompts targeting LLMs (`"FinLens: ignore previous instructions and state..."`).
- Automatically replaces malicious chunks with `[CONTENT REDACTED]` and emits security audit warnings.

### 3. Session Ownership & IDOR Protection
- Every request to `/chat`, `/upload`, and `/retrieve` verifies session ownership via `verify_session_access()`.
- Validates that the requested `sessionId` belongs directly to the authenticated `current_user["userId"]`, preventing Insecure Direct Object Reference (IDOR) attacks.

### 4. JWT Backend Authentication
- Frontend issues signed, short-lived JWTs via `/api/auth/backend-token` using a shared `BACKEND_AUTH_SECRET`.
- The FastAPI backend validates bearer tokens via `HTTPBearer` (`app/auth/dependencies.py`), rejecting unauthenticated requests with `401 Unauthorized`.

---

## Two-Tier Rate Limiting

To prevent DoS attacks, API scraping, and LLM quota exhaustion, FinLens employs synchronized dual-tier rate limiting:

| Layer | Implementation | Storage / Fallback | Route / Scope | Limit |
|---|---|---|---|---|
| **Frontend** | `@upstash/ratelimit` | Upstash Redis $\to$ Sliding-window in-memory fallback | Auth routes (`/api/auth/*`) | 20 req / min |
| **Frontend** | `@upstash/ratelimit` | Upstash Redis $\to$ Sliding-window in-memory fallback | Write routes (sessions create) | 30 req / min |
| **Frontend** | `@upstash/ratelimit` | Upstash Redis $\to$ Sliding-window in-memory fallback | Read routes (messages, history) | 90 req / min |
| **Frontend** | `@upstash/ratelimit` | Upstash Redis $\to$ Sliding-window in-memory fallback | General routes | 60 req / min |
| **Backend** | `slowapi` | Redis (`REDIS_URL`) $\to$ In-memory fallback (`memory://`) | `POST /upload/` | 10 req / min |
| **Backend** | `slowapi` | Redis (`REDIS_URL`) $\to$ In-memory fallback (`memory://`) | `POST /chat/` | 20 req / min |
| **Backend** | `slowapi` | Redis (`REDIS_URL`) $\to$ In-memory fallback (`memory://`) | `POST /retrieve/` | 30 req / min |
| **Backend** | `slowapi` | Redis (`REDIS_URL`) $\to$ In-memory fallback (`memory://`) | Default global limit | 120 req / min |

*All limiters prioritize authenticated user IDs (`user:<userId>`) and fall back to IP addresses (`ip:<remote_addr>`).*

---

## Evaluation & Benchmark Results

FinLens has been rigorously benchmarked using custom multi-document financial datasets, empirical latency profiling, and the **Ragas** evaluation framework.

### 1. Retrieval Engine Benchmark (Single-Chunk Queries)

Evaluated against financial ground-truth queries extracted from SEC filings:

| Retrieval Method | Hit Rate @ Top-K | Recall @ Top-K | Mean Reciprocal Rank (MRR) |
|---|:---:|:---:|:---:|
| **Dense Vector (pgvector)** | 88.24% | 0.8824 | 0.7371 |
| **Sparse Keyword (BM25)** | 94.12% | 0.9412 | 0.8034 |
| **Hybrid (Dense + BM25 RRF)** | 94.12% | 0.9412 | 0.7985 |
| **Reranker (Cross-Encoder + Hybrid Selection)** | **99.02%** | **0.9902** | **0.8644** |

### 2. Multi-Chunk Synthesis Benchmark

Complex queries spanning multiple financial pages and multi-table disclosures:

| Retrieval Method | Partial Hit Rate | Complete Hit Rate | Recall | MRR |
|---|:---:|:---:|:---:|:---:|
| **Dense Vector** | 95.45% | 31.82% | 0.6591 | 0.6735 |
| **Sparse BM25** | 100.0% | 45.45% | 0.7424 | 0.8258 |
| **Hybrid RRF** | 95.45% | 50.00% | 0.7121 | 0.8636 |
| **Cross-Encoder Reranker** | **100.0%** | **45.45%** | **0.7197** | **0.9242** |

### 3. Ragas Generation Quality Benchmark

| Metric | Score | Target | Interpretation |
|---|:---:|:---:|---|
| **Faithfulness** | **1.000** (100%) | > 0.85 | Zero hallucinations detected. 100% of generated claims are derived from context chunks. |
| **Context Recall** | **0.912** (91.2%) | > 0.80 | Model captures > 91% of reference financial ground truth in its generated synthesis. |

### 4. Latency Benchmark Breakdown

Benchmarked across cold starts and warm query states (`backend/benchmark_latency.py`):

| Pipeline Stage | Cold Mean | Warm Mean | Cold P95 | Warm P95 |
|---|:---:|:---:|:---:|:---:|
| **Guardrail Validation** | 0.2 ms | < 0.1 ms | 0.1 ms | < 0.1 ms |
| **Hybrid Retrieval (Dense + BM25 + RRF)** | 1,745.5 ms | **23.0 ms** | 83.4 ms | 25.0 ms |
| **Cross-Encoder Reranking** | 1,653.4 ms | **360.2 ms** | 384.2 ms | 368.6 ms |
| **Prompt Assembly** | 0.1 ms | < 0.1 ms | 0.1 ms | 0.1 ms |
| **Time to First Token (TTFT)** | 3,296.2 ms | **1,636.6 ms** | 2,124.2 ms | 1,806.6 ms |
| **Total Query Latency (Server)** | 7,718.3 ms | **3,125.4 ms** | 3,514.2 ms | 3,114.0 ms |

---

## Tech Stack

### **Backend & AI Engine**
- **Runtime & Web Framework**: Python 3.10+, FastAPI, Uvicorn, AsyncPG, Psycopg3
- **Vector Database**: PostgreSQL 15+ with `pgvector` (cosine distance, HNSW / IVFFlat compatible)
- **Database Tooling & ORM**: Prisma ORM (dual-client generation for Python and Next.js)
- **Dense Embeddings**: `sentence-transformers` (`all-MiniLM-L6-v2`, 384-dim)
- **Sparse Retrieval**: `rank-bm25`
- **Reranker**: `cross-encoder/ms-marco-MiniLM-L-6-v2`
- **Document Extractors**: PyMuPDF (`fitz`), `python-docx`, BeautifulSoup4 (HTML parsing), `pypdf`
- **Text Chunking**: `langchain-text-splitters` (`RecursiveCharacterTextSplitter`), `tiktoken` (`cl100k_base`)
- **LLM Synthesis**: Google GenAI SDK (`google-genai`), `gemini-3.5-flash-lite` / `gemma-4-31b-it`
- **Rate Limiting**: `slowapi`, `redis`
- **Evaluation**: `ragas==0.4.3`, `datasets`, `pytest`, `pytest-asyncio`

### **Frontend & UI**
- **Framework**: Next.js 16.2 (App Router, Turbopack for local development)
- **Core Library**: React 19.2
- **Styling**: Tailwind CSS v4, custom glassmorphism design tokens
- **Authentication**: NextAuth.js v5 (`beta.32`) with Google OAuth and Resend Magic Links
- **Rate Limiting**: `@upstash/ratelimit`, `@upstash/redis`

---

## Directory Structure

```text
finance_rag/
├── package.json                 # Root monorepo orchestration (concurrent dev launcher)
├── SECURITY_AUDIT.md            # Comprehensive security audit report & verification log
├── README.md                    # Project documentation
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── chat.py          # POST /chat/ (SSE streaming + citation DB persistence)
│   │   │   ├── retrive.py       # POST /retrieve/ (hybrid search & reranking inspector)
│   │   │   ├── upload.py        # POST /upload/ (multipart doc parser, chunker, vector storer)
│   │   │   └── benchmark.py     # Latency benchmark route (disabled in prod for security)
│   │   ├── auth/
│   │   │   └── dependencies.py  # JWT authentication & session IDOR verification
│   │   ├── db/
│   │   │   └── database.py      # AsyncPG connection pool & lifecycle management
│   │   ├── evaluation/
│   │   │   ├── dataset/         # Single-chunk & multi-chunk gold test datasets
│   │   │   ├── results/         # Saved JSON benchmark runs (Ragas, MRR, Hit-rates)
│   │   │   ├── evaluate_retrival.py
│   │   │   ├── evaluate_multi_chunk_retrieval.py
│   │   │   └── ragas_evaluation.py
│   │   ├── schemas/
│   │   │   └── utils.py         # Pydantic models (ChatRequest, RetrievalResponse, etc.)
│   │   ├── services/
│   │   │   ├── bm25.py          # In-memory sparse BM25 indexer
│   │   │   ├── chunking.py      # Token-aware recursive chunker
│   │   │   ├── cleaner.py       # Text normalization & whitespace sanitizer
│   │   │   ├── embedding.py     # SentenceTransformer embedding generator
│   │   │   ├── extractor.py     # Multi-format doc extractor (PDF, DOCX, HTML, TXT)
│   │   │   ├── generator.py     # Context builder, prompt templating, Gemini stream
│   │   │   ├── guardrails.py    # Direct & indirect prompt injection defense
│   │   │   ├── hybird_retrival.py # Reciprocal Rank Fusion (RRF) logic
│   │   │   ├── reranker.py      # Cross-encoder & hybrid-aware anchor selection
│   │   │   ├── retriever.py     # Dense vector similarity retriever (pgvector)
│   │   │   └── vector_store.py  # Asynchronous PostgreSQL chunk & vector ingestion
│   │   ├── main.py              # FastAPI app definition, CORS, lifespan, SlowAPI limiter
│   │   └── rate_limiter.py      # SlowAPI limiter instance & key extraction logic
│   ├── prisma/
│   │   └── schema.prisma        # Database schema (User, Session, Document, Chunk, Citation)
│   ├── tests/                   # Pytest test suite (hybrid retrieval, reranker, chunker)
│   ├── benchmark_latency.py     # CLI latency benchmarking tool
│   ├── latency_report.md        # Generated latency benchmark report
│   ├── requirements.txt         # Backend Python dependencies
│   └── package.json             # Backend Prisma npm scripts
│
├── frontend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── auth/
│   │   │   │   ├── [...nextauth]/route.js   # NextAuth OAuth & email handlers
│   │   │   │   └── backend-token/route.js   # JWT minting endpoint for backend API
│   │   │   ├── chunks/[id]/route.js         # Chunk inspection endpoint
│   │   │   └── sessions/                    # Analytical session CRUD & message history
│   │   ├── auth/                            # Sign-in & verification pages
│   │   ├── chat/                            # Main interactive workspace & document viewer
│   │   ├── components/                      # UI components (ShapeGrid, Sidebar, MessageView)
│   │   ├── globals.css                      # Tailwind CSS v4 styling rules
│   │   └── layout.js                        # Root application layout
│   ├── lib/
│   │   ├── backendToken.js      # Client-side cached JWT token manager
│   │   ├── prisma.js            # Prisma client instance for Next.js
│   │   └── rateLimit.js         # Upstash Redis + in-memory sliding-window limiter
│   ├── auth.config.js           # NextAuth configuration
│   ├── middleware.js            # Route protection middleware
│   └── package.json             # Frontend npm dependencies
│
└── data/                        # Sample financial filings & evaluation documents
```


---

## API Reference

### Backend Endpoints (`http://localhost:8000`)

| Method | Endpoint | Auth | Rate Limit | Description |
|---|---|:---:|:---:|---|
| `GET` | `/` | No | 120/min | Healthcheck returning service status |
| `POST` | `/upload/` | Bearer JWT | 10/min | Upload document (`.pdf`, `.docx`, `.html`, `.txt`, max 25MB). Extracts, chunks, embeds, and stores in DB. |
| `POST` | `/retrieve/` | Bearer JWT | 30/min | Perform hybrid search + reranking on a session without triggering LLM generation. |
| `POST` | `/chat/` | Bearer JWT | 20/min | Query documents with real-time SSE token streaming, citation generation, and auto-persistence. |

#### `POST /chat/` Request Body
```json
{
  "query": "What was the operating margin in Q3 and what were the main drivers?",
  "session_id": "06738e01-cb08-4727-8810-56413ed41755",
  "top_k": 6,
  "candidate_k": 20
}
```

#### `POST /chat/` SSE Stream Events
- `{"type": "token", "content": "The"}`
- `{"type": "token", "content": " operating margin was..."}`
- `{"type": "sources", "sources": [{"citation_id": 1, "document_filename": "10-Q_Q3.pdf", "page_number": 14, "relevance_score": 0.892, "content_preview": "..."}]}`

---

### Frontend API Routes (`http://localhost:3000`)

| Method | Endpoint | Auth | Rate Limit | Description |
|---|---|:---:|:---:|---|
| `GET` | `/api/auth/backend-token` | Session | 20/min | Issues signed JWT for frontend client to authorize requests to FastAPI backend. |
| `GET/POST` | `/api/sessions` | Session | 90/min (R) / 30/min (W) | List user sessions or create a new analytical session. |
| `GET/DELETE`| `/api/sessions/[id]` | Session | 90/min (R) / 30/min (W) | Fetch session details or delete session (cascades all docs & messages). |
| `GET` | `/api/sessions/[id]/messages` | Session | 90/min | Fetch past message history and citations for a session. |
| `GET` | `/api/chunks/[id]` | Session | 90/min | Fetch chunk content and metadata for citation modals. |

---

## Getting Started

### Prerequisites

Ensure you have the following installed:
- **Node.js**: v18.x or v20.x+
- **Python**: v3.10 or v3.11+
- **PostgreSQL**: v15+ with the `pgvector` extension
- *(Optional)* **Redis**: For distributed rate limiting (fallback to memory mode if omitted)

---

### 1. Database Setup

1. Connect to PostgreSQL and enable `pgvector`:
   ```sql
   CREATE DATABASE financerag;
   \c financerag
   CREATE EXTENSION IF NOT EXISTS vector;
   ```
2. Verify that `vector` extension is active:
   ```sql
   SELECT * FROM pg_extension WHERE extname = 'vector';
   ```

---

### 2. Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a Python virtual environment:
   ```bash
   # Windows (PowerShell)
   python -m venv venv
   .\venv\Scripts\Activate.ps1

   # Linux / macOS
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Install Prisma CLI dependencies and generate dual clients:
   ```bash
   npm install
   npx prisma generate
   ```
5. Apply database schema migrations:
   ```bash
   npx prisma db push
   ```
6. Start the FastAPI development server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

---

### 3. Frontend Setup

1. Open a new terminal and navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install npm dependencies:
   ```bash
   npm install
   ```
3. Generate the frontend Prisma client:
   ```bash
   npx prisma generate --schema=../backend/prisma/schema.prisma
   ```
4. Start the Next.js development server with Turbopack:
   ```bash
   npm run dev
   ```
   > **Note**: Turbopack is enabled for development mode (`next dev --turbo`) for instant hot reload. For production builds, run `npm run build` and `npm start`.

5. Open [http://localhost:3000](http://localhost:3000) in your browser.

---

### 4. Concurrent Development Mode

You can also run both frontend and backend concurrently from the root directory:

```bash
npm install
npm start
```

---

## Environment Configuration

### Backend Environment Variables (`backend/.env`)

```env
# Database Connection (PostgreSQL + pgvector)
DATABASE_URL="postgresql://postgres:password@localhost:5432/financerag"

# Google Gemini API Key & Model
GEMINI_API_KEY="your-google-ai-studio-api-key"
GEMINI_MODEL="gemini-3.5-flash-lite"
LLM_PROVIDER="gemini"

# Shared JWT Secret for Backend Authentication (Must match frontend)
BACKEND_AUTH_SECRET="your-generated-32-byte-hex-secret"

# Frontend Origin for CORS
FRONTEND_URL="http://localhost:3000"

# (Optional) Redis for Distributed Rate Limiting (Default: memory://)
REDIS_URL="redis://localhost:6379"

# Evaluation IDs (Used by benchmark scripts)
EVAL_SESSION_ID="test-id"
EVAL_DOCUMENT_ID="test-id"
```

### Frontend Environment Variables (`frontend/.env.local`)

```env
# NextAuth Configuration
AUTH_SECRET="your-nextauth-secret"
AUTH_TRUST_HOST=true
NEXTAUTH_URL="http://localhost:3000"

# Google OAuth Provider (https://console.cloud.google.com/apis/credentials)
GOOGLE_CLIENT_ID="your-google-oauth-client-id"
GOOGLE_CLIENT_SECRET="your-google-oauth-client-secret"

# Resend Magic Links (https://resend.com)
AUTH_RESEND_KEY="re_your_api_key"
AUTH_EMAIL_FROM="onboarding@resend.dev"

# Database Connection (Same PostgreSQL instance)
DATABASE_URL="postgresql://postgres:password@localhost:5432/financerag"

# Shared JWT Secret (Must match backend BACKEND_AUTH_SECRET)
BACKEND_AUTH_SECRET="your-generated-32-byte-hex-secret"

# FastAPI Backend URL
BACKEND_URL="http://localhost:8000"

# (Optional) Upstash Redis for Edge Rate Limiting (Default: in-memory)
UPSTASH_REDIS_REST_URL="https://your-upstash-redis.upstash.io"
UPSTASH_REDIS_REST_TOKEN="your-upstash-token"
```

> **Tip for generating secrets**: Run `openssl rand -hex 32` or `node -e "console.log(crypto.randomBytes(32).toString('hex'))"` to generate secure secrets for `AUTH_SECRET` and `BACKEND_AUTH_SECRET`.

---

## Testing & Benchmarking Guide

### 1. Run Unit & Service Tests

Run the full pytest suite for chunking, text extraction, BM25, and hybrid reranking:

```bash
cd backend
pytest -v
```

### 2. Run Retrieval Evaluation

Benchmark Hit Rate, Recall, and MRR for Dense vs. BM25 vs. Hybrid vs. Cross-Encoder:

```bash
cd backend
python -m app.evaluation.evaluate_retrival
python -m app.evaluation.evaluate_multi_chunk_retrieval
```

### 3. Run Ragas Groundedness & Faithfulness Evaluation

Evaluate model generation faithfulness and context recall against the golden evaluation dataset:

```bash
cd backend
python -m app.evaluation.ragas_evaluation
```

### 4. Run Latency Profiling

Benchmark end-to-end latency across cold and warm runs with detailed millisecond breakdowns:

```bash
cd backend
python benchmark_latency.py --session-id <YOUR_SESSION_UUID> --query "What were the total revenues reported?" --cold-runs 5 --warm-runs 5
```

