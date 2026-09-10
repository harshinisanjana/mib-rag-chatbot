# AI Customer Support Knowledge Base - RAG Chatbot

A full-stack RAG-based customer support system with document ingestion, semantic search, grounded AI responses using Groq LLM, and a customer-facing chat experience.

## 🏗️ Architecture Overview

```
Frontend (Angular)
    ↓
Backend (FastAPI)
    ↓
Database (PostgreSQL + pgvector)
    ↓
LLM (Groq API)
```

## 📋 Tech Stack

### Frontend
- Angular
- TypeScript
- Angular Router
- Reactive Forms
- CSS

### Backend
- Python 3.13+
- FastAPI
- SQLAlchemy
- Pydantic
- Alembic

### Database
- PostgreSQL
- pgvector (for semantic search)

### LLM & Embeddings
- Groq API (`openai/gpt-oss-20b`)
- Sentence Transformers for embeddings

### Document Processing
- PyMuPDF (PDF)
- python-docx (DOCX)

## 🚀 Quick Start

### Prerequisites
- Python 3.13+
- PostgreSQL 14+ with pgvector extension
- Node.js 18+ (for Angular)
- Groq API key

### Backend Setup

1. **Create and activate virtual environment** (Already created):
   ```bash
   cd backend
   ..\venv\Scripts\Activate.ps1  # Windows PowerShell
   # or
   source ../venv/bin/activate  # macOS/Linux
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Create `.env` file** (copy from `.env.example`):
   ```bash
   cp .env.example .env
   ```
   Update with your actual values:
   - PostgreSQL connection string
   - Groq API key
   - JWT secret key

4. **Initialize database**:
   ```bash
   alembic upgrade head
   ```

5. **Run backend**:
   ```bash
   python -m uvicorn app.main:app --reload --port 8000
   ```

   Health check: `http://localhost:8000/health`

### Frontend Setup

1. **Install dependencies**:
   ```bash
   cd frontend
   npm install
   ```

2. **Configure backend proxy** (for development):
   The repository includes `proxy.conf.json`:
   ```json
   {
     "/api": {
       "target": "http://localhost:8000",
       "secure": false
     }
   }
   ```

3. **Run frontend**:
   ```bash
   ng serve --proxy-config proxy.conf.json
   ```

   Open: `http://localhost:4200`

## 📁 Project Structure

```
mib-rag-chatbot/
├── venv/                          # Python virtual environment
├── backend/
│   ├── app/
│   │   ├── main.py               # FastAPI app entry point
│   │   ├── api/                  # API routes (auth, documents, chat, etc.)
│   │   ├── core/                 # Config, security
│   │   ├── db/                   # Database connection
│   │   ├── models/               # SQLAlchemy models
│   │   ├── schemas/              # Pydantic schemas
│   │   ├── services/             # Business logic
│   │   └── utils/                # Utilities
│   ├── uploads/                  # Uploaded documents
│   ├── alembic/                  # Database migrations
│   ├── requirements.txt
│   ├── .env.example
│   └── .env                       # (create locally)
├── frontend/                       # Angular application
├── .gitignore
└── README.md
```

## 🔄 Development Phases

1. **Phase 1**  Foundation
   -  Backend & frontend structure
   -  Environment configuration
   -  FastAPI health endpoint
   -  Verify both apps run

2. **Phase 2** Database
   -  SQLAlchemy models
   -  Alembic migrations
   -  pgvector setup

3. **Phase 3** Authentication
   -  Admin & agent login
   -  JWT tokens
   -  Role-based access

4. **Phase 4** Document Management
   -  Upload, store, delete
   -  Document status tracking

5. **Phase 5** Document Processing
   -  PDF/DOCX extraction
   -  Text cleaning & chunking

6. **Phase 6** Embeddings
   -  Embedding service
   -  Vector storage in pgvector

7. **Phase 7** Retrieval
   -  Semantic search with pgvector
   -  Top-k retrieval

8. **Phase 8** RAG + Groq Integration
   -  Prompt construction
   -  Groq API integration
   -  Hallucination prevention

9. **Phase 9** Customer Chat
   -  Chat UI
   -  API integration
   -  Source attribution

10. **Phase 10** Escalation
    -  Escalation workflow

11. **Phase 11** Testing & Hardening
    -  Comprehensive testing
    -  Security validation

## 🔐 Security

- JWT authentication for admin & support agents
- Bcrypt password hashing
- Environment-based secrets (no hardcoded keys)
- File validation & safe filenames
- CORS configuration
- Input validation with Pydantic

## 📚 API Documentation

Once the backend is running:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

