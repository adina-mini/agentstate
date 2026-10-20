from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    query: str = Field(..., description="The user query or question")
    strategy: str = Field(default="hybrid", description="Retrieval strategy: hybrid | dense | sparse")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of context chunks to retrieve")


class CitationModel(BaseModel):
    title: str
    url: Optional[str] = None
    snippet: str
    relevance_score: float


class QueryResponse(BaseModel):
    query: str
    answer: str
    citations: List[CitationModel]
    confidence: float
    strategy: str
    latency_ms: float
    llm_tokens_used: int
    estimated_cost_usd: float


class GitHubSourceRequest(BaseModel):
    repo: str = Field(..., description="GitHub repository in 'owner/repo' or URL format")
    token: Optional[str] = Field(default=None, description="Optional GitHub personal access token")


class SourceResponse(BaseModel):
    id: str
    name: str
    type: str
    config: Dict[str, Any]
    doc_count: int
    status: str
    last_synced: Optional[str] = None
    created_at: Optional[str] = None


class EvalLogModel(BaseModel):
    id: int
    timestamp: str
    query: str
    strategy: str
    answer: str
    faithfulness: Optional[float] = None
    relevance: Optional[float] = None
    latency_ms: float
    tokens_used: int
    cost_usd: float
    sources: List[Dict[str, Any]]


class EvalSummaryResponse(BaseModel):
    summary: Dict[str, Any]
    recent_logs: List[EvalLogModel]
