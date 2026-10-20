import time
from typing import Any, Dict, List
from agentgate.agents.graph import execute_agent_query
from agentgate.evals.metrics import calculate_faithfulness, calculate_relevance


async def run_strategy_benchmark(
    sample_query: str = "How is authentication and rate limiting configured?",
) -> Dict[str, Any]:
    """Runs a side-by-side benchmark of Dense, Sparse, and Hybrid retrieval strategies."""
    strategies = ["dense", "sparse", "hybrid"]
    comparison_results: List[Dict[str, Any]] = []

    for strat in strategies:
        start_time = time.perf_counter()
        result = await execute_agent_query(query=sample_query, strategy=strat, top_k=5)
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        answer = result.get("answer", "")
        chunks = result.get("retrieved_chunks", [])
        chunk_texts = [c.get("content", "") for c in chunks]

        faithfulness = calculate_faithfulness(answer, chunk_texts)
        relevance = calculate_relevance(sample_query, chunk_texts)

        tokens = result.get("llm_tokens_used", 0)
        cost = result.get("estimated_cost_usd", 0.0)

        comparison_results.append(
            {
                "strategy": strat.capitalize(),
                "faithfulness": round(faithfulness, 3),
                "relevance": round(relevance, 3),
                "latency_ms": elapsed_ms,
                "tokens_used": tokens,
                "cost_usd": cost,
                "chunks_retrieved": len(chunks),
            }
        )

    return {
        "benchmark_query": sample_query,
        "results": comparison_results,
    }
