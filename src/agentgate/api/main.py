from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from agentgate.api.routes import evals, query, sources
from agentgate.config import settings
from agentgate.db.database import get_db
from agentgate.retrieval.hybrid import get_hybrid_retriever


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure directories and initialize database schema
    settings.ensure_directories()
    get_db()
    # Pre-sync sparse index in background
    try:
        get_hybrid_retriever().sync_sparse_index()
    except Exception as e:
        print(f"[Lifespan] Initial index sync notice: {e}")
    yield


app = FastAPI(
    title="AgentGate API",
    description="MCP-Native Knowledge Gateway with Multi-Agent Retrieval & Eval Engine",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(query.router, prefix="/api")
app.include_router(sources.router, prefix="/api")
app.include_router(evals.router, prefix="/api")

# Static files & Web Dashboard
from pathlib import Path
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/", tags=["Dashboard"], include_in_schema=False)
    async def serve_dashboard():
        index_file = STATIC_DIR / "index.html"
        return FileResponse(str(index_file))


@app.get("/api/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": "AgentGate",
        "version": "0.1.0",
        "llm_model": settings.llm_model,
        "embedding_model": settings.embedding_model,
    }


def start():
    """CLI script entrypoint to start API server."""
    uvicorn.run(
        "agentgate.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
    )


if __name__ == "__main__":
    start()
