import asyncio
import time
from typing import Any, Dict, List
from agentgate.agents.graph import execute_agent_query
from agentgate.evals.metrics import calculate_faithfulness, calculate_relevance


async def _evaluate_single_strategy(strat: str, query: str) -> Dict[str, Any]:
    start_time = time.perf_counter()
    result = await execute_agent_query(query=query, strategy=strat, top_k=5)
    elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

    answer = result.get("answer", "")
    chunks = result.get("retrieved_chunks", [])
    chunk_texts = [c.get("content", "") for c in chunks]

    faithfulness = await asyncio.to_thread(calculate_faithfulness, answer, chunk_texts)
    relevance = calculate_relevance(query, chunk_texts)

    tokens = result.get("llm_tokens_used", 0)
    cost = result.get("estimated_cost_usd", 0.0)

    return {
        "strategy": strat.capitalize(),
        "faithfulness": round(faithfulness, 3),
        "relevance": round(relevance, 3),
        "context_relevance": round(relevance, 3),
        "latency_ms": elapsed_ms,
        "tokens_used": tokens,
        "cost_usd": cost,
        "chunks_retrieved": len(chunks),
    }


async def run_strategy_benchmark(
    sample_query: str = "How is authentication and rate limiting configured?",
) -> Dict[str, Any]:
    """Runs a side-by-side benchmark of Dense, Sparse, and Hybrid retrieval strategies concurrently."""
    strategies = ["dense", "sparse", "hybrid"]
    comparison_results: List[Dict[str, Any]] = await asyncio.gather(
        *[_evaluate_single_strategy(s, sample_query) for s in strategies]
    )

    response = {
        "benchmark_query": sample_query,
        "results": list(comparison_results),
    }
    for item in comparison_results:
        key = item["strategy"].lower()
        response[key] = item

    return response
