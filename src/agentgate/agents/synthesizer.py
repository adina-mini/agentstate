import time
from typing import Any, Dict, List
from agentgate.agents.state import AgentState
from agentgate.config import settings


def synthesizer_node(state: AgentState) -> Dict[str, Any]:
    """Synthesizer Agent: Generates grounded answers with strict source citations."""
    intent = state.get("intent", "knowledge_query")
    query = state.get("query", "")
    chunks = state.get("retrieved_chunks", [])
    scores = state.get("retrieval_scores", [])

    # Handle greetings
    if intent == "greeting":
        return {
            "answer": "Hello! I am AgentGate, your enterprise knowledge assistant. Ask me anything about your connected codebases, documentation, or specifications.",
            "citations": [],
            "confidence": 1.0,
            "llm_tokens_used": 0,
            "estimated_cost_usd": 0.0,
        }

    # Handle off-topic
    if intent == "off_topic":
        return {
            "answer": "I specialize in answering questions grounded in your connected enterprise knowledge sources and repositories. Please ask a technical or documentation question related to your synced sources.",
            "citations": [],
            "confidence": 0.8,
            "llm_tokens_used": 0,
            "estimated_cost_usd": 0.0,
        }

    # Handle case with no retrieved chunks
    if not chunks:
        return {
            "answer": "I could not find any relevant documentation or code matching your question in the currently connected knowledge sources. Please check your query or connect additional sources.",
            "citations": [],
            "confidence": 0.2,
            "llm_tokens_used": 0,
            "estimated_cost_usd": 0.0,
        }

    # Format context for prompt
    context_blocks = []
    citations: List[Dict[str, Any]] = []
    for idx, chunk in enumerate(chunks, start=1):
        score = scores[idx - 1] if idx - 1 < len(scores) else 0.0
        context_blocks.append(
            f"[Source {idx}] ({chunk.get('source_title', 'Doc')})\n{chunk.get('content')}"
        )
        citations.append(
            {
                "title": f"[Source {idx}] {chunk.get('source_title', 'Doc')}",
                "url": chunk.get("source_url"),
                "snippet": chunk.get("content", "")[:200] + "...",
                "relevance_score": score,
            }
        )

    context_str = "\n\n".join(context_blocks)
    avg_score = sum(scores) / max(1, len(scores))

    # Invoke LLM if Groq key exists
    tokens_used = 0
    cost_usd = 0.0
    if settings.groq_api_key:
        try:
            from langchain_groq import ChatGroq
            from langchain_core.messages import SystemMessage, HumanMessage

            llm = ChatGroq(
                groq_api_key=settings.groq_api_key,
                model_name=settings.llm_model,
                temperature=settings.llm_temperature,
            )
            system_prompt = (
                "You are AgentGate's Synthesizer Agent. Answer the user's question accurately using ONLY the provided sources.\n"
                "RULES:\n"
                "1. Cite sources inline using bracketed notation like [Source 1], [Source 2].\n"
                "2. Do not invent facts not present in the sources.\n"
                "3. If the sources do not provide sufficient information to answer fully, explicitly acknowledge the gaps."
            )
            user_prompt = f"Context Sources:\n{context_str}\n\nQuestion: {query}\n\nAnswer:"
            resp = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)])

            # Estimate tokens & cost
            tokens_used = len(user_prompt.split()) + len(resp.content.split())
            # $0.59 per million tokens rough benchmark
            cost_usd = round((tokens_used / 1_000_000) * 0.59, 6)

            return {
                "answer": resp.content.strip(),
                "citations": citations,
                "confidence": round(min(1.0, max(0.1, avg_score * 1.1)), 3),
                "llm_tokens_used": tokens_used,
                "estimated_cost_usd": cost_usd,
            }
        except Exception as e:
            print(f"[SynthesizerAgent] LLM generation error: {e}, falling back to chunk excerpt synthesis")

    # Fallback without LLM API key: synthesized excerpts
    fallback_answer = (
        f"Based on {len(chunks)} relevant excerpt(s) found in your connected knowledge base:\n\n"
    )
    for idx, c in enumerate(chunks, start=1):
        snippet = c.get("content", "")[:250].strip()
        fallback_answer += f"• **[Source {idx}]** ({c.get('source_title', 'Doc')}): \"{snippet}...\"\n\n"

    return {
        "answer": fallback_answer.strip(),
        "citations": citations,
        "confidence": round(avg_score, 3),
        "llm_tokens_used": 0,
        "estimated_cost_usd": 0.0,
    }
