from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.api.auth import router as auth_router
from app.api.documents import router as documents_router
from app.api.retrieval import router as retrieval_router
from app.api.rag import router as rag_router
from app.api.chat import router as chat_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Application starting...")
    yield
    print("Application shutting down...")

app = FastAPI(
    title=settings.app_name,
    description="RAG-based customer support system",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth_router)
app.include_router(documents_router)
app.include_router(retrieval_router)
app.include_router(rag_router)
app.include_router(chat_router)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "AI Customer Support Knowledge Base",
        "version": "0.1.0"
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to the AI Customer Support Knowledge Base API",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
