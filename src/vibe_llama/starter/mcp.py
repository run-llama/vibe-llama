from fastmcp import FastMCP
from .utils import Retriever

mcp: FastMCP = FastMCP(name="VibeLlama MCP")
retr = Retriever()


@mcp.tool(
    name="get_relevant_context",
    title="Get Relevant Context from LlamaIndex LLM-friendly documentation",
    description="The get_relevant_context tool serves the purporse of getting relevant chunks of context from documentation starting from a query (str) argument",
)
async def get_relevant_context(query: str) -> str:
    doc_hits = await retr.retrieve(query)
    if doc_hits:
        return "\n".join([f"Rank {i}\n{doc_hits[i]}" for i in range(len(doc_hits))])
    return "Impossible to retrieve similar chunks at this time, try with another query!"
