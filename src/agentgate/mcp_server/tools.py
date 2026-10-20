import json
from typing import Any, Dict, List
from agentgate.agents.graph import execute_agent_query
from agentgate.db.database import get_db
from agentgate.retrieval.dense import get_dense_retriever
from agentgate.retrieval.hybrid import get_hybrid_retriever


async def search_knowledge_tool(query: str, top_k: int = 5) -> str:
    """Tool: Search connected enterprise knowledge sources with hybrid retrieval."""
    result = await execute_agent_query(query=query, strategy="hybrid", top_k=top_k)
    answer = result.get("answer", "")
    citations = result.get("citations", [])

    output = f"Answer:\n{answer}\n\nSources:\n"
    for idx, cite in enumerate(citations, start=1):
        output += f"- [{idx}] {cite.get('title')} (Relevance: {cite.get('relevance_score')}): {cite.get('url') or 'N/A'}\n"

    return output


def list_sources_tool() -> str:
    """Tool: Lists all connected knowledge sources in AgentGate."""
    db = get_db()
    sources = db.list_sources()
    if not sources:
        return "No knowledge sources connected yet."

    lines = ["Connected Sources:"]
    for s in sources:
        lines.append(
            f"- [{s.get('id')}] {s.get('name')} | Type: {s.get('type')} | Documents: {s.get('doc_count')} | Status: {s.get('status')}"
        )
    return "\n".join(lines)


def get_document_tool(doc_id: str) -> str:
    """Tool: Fetches document details by ID from the vector store."""
    dense = get_dense_retriever()
    all_chunks = dense.get_all_chunks()
    matches = [c for c in all_chunks if c.document_id == doc_id or c.id == doc_id]

    if not matches:
        return f"Document with ID '{doc_id}' not found."

    header = f"Document: {matches[0].source_title}\nURL: {matches[0].source_url or 'N/A'}\nChunks: {len(matches)}\n\n"
    content = "\n---\n".join([f"[Chunk {c.chunk_index}]\n{c.content}" for c in matches])
    return header + content


def get_knowledge_stats_resource() -> str:
    """Resource: Returns system-wide knowledge statistics."""
    db = get_db()
    dense = get_dense_retriever()
    eval_summary = db.get_eval_summary()
    sources = db.list_sources()

    stats = {
        "total_sources": len(sources),
        "total_chunks_indexed": dense.count(),
        "total_queries_logged": eval_summary.get("total_queries", 0),
        "avg_faithfulness": eval_summary.get("avg_faithfulness", 0.0),
        "avg_latency_ms": eval_summary.get("avg_latency_ms", 0.0),
        "sources": [
            {"id": s.get("id"), "name": s.get("name"), "type": s.get("type"), "docs": s.get("doc_count")}
            for s in sources
        ],
    }
    return json.dumps(stats, indent=2)
