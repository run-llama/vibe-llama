import socket
import pytest

from fastmcp import Client
from fastmcp.client.client import CallToolResult
from vibe_llama.sdk import VibeLlamaMCPClient


def is_port_open(host: str, port: int, timeout: float = 2.0) -> bool:
    """Check if a TCP port is open on a given host."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        return result == 0


def test_class_init():
    mcp_client = VibeLlamaMCPClient()
    assert isinstance(mcp_client.client, Client)


@pytest.mark.skipif(
    condition=(not is_port_open("127.0.0.1", 8000)), reason="MCP server not available"
)
@pytest.mark.asyncio
async def test_tools_list():
    mcp_client = VibeLlamaMCPClient()
    tools = await mcp_client.list_tools()
    assert isinstance(tools, list)
    assert len(tools) == 1
    assert tools[0].name == "get_relevant_context"


@pytest.mark.skipif(
    condition=(not is_port_open("127.0.0.1", 8000)), reason="MCP server not available"
)
@pytest.mark.asyncio
async def test_call_tool():
    mcp_client = VibeLlamaMCPClient()
    res = await mcp_client.call_tool(
        "get_relevant_context", {"query": "Human in the loop"}
    )
    assert isinstance(res, CallToolResult)
    assert hasattr(res.content[0], "text")
    assert "Rank" in res.content[0].text  # type: ignore


@pytest.mark.skipif(
    condition=(not is_port_open("127.0.0.1", 8000)), reason="MCP server not available"
)
@pytest.mark.asyncio
async def test_retrieve_docs():
    mcp_client = VibeLlamaMCPClient()
    res = await mcp_client.retrieve_docs("Human in the loop")
    assert isinstance(res, str)
    assert "Rank" in res
