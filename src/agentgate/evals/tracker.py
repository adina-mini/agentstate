from typing import Any, Dict, List, Optional
from agentgate.db.database import Database, get_db
from agentgate.evals.metrics import calculate_faithfulness, calculate_relevance


class EvalTracker:
    """Logs evaluation telemetry and computes quality scores for queries."""

    def __init__(self, db: Optional[Database] = None):
        self.db = db or get_db()

    def record_query(
        self,
        query: str,
        strategy: str,
        answer: str,
        retrieved_chunks: List[Dict[str, Any]],
        latency_ms: float,
        tokens_used: int = 0,
        cost_usd: float = 0.0,
        citations: Optional[List[Dict[str, Any]]] = None,
    ) -> int:
        context_texts = [c.get("content", "") for c in retrieved_chunks]
        faithfulness = calculate_faithfulness(answer, context_texts)
        relevance = calculate_relevance(query, context_texts)

        log_id = self.db.log_eval(
            query=query,
            strategy=strategy,
            answer=answer,
            faithfulness=faithfulness,
            relevance=relevance,
            latency_ms=latency_ms,
            tokens_used=tokens_used,
            cost_usd=cost_usd,
            sources=citations or [],
        )
        return log_id


_tracker_instance: Optional[EvalTracker] = None


def get_eval_tracker() -> EvalTracker:
    global _tracker_instance
    if _tracker_instance is None:
        _tracker_instance = EvalTracker()
    return _tracker_instance
