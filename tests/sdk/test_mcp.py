import socket
import pytest

from fastmcp import Client
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
async def test_retrieve_docs():
    mcp_client = VibeLlamaMCPClient()
    res = await mcp_client.retrieve_docs("Human in the loop")
    assert isinstance(res, str)
    assert "<result>" in res
    res1 = await mcp_client.retrieve_docs("Human in the loop", top_k=4, parse_xml=True)
    assert isinstance(res1, dict)
    assert "result" in res1
    assert len(res1["result"]) <= 4
