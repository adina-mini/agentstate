import time
from typing import Any, Dict
from langgraph.graph import StateGraph, END
from agentgate.agents.state import AgentState
from agentgate.agents.router import router_node
from agentgate.agents.retriever import retriever_node
from agentgate.agents.synthesizer import synthesizer_node


def decide_route(state: AgentState) -> str:
    """Conditional edge decision function."""
    intent = state.get("intent", "knowledge_query")
    if intent == "knowledge_query":
        return "retriever"
    return "synthesizer"


def create_agent_graph():
    """Builds and compiles the multi-agent LangGraph workflow."""
    workflow = StateGraph(AgentState)

    # Add agent nodes
    workflow.add_node("router", router_node)
    workflow.add_node("retriever", retriever_node)
    workflow.add_node("synthesizer", synthesizer_node)

    # Set entry point
    workflow.set_entry_point("router")

    # Add conditional branching from router
    workflow.add_conditional_edges(
        "router",
        decide_route,
        {
            "retriever": "retriever",
            "synthesizer": "synthesizer",
        },
    )

    # Add normal edges
    workflow.add_edge("retriever", "synthesizer")
    workflow.add_edge("synthesizer", END)

    return workflow.compile()


async def execute_agent_query(
    query: str,
    strategy: str = "hybrid",
    top_k: int = 5,
) -> Dict[str, Any]:
    """Helper function to execute the full LangGraph graph with latency tracking."""
    start_time = time.perf_counter()
    graph = create_agent_graph()

    initial_state: AgentState = {
        "query": query,
        "retrieval_strategy": strategy,
        "top_k": top_k,
        "intent": "knowledge_query",
        "retrieved_chunks": [],
        "retrieval_scores": [],
        "answer": "",
        "citations": [],
        "confidence": 0.0,
        "latency_ms": 0.0,
        "llm_tokens_used": 0,
        "estimated_cost_usd": 0.0,
    }

    result = await graph.ainvoke(initial_state)
    elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
    result["latency_ms"] = elapsed_ms
    return result
