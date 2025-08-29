from fastmcp import Client
from fastmcp.client.client import CallToolResult
from mcp.types import TextContent, Tool
from typing import List, cast, Dict, Any

from vibe_llama.starter import mcp_server


class VibeLlamaMCPClient:
    """
    Client for vibe-llama MCP server.

    Attributes:
        client (Client): Client for the MCP server
    """

    def __init__(self) -> None:
        self.client = Client(mcp_server)

    async def list_tools(self) -> List[Tool]:
        """
        List available tools within the MCP server.
        """
        async with self.client:
            tools = await self.client.list_tools()
        return tools

    async def retrieve_docs(self, query: str) -> str:
        """Call the get_relevant_context MCP tool.

        Args:
            query (str): Query to use while retrieving relevant information from LlamaIndex documentation.
        """
        async with self.client:
            result = await self.client.call_tool(
                "get_relevant_context", {"query": query}
            )
        return cast(TextContent, result.content[0]).text

    async def call_tool(
        self, tool_name: str, tool_args: Dict[str, Any]
    ) -> CallToolResult:
        """
        Call an MCP tool directly.

        Args:
            tool_name (str): name of the tool to call, as reported in the MCP server
            tool_args (Dict[str, Any]): arguments to pass to the tool
        """
        async with self.client:
            result = await self.client.call_tool(tool_name, tool_args)
        return result
