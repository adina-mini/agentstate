import os
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

    # Invoke LLM if Gemini or Groq key exists
    tokens_used = 0
    cost_usd = 0.0
    gemini_key = settings.gemini_api_key or settings.google_api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    groq_key = settings.groq_api_key or os.environ.get("GROQ_API_KEY")

    system_prompt = (
        "You are AgentGate's Synthesizer Agent. Answer the user's question directly, clearly, and naturally using ONLY the provided context sources.\n"
        "STYLE GUIDELINES:\n"
        "1. Write in natural, fluid, clean prose. Avoid robotic, overly rigid bullet points.\n"
        "2. Do NOT spam bold asterisks (**) around every skill, name, or word. Keep the text clean and readable.\n"
        "3. Cite sources cleanly using [Source 1], [Source 2] at the end of key statements.\n"
        "4. Be concise and helpful. Never invent facts not present in the sources."
    )
    user_prompt = f"Context Sources:\n{context_str}\n\nQuestion: {query}\n\nAnswer:"

    # 1. Try Gemini first if key available
    if gemini_key:
        candidate_models = [settings.gemini_model or "gemini-2.5-flash", "gemini-2.5-flash"]
        tried_models = set()
        for model_name in candidate_models:
            if not model_name or model_name in tried_models:
                continue
            tried_models.add(model_name)
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
                from langchain_core.messages import SystemMessage, HumanMessage

                llm = ChatGoogleGenerativeAI(
                    model=model_name,
                    google_api_key=gemini_key,
                    temperature=0.2,
                    request_timeout=8.0,
                    max_retries=1,
                )
                resp = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)])
                tokens_used = len(user_prompt.split()) + len(resp.content.split())
                cost_usd = round((tokens_used / 1_000_000) * 0.075, 6)

                return {
                    "answer": resp.content.strip(),
                    "citations": citations,
                    "confidence": round(min(1.0, max(0.1, avg_score * 1.1)), 3),
                    "llm_tokens_used": tokens_used,
                    "estimated_cost_usd": cost_usd,
                }
            except Exception as e:
                print(f"[SynthesizerAgent] Gemini model '{model_name}' error: {e}")

    # 2. Try Groq if key available
    if groq_key:
        groq_candidates = [settings.groq_model, "openai/gpt-oss-120b", "qwen/qwen3.8-27b", "llama-3.3-70b-versatile"]
        tried_groq = []
        for g_model in groq_candidates:
            if not g_model or g_model in tried_groq:
                continue
            tried_groq.append(g_model)
            try:
                from langchain_groq import ChatGroq
                from langchain_core.messages import SystemMessage, HumanMessage

                llm = ChatGroq(
                    groq_api_key=groq_key,
                    model_name=g_model,
                    temperature=settings.llm_temperature,
                )
                resp = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)])
                tokens_used = len(user_prompt.split()) + len(resp.content.split())
                cost_usd = round((tokens_used / 1_000_000) * 0.59, 6)

                return {
                    "answer": resp.content.strip(),
                    "citations": citations,
                    "confidence": round(min(1.0, max(0.1, avg_score * 1.1)), 3),
                    "llm_tokens_used": tokens_used,
                    "estimated_cost_usd": cost_usd,
                }
            except Exception as e:
                print(f"[SynthesizerAgent] Groq model '{g_model}' error: {e}")

    # Fallback without LLM API key: synthesized excerpts
    fallback_answer = (
        f"Based on {len(chunks)} relevant excerpt(s) found in your connected knowledge base:\n\n"
    )
    for idx, c in enumerate(chunks, start=1):
        snippet = c.get("content", "")[:250].strip()
        fallback_answer += f"- **[Source {idx}]** ({c.get('source_title', 'Doc')}): \"{snippet}...\"\n\n"

    return {
        "answer": fallback_answer.strip(),
        "citations": citations,
        "confidence": round(avg_score, 3),
        "llm_tokens_used": 0,
        "estimated_cost_usd": 0.0,
    }
