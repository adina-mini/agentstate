import time
from typing import Any, Dict
from agentgate.agents.state import AgentState
from agentgate.config import settings

GREETING_WORDS = {"hello", "hi", "hey", "good morning", "good evening", "howdy", "sup"}


def router_node(state: AgentState) -> Dict[str, Any]:
    """Router Agent: Classifies intent into knowledge_query, greeting, or off_topic."""
    query = state.get("query", "").strip()
    clean_lower = query.lower()

    # Fast heuristic check for greetings
    if clean_lower in GREETING_WORDS or len(clean_lower.split()) <= 2 and any(w in clean_lower for w in GREETING_WORDS):
        return {"intent": "greeting"}

    # Check Gemini first
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
                "You are an intent classifier for an enterprise knowledge retrieval system.\n"
                "Classify the following query into exactly ONE category:\n"
                "- knowledge_query: questions about code, documentation, APIs, architectures, guides, technical details.\n"
                "- greeting: casual pleasantries or hellos.\n"
                "- off_topic: unrelated queries that cannot be answered by documentation.\n"
                "Respond with ONLY the category name and nothing else."
            )
            resp = llm.invoke([SystemMessage(content=prompt), HumanMessage(content=query)])
            classified = resp.content.strip().lower()
            if "knowledge" in classified:
                return {"intent": "knowledge_query"}
            elif "greeting" in classified:
                return {"intent": "greeting"}
            elif "off_topic" in classified:
                return {"intent": "off_topic"}
            return {"intent": "knowledge_query"}
        except Exception as e:
            print(f"[RouterAgent] Gemini classification error: {e}, trying alternative")

    # If Groq is available, try Groq
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
                "You are an intent classifier for an enterprise knowledge retrieval system.\n"
                "Classify the following query into exactly ONE category:\n"
                "- knowledge_query: questions about code, documentation, APIs, architectures, guides, technical details.\n"
                "- greeting: casual pleasantries or hellos.\n"
                "- off_topic: unrelated queries that cannot be answered by documentation.\n"
                "Respond with ONLY the category name and nothing else."
            )
            resp = llm.invoke([SystemMessage(content=prompt), HumanMessage(content=query)])
            classified = resp.content.strip().lower()
            if "knowledge" in classified:
                return {"intent": "knowledge_query"}
            elif "greeting" in classified:
                return {"intent": "greeting"}
            elif "off_topic" in classified:
                return {"intent": "off_topic"}
            return {"intent": "knowledge_query"}
        except Exception as e:
            print(f"[RouterAgent] Groq classification error: {e}, using fallback")

    # Fallback default: Treat any question or multi-word prompt as knowledge_query
    return {"intent": "knowledge_query"}
