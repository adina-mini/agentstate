import asyncio
import sys
from agentgate.mcp_server.tools import (
    get_document_tool,
    get_knowledge_stats_resource,
    list_sources_tool,
    search_knowledge_tool,
)


def create_mcp_server():
    """Initializes FastMCP server instance with registered tools and resources."""
    try:
        from mcp.server.fastmcp import FastMCP

        mcp = FastMCP("agentgate", description="AgentGate Enterprise Knowledge Gateway")

        @mcp.tool(name="search_knowledge", description="Search connected enterprise knowledge sources")
        async def search_knowledge(query: str, top_k: int = 5) -> str:
            return await search_knowledge_tool(query=query, top_k=top_k)

        @mcp.tool(name="list_sources", description="List all connected knowledge repositories and sources")
        def list_sources() -> str:
            return list_sources_tool()

        @mcp.tool(name="get_document", description="Retrieve full document or chunk details by document ID")
        def get_document(doc_id: str) -> str:
            return get_document_tool(doc_id=doc_id)

        @mcp.resource("knowledge://stats", description="System knowledge statistics and health metrics")
        def knowledge_stats() -> str:
            return get_knowledge_stats_resource()

        return mcp
    except ImportError:
        # Fallback runner for environments where MCP SDK is in process of being installed
        print("MCP package not yet installed. Run 'pip install mcp'", file=sys.stderr)
        return None


def main():
    """Entry point for running the MCP server over stdio."""
    server = create_mcp_server()
    if server:
        server.run()
    else:
        print("Failed to start AgentGate MCP server.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
