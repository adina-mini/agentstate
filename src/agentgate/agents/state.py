from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from typing_extensions import TypedDict


class Citation(BaseModel):
    title: str = Field(description="Document or source title")
    url: Optional[str] = Field(default=None, description="Direct URL")
    snippet: str = Field(description="Relevant text excerpt")
    relevance_score: float = Field(default=0.0, description="Relevance score in [0, 1]")


class AgentState(TypedDict):
    # Inputs
    query: str
    retrieval_strategy: str  # "hybrid" | "dense" | "sparse"
    top_k: int

    # Router output
    intent: str  # "knowledge_query" | "greeting" | "off_topic"

    # Retriever output
    retrieved_chunks: List[Dict[str, Any]]
    retrieval_scores: List[float]

    # Synthesizer output
    answer: str
    citations: List[Dict[str, Any]]
    confidence: float

    # Eval telemetry
    latency_ms: float
    llm_tokens_used: int
    estimated_cost_usd: float
