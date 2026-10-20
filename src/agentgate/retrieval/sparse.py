import re
from typing import Any, List, Optional, Tuple
from agentgate.connectors.base import Chunk

try:
    from rank_bm25 import BM25Okapi, BM25Plus
    HAS_RANK_BM25 = True
except ImportError:
    HAS_RANK_BM25 = False


def tokenize(text: str) -> List[str]:
    """Simple alphanumeric lowercase tokenization."""
    return re.findall(r"\w+", text.lower())


class SparseRetriever:
    """Keyword-based BM25 sparse retriever with token overlap fallback."""

    def __init__(self, chunks: Optional[List[Chunk]] = None):
        self.chunks: List[Chunk] = []
        self.bm25: Optional[Any] = None
        if chunks:
            self.fit(chunks)

    def fit(self, chunks: List[Chunk]) -> None:
        self.chunks = chunks
        if not chunks:
            self.bm25 = None
            return

        corpus = [tokenize(c.content) for c in chunks]
        if HAS_RANK_BM25:
            # BM25Plus prevents negative IDF on small document collections
            self.bm25 = BM25Plus(corpus)
        else:
            self.bm25 = None

    def search(self, query: str, top_k: int = 5) -> List[Tuple[Chunk, float]]:
        if not query.strip() or not self.chunks:
            return []

        tokenized_query = tokenize(query)
        if not tokenized_query:
            return []

        if self.bm25 and HAS_RANK_BM25:
            scores = self.bm25.get_scores(tokenized_query)
            indexed_scores = [(idx, score) for idx, score in enumerate(scores) if score > 0]
            if indexed_scores:
                max_score = max(s for _, s in indexed_scores) if indexed_scores else 1.0
                indexed_scores.sort(key=lambda x: x[1], reverse=True)
                top = indexed_scores[:top_k]
                return [
                    (self.chunks[idx], round(float(score / max_score), 4))
                    for idx, score in top
                ]

        # Exact token overlap scoring fallback (handles single-document corpus & zero IDF)
        query_set = set(tokenized_query)
        matches: List[Tuple[int, float]] = []
        for idx, chunk in enumerate(self.chunks):
            chunk_tokens = set(tokenize(chunk.content))
            overlap = len(query_set.intersection(chunk_tokens))
            if overlap > 0:
                score = overlap / len(query_set)
                matches.append((idx, score))

        matches.sort(key=lambda x: x[1], reverse=True)
        return [(self.chunks[idx], round(score, 4)) for idx, score in matches[:top_k]]
