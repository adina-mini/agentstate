"""Retrieval strategies for AgentGate: Dense, Sparse (BM25), and Hybrid (RRF)."""

from agentgate.retrieval.dense import DenseRetriever, get_dense_retriever
from agentgate.retrieval.sparse import SparseRetriever
from agentgate.retrieval.hybrid import HybridRetriever, get_hybrid_retriever

__all__ = [
    "DenseRetriever",
    "get_dense_retriever",
    "SparseRetriever",
    "HybridRetriever",
    "get_hybrid_retriever",
]
