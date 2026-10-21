import pytest
from agentgate.agents.router import router_node
from agentgate.agents.graph import execute_agent_query


def test_router_greeting():
    state = {"query": "Hello there!"}
    res = router_node(state)
    assert res["intent"] == "greeting"


@pytest.mark.asyncio
async def test_agent_graph_greeting():
    res = await execute_agent_query("Hi AgentGate", strategy="hybrid", top_k=3)
    assert "answer" in res
    assert "confidence" in res
    assert res["latency_ms"] >= 0.0
