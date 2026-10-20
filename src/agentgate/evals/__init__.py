"""Evaluation and observability framework for AgentGate."""

from agentgate.evals.comparison import run_strategy_benchmark
from agentgate.evals.metrics import calculate_faithfulness, calculate_relevance
from agentgate.evals.tracker import EvalTracker, get_eval_tracker

__all__ = [
    "calculate_faithfulness",
    "calculate_relevance",
    "EvalTracker",
    "get_eval_tracker",
    "run_strategy_benchmark",
]
