from fastmcp import Client
from mcp.types import TextContent, Tool
from typing import List, cast, Dict, Union

from vibe_llama.starter import mcp_server
from .utils import parse_xml_string


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

    async def retrieve_docs(
        self, query: str, top_k: int = 5, parse_xml: bool = False
    ) -> Union[str, Dict[str, List[str]]]:
        """Call the get_relevant_context MCP tool.

        Args:
            query (str): Query to use while retrieving relevant information from LlamaIndex documentation.
            top_k (int): Maximum number of top matches to retrieve
            parse_xml (bool): Parses the XML string returned by the tool and outputs a dictionary with the list of top matches under the 'result' key or with a list of error messages under the 'error' key.

        Returns:
            The raw XML string result _or_ the parsed XML string represented as a dictionary with either 'result' (successfull run) or 'error' (failed run) as key.
        """
        async with self.client:
            result = await self.client.call_tool(
                "get_relevant_context", {"query": query, "top_k": top_k}
            )
        if not parse_xml:
            return cast(TextContent, result.content[0]).text
        else:
            return parse_xml_string(cast(TextContent, result.content[0]).text)
