from collections import defaultdict
from typing import Dict, List, Optional, Tuple
from agentgate.connectors.base import Chunk
from agentgate.retrieval.dense import DenseRetriever, get_dense_retriever
from agentgate.retrieval.sparse import SparseRetriever


class HybridRetriever:
    """Hybrid Retriever combining Dense (embeddings) and Sparse (BM25) via Reciprocal Rank Fusion (RRF)."""

    def __init__(
        self,
        dense_retriever: Optional[DenseRetriever] = None,
        rrf_k: int = 60,
    ):
        self.dense = dense_retriever or get_dense_retriever()
        self.sparse = SparseRetriever()
        self.rrf_k = rrf_k
        self._sparse_synced = False

    def sync_sparse_index(self) -> None:
        """Syncs all chunks from the dense vector store into the in-memory sparse index."""
        all_chunks = self.dense.get_all_chunks()
        self.sparse.fit(all_chunks)
        self._sparse_synced = True

    def search(
        self,
        query: str,
        top_k: int = 5,
        dense_weight: float = 0.5,
        sparse_weight: float = 0.5,
    ) -> List[Tuple[Chunk, float]]:
        if not self._sparse_synced:
            self.sync_sparse_index()

        # Retrieve candidates from both
        dense_results = self.dense.search(query, top_k=top_k * 2)
        sparse_results = self.sparse.search(query, top_k=top_k * 2)

        if not dense_results and not sparse_results:
            return []
        if not dense_results:
            return sparse_results[:top_k]
        if not sparse_results:
            return dense_results[:top_k]

        # Reciprocal Rank Fusion
        rrf_scores: Dict[str, float] = defaultdict(float)
        chunk_map: Dict[str, Chunk] = {}

        for rank, (chunk, _) in enumerate(dense_results, start=1):
            chunk_map[chunk.id] = chunk
            rrf_scores[chunk.id] += dense_weight * (1.0 / (self.rrf_k + rank))

        for rank, (chunk, _) in enumerate(sparse_results, start=1):
            chunk_map[chunk.id] = chunk
            rrf_scores[chunk.id] += sparse_weight * (1.0 / (self.rrf_k + rank))

        # Normalize scores to [0, 1]
        max_score = max(rrf_scores.values()) if rrf_scores else 1.0
        sorted_chunks = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

        results: List[Tuple[Chunk, float]] = []
        for cid, raw_score in sorted_chunks[:top_k]:
            normalized_score = round(raw_score / max_score, 4)
            results.append((chunk_map[cid], normalized_score))

        return results


_hybrid_instance: Optional[HybridRetriever] = None


def get_hybrid_retriever() -> HybridRetriever:
    global _hybrid_instance
    if _hybrid_instance is None:
        _hybrid_instance = HybridRetriever()
    return _hybrid_instance
