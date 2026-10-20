from fastapi import APIRouter, Query
from agentgate.api.models import EvalSummaryResponse
from agentgate.db.database import get_db
from agentgate.evals.comparison import run_strategy_benchmark

router = APIRouter(prefix="/evals", tags=["Evals"])


@router.get("", response_model=EvalSummaryResponse)
def get_eval_telemetry(limit: int = Query(default=50, ge=1, le=200)):
    """Returns real-time aggregated evaluation metrics and recent query logs."""
    db = get_db()
    summary = db.get_eval_summary()
    logs = db.get_recent_evals(limit=limit)
    return EvalSummaryResponse(summary=summary, recent_logs=logs)


@router.get("/comparison")
async def get_strategy_comparison(
    query: str = Query(
        default="How is authentication and rate limiting configured?",
        description="Query to test across retrieval strategies",
    )
):
    """Executes live side-by-side comparison between Dense, Sparse, and Hybrid retrieval."""
    benchmark = await run_strategy_benchmark(sample_query=query)
    return benchmark
