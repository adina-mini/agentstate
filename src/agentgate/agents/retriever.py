from typing import Any, Dict
from agentgate.agents.state import AgentState
from agentgate.retrieval.dense import get_dense_retriever
from agentgate.retrieval.sparse import SparseRetriever
from agentgate.retrieval.hybrid import get_hybrid_retriever


def retriever_node(state: AgentState) -> Dict[str, Any]:
    """Retriever Agent: Performs dense, sparse, or hybrid search based on state config."""
    query = state.get("query", "")
    strategy = state.get("retrieval_strategy", "hybrid").lower()
    top_k = state.get("top_k", 5)

    if strategy == "dense":
        dense = get_dense_retriever()
        results = dense.search(query, top_k=top_k)
    elif strategy == "sparse":
        dense = get_dense_retriever()
        sparse = SparseRetriever(chunks=dense.get_all_chunks())
        results = sparse.search(query, top_k=top_k)
    else:  # hybrid
        hybrid = get_hybrid_retriever()
        results = hybrid.search(query, top_k=top_k)

    retrieved_chunks = [
        {
            "id": chunk.id,
            "document_id": chunk.document_id,
            "content": chunk.content,
            "chunk_index": chunk.chunk_index,
            "source_title": chunk.source_title,
            "source_url": chunk.source_url,
            "metadata": chunk.metadata,
        }
        for chunk, _ in results
    ]
    retrieval_scores = [score for _, score in results]

    return {
        "retrieved_chunks": retrieved_chunks,
        "retrieval_scores": retrieval_scores,
    }
