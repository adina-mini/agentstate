import re
from typing import List
from agentgate.config import settings


def tokenize_set(text: str) -> set:
    return set(re.findall(r"\w+", text.lower()))


def calculate_faithfulness(answer: str, context_chunks: List[str]) -> float:
    """Calculates how well the answer is grounded in the retrieved chunks (0.0 to 1.0).

    Uses LLM-as-a-judge if Groq is available, with lexical grounding fallback.
    """
    if not answer.strip() or not context_chunks:
        return 0.0

    combined_context = " ".join(context_chunks)

    # 1. Try Gemini judge first if key available
    gemini_key = settings.gemini_api_key or settings.google_api_key
    if gemini_key:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            from langchain_core.messages import SystemMessage, HumanMessage

            llm = ChatGoogleGenerativeAI(
                google_api_key=gemini_key,
                model=settings.gemini_model or "gemini-2.5-flash",
                temperature=0.0,
            )
            prompt = (
                "You are an impartial RAG evaluation judge. Evaluate the faithfulness of the answer based ONLY on the context.\n"
                "Give a score between 0.0 and 1.0 where 1.0 means every claim is fully supported by the context, and 0.0 means completely hallucinated.\n"
                "Output ONLY a single floating-point number between 0.0 and 1.0."
            )
            resp = llm.invoke(
                [
                    SystemMessage(content=prompt),
                    HumanMessage(content=f"Context:\n{combined_context[:3000]}\n\nAnswer:\n{answer}"),
                ]
            )
            match = re.search(r"\b0?\.\d+|\b1\.0|\b[01]\b", resp.content)
            if match:
                score = float(match.group(0))
                return max(0.0, min(1.0, score))
        except Exception as e:
            print(f"[EvalMetrics] Gemini faithfulness check error: {e}")

    # 2. Try Groq judge if key available
    if settings.groq_api_key:
        try:
            from langchain_groq import ChatGroq
            from langchain_core.messages import SystemMessage, HumanMessage

            llm = ChatGroq(
                groq_api_key=settings.groq_api_key,
                model_name=settings.groq_model or "openai/gpt-oss-120b",
                temperature=0.0,
            )
            prompt = (
                "You are an impartial RAG evaluation judge. Evaluate the faithfulness of the answer based ONLY on the context.\n"
                "Give a score between 0.0 and 1.0 where 1.0 means every claim is fully supported by the context, and 0.0 means completely hallucinated.\n"
                "Output ONLY a single floating-point number between 0.0 and 1.0."
            )
            resp = llm.invoke(
                [
                    SystemMessage(content=prompt),
                    HumanMessage(content=f"Context:\n{combined_context[:3000]}\n\nAnswer:\n{answer}"),
                ]
            )
            match = re.search(r"\b0?\.\d+|\b1\.0|\b[01]\b", resp.content)
            if match:
                score = float(match.group(0))
                return max(0.0, min(1.0, score))
        except Exception as e:
            print(f"[EvalMetrics] Groq faithfulness check error: {e}")

    # Deterministic fallback: claim token overlap ratio
    answer_tokens = tokenize_set(answer)
    context_tokens = tokenize_set(combined_context)
    if not answer_tokens:
        return 0.0

    overlap = len(answer_tokens.intersection(context_tokens))
    score = overlap / len(answer_tokens)
    return round(max(0.1, min(1.0, score * 1.15)), 3)


def calculate_relevance(query: str, context_chunks: List[str]) -> float:
    """Calculates the semantic relevance of retrieved context chunks to the query."""
    if not query.strip() or not context_chunks:
        return 0.0

    query_tokens = tokenize_set(query)
    if not query_tokens:
        return 0.0

    chunk_scores = []
    for chunk in context_chunks:
        chunk_tokens = tokenize_set(chunk)
        overlap = len(query_tokens.intersection(chunk_tokens))
        chunk_scores.append(overlap / len(query_tokens))

    avg_overlap = sum(chunk_scores) / max(1, len(chunk_scores))
    return round(max(0.1, min(1.0, avg_overlap * 1.5)), 3)
