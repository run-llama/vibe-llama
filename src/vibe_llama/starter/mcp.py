from fastmcp import FastMCP
from .utils import Retriever

mcp_server: FastMCP = FastMCP(name="VibeLlama MCP")
retr = Retriever()


@mcp_server.tool(
    name="get_relevant_context",
    title="Get Relevant Context from LlamaIndex LLM-friendly documentation",
    description="The get_relevant_context tool serves the purporse of getting relevant chunks of context from documentation starting from a query (str) and a top_k (int, maximum number of top matches to retrieve) argument. The query should be more a keyword-base search query than a natural-language question. It returns an XML-formatted string using the <match> tag to delimit a match and the <content> tag to delimit the match text content.",
)
async def get_relevant_context(query: str, top_k: int) -> str:
    doc_hits = await retr.retrieve(query, top_k)
    if doc_hits:
        return (
            "<result>\n"
            + "\n".join(
                [
                    f"\t<match>\n\t\t<content>{doc_hits[i]}</content>\n\t</match>"
                    for i in range(len(doc_hits))
                ]
            )
            + "\n</result>"
        )
    return "<error>\n\t<message>\n\t\t<content>Impossible to retrieve similar chunks at this time, try with another query!</content>\n\t</message>\n</error>"
