from fastapi import APIRouter, HTTPException
from agentgate.agents.graph import execute_agent_query
from agentgate.api.models import QueryRequest, QueryResponse
from agentgate.evals.tracker import get_eval_tracker

router = APIRouter(prefix="/query", tags=["Query"])


@router.post("", response_model=QueryResponse)
async def query_knowledge_base(request: QueryRequest):
    """Executes the multi-agent retrieval and synthesis graph, logging eval metrics."""
    try:
        result = await execute_agent_query(
            query=request.query,
            strategy=request.strategy,
            top_k=request.top_k,
        )

        # Track query in eval database
        tracker = get_eval_tracker()
        tracker.record_query(
            query=request.query,
            strategy=request.strategy,
            answer=result.get("answer", ""),
            retrieved_chunks=result.get("retrieved_chunks", []),
            latency_ms=result.get("latency_ms", 0.0),
            tokens_used=result.get("llm_tokens_used", 0),
            cost_usd=result.get("estimated_cost_usd", 0.0),
            citations=result.get("citations", []),
        )

        return QueryResponse(
            query=request.query,
            answer=result.get("answer", ""),
            citations=result.get("citations", []),
            confidence=result.get("confidence", 0.0),
            strategy=request.strategy,
            latency_ms=result.get("latency_ms", 0.0),
            llm_tokens_used=result.get("llm_tokens_used", 0),
            estimated_cost_usd=result.get("estimated_cost_usd", 0.0),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query execution failed: {str(e)}")
