# MIB RAG Chatbot

A domain-specific, privacy-preserving **Retrieval-Augmented Generation (RAG) Chatbot** designed to answer natural language questions grounded in MIB Tech Solutions documentation.

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    React Frontend                       │
│       (Vite + Lucide/CSS Glassmorphism UI)              │
└──────────────────────────┬──────────────────────────────┘
                           │ HTTP /api/chat
┌──────────────────────────▼──────────────────────────────┐
│                    FastAPI Backend                      │
│             (REST API + Session Management)             │
└──────────────┬───────────────────────────┬──────────────┘
               │                           │
┌──────────────▼─────────────┐   ┌─────────▼──────────────┐
│       Vector Store         │   │       Local LLM        │
│  ChromaDB + all-MiniLM-L6  │   │   Ollama (Llama 3.2 3B)│
│    (Embeddings & Top-K)    │   │  (Grounded Synthesis)  │
└────────────────────────────┘   └────────────────────────┘
```

---

## 📋 Tech Stack

- **Frontend**: React 19, Vite, Marked (Markdown rendering), Vanilla CSS (Responsive Dark Mode Glassmorphism)
- **Backend**: Python 3.13, FastAPI, Uvicorn, Pydantic v2
- **RAG Framework**: LlamaIndex v0.14+
- **Vector Database**: ChromaDB
- **Embedding Model**: `sentence-transformers/all-MiniLM-L6-v2` (Local, Hugging Face)
- **Local LLM**: Ollama (`llama3.2:3b`)

---

## 🚀 Quick Start

### 1. Prerequisites

- **Python 3.11+** (virtual environment in `venv/`)
- **Node.js 18+**
- **Ollama** installed with `llama3.2:3b`:
  ```bash
  ollama pull llama3.2:3b
  ```

---

### 2. Ingest MIB Documents

Ingest raw PDF/DOCX/TXT files into ChromaDB:

```bash
# Windows PowerShell
.\venv\Scripts\python scripts/ingest_documents.py

# macOS/Linux
./venv/bin/python scripts/ingest_documents.py
```

---

### 3. Run Backend (FastAPI)

```bash
cd backend
..\venv\Scripts\uvicorn app.main:app --reload --port 8000
```

- **Interactive API Docs (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check**: [http://localhost:8000/api/health](http://localhost:8000/api/health)

---

### 4. Run Frontend (React + Vite)

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

- **Chat Interface**: [http://localhost:5173](http://localhost:5173)

---

## 🧪 Evaluation & Testing

Run automated evaluation against 14 benchmark test cases (factual, paraphrased, multi-chunk, follow-ups, out-of-scope, ambiguous, terminology variations):

```bash
cd backend
..\venv\Scripts\python -m app.evaluation.evaluator
```

---

## 📁 Project Structure

```
mib-rag-chatbot/
├── backend/
│   ├── app/
│   │   ├── api/             # FastAPI routes (/chat, /health, /ingest)
│   │   ├── core/            # App configuration & settings
│   │   ├── evaluation/      # Benchmark test cases & evaluator
│   │   ├── ingestion/       # PDF/DOCX/TXT loader & chunking logic
│   │   ├── models/          # Pydantic request/response schemas
│   │   ├── rag/             # LlamaIndex pipeline, prompts & retrieval
│   │   └── services/        # ChromaDB & Ollama health services
│   ├── data/
│   │   ├── chroma/          # Persistent ChromaDB vector store
│   │   └── documents/       # Raw knowledge base documents
│   ├── requirements.txt     # Python backend dependencies
│   └── .env                 # Environment variables
├── frontend/                # Vite + React chat application
│   ├── src/
│   │   ├── App.jsx          # Chat UI component with suggestions & citation chips
│   │   ├── App.css          # Premium glassmorphic styling
│   │   ├── api.js           # Backend API integration
│   │   └── main.jsx         # React application entry point
│   ├── index.html
│   ├── package.json
│   └── vite.config.js       # Vite config with /api proxy
├── scripts/
│   └── ingest_documents.py  # CLI document ingestion script
└── README.md
```
