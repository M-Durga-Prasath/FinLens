# FinLens

> **Advanced Financial Document RAG System** featuring Hybrid Retrieval, Cross-Encoder Reranking, and Context-Aware Grounded Generation.

FinLens is a high-performance Retrieval-Augmented Generation (RAG) platform purpose-built for financial analysis. It enables users to upload complex financial documents (10-K, 10-Q SEC filings, annual reports, balance sheets, analyst notes) and extract precise, context-aware answers backed by exact page-level citations and relevance scoring.

---

## Key Features

- **Hybrid Retrieval Engine**: Combines **Dense Vector Similarity Search** (using `SentenceTransformers` and `pgvector`) with **Sparse Keyword Search** (`BM25`). This guarantees retrieval of both contextual semantic meaning and exact financial terminology (ratios, ticker symbols, line items like EBITDA, Capex, WACC).
- **Cross-Encoder Reranking**: Utilizes cross-encoder reranking to re-evaluate and score candidate chunks, maximizing precision and filtering out noise before feeding context to the LLM.
- **Context-Aware & Grounded Generation**: Generates structured, precise responses strictly grounded in the parsed documents, eliminating financial hallucinations and providing direct document citations.
- **Robust Financial Document Pipeline**:
  - Multi-format document ingestion (PDF, DOCX, etc.).
  - Text extraction, noise reduction, and structural preservation.
  - Smart token-aware chunking optimized for financial table and paragraph structures.
- **Multi-Document Session Management**: Maintain conversational context across multiple uploaded documents within separate analytical sessions.
- **Modern Dark-Themed UI**: Built with Next.js 15 App Router, React, and smooth glassmorphism design for an exceptional user experience.

---

## System Architecture

```mermaid
graph TD
    subgraph Ingestion Pipeline
        A[User Uploads PDF / DOCX] --> B[Text & Table Extraction]
        B --> C[Text Cleaning & Normalization]
        C --> D[Token-Aware Chunking]
        D --> E1[Dense Embedding Generator]
        D --> E2[Sparse BM25 Indexer]
        E1 --> F[(PostgreSQL + pgvector)]
    end

    subgraph Query & RAG Pipeline
        G[User Query] --> H1[Dense Vector Search]
        G --> H2[Sparse BM25 Search]
        H1 --> I[Candidate Chunk Fusion]
        H2 --> I
        I --> J[Cross-Encoder Reranker]
        J --> K[Top-K Relevant Chunks]
        K --> L[Context-Aware LLM Response Generator]
        L --> M[Answer with Page-Level Citations]
    end
```

---

## Tech Stack

### **Backend & RAG Pipeline**
- **Framework**: Python 3.10+, FastAPI, Uvicorn
- **Embeddings**: `SentenceTransformers` (`all-MiniLM-L6-v2`, 384-dim)
- **Sparse Search**: `rank-bm25`
- **Reranking**: Transformer-based Cross-Encoder
- **PDF & Document Processing**: PyMuPDF (`fitz`), `python-docx`, BeautifulSoup4
- **Chunking**: `langchain-text-splitters`, `tiktoken`
- **LLM Integrations**: Groq, OpenAI, Google Gemini (any one model)
- **Database & ORM**: PostgreSQL with `pgvector` extension, Prisma ORM (`prisma-client-py` / `asyncpg`)

### **Frontend**
- **Framework**: Next.js 15 (App Router), React 19
- **Styling**: Vanilla CSS / Tailwind CSS, Custom Glassmorphism UI
- **Authentication**: NextAuth.js
- **Icons**: Custom SVG icons

---

## Directory Structure

```text
finance_rag/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI route handlers (upload, query, sessions)
│   │   ├── schemas/      # Pydantic data schemas
│   │   ├── services/     # Core RAG services (extraction, chunking, embedding, retrieval, reranking)
│   │   └── main.py       # FastAPI application entrypoint
│   ├── prisma/
│   │   └── schema.prisma # Prisma database schema (User, Session, Document, Chunk, Citation)
│   └── requirements.txt  # Python backend dependencies
├── frontend/
│   ├── app/              # Next.js App Router pages (Home, Chat, API routes)
│   ├── app/components/   # React components (ShapeGrid, Sidebar, MessageView, etc.)
│   ├── auth.config.js    # NextAuth authentication config
│   └── package.json      # Frontend npm dependencies
├── data/                 # Sample financial documents & dataset
└── eval/                 # RAG evaluation scripts & benchmark metrics
```

---

## Getting Started

### Prerequisites

Ensure you have the following installed on your machine:
- **Node.js**: v18.x or higher
- **Python**: v3.10 or higher
- **PostgreSQL**: v15+ with the `pgvector` extension installed

---

### 1. Database Setup

1. Enable `pgvector` in your PostgreSQL database:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```
2. Set your `DATABASE_URL` in the environment file:
   ```env
   DATABASE_URL="postgresql://postgres:password@localhost:5432/financerag"
   or ur hosted Db 
   ```

---

### 2. Backend Installation

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a Python virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On Linux/macOS:
   source venv/bin/activate
   ```
3. Install backend dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run Prisma database migrations:
   ```bash
   npx prisma migrate dev --name init
   ```
5. Start the FastAPI backend server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

---

### 3. Frontend Installation

1. Open a new terminal and navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Set up environment variables (`.env.local`):
   ```env
   NEXTAUTH_URL="http://localhost:3000"
   NEXTAUTH_SECRET="your-nextauth-secret-key"
   BACKEND_URL="http://localhost:8000"
   ```
4. Run the development server:
   ```bash
   npm run dev
   ```
5. Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## Evaluation & Testing

Run backend tests using `pytest`:

```bash
cd backend
pytest
```

---

