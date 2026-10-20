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

    # If Groq is available, use LLM intent classification
    if settings.groq_api_key:
        try:
            from langchain_groq import ChatGroq
            from langchain_core.messages import SystemMessage, HumanMessage

            llm = ChatGroq(
                groq_api_key=settings.groq_api_key,
                model_name=settings.llm_model,
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
                intent = "knowledge_query"
            elif "greeting" in classified:
                intent = "greeting"
            elif "off_topic" in classified:
                intent = "off_topic"
            else:
                intent = "knowledge_query"
            return {"intent": intent}
        except Exception as e:
            print(f"[RouterAgent] LLM classification error: {e}, using fallback")

    # Fallback default: Treat any question or multi-word prompt as knowledge_query
    return {"intent": "knowledge_query"}
