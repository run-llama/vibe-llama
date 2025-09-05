from pydantic import ConfigDict
from typing import Annotated
from llama_index.llms.openai import OpenAI
from workflows import Workflow, step, Context
from workflows.events import StartEvent, Event, StopEvent
from workflows.resource import Resource
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
from llama_index.core.schema import NodeWithScore
from llama_index.core.llms import LLM


class IndexCreatedEvent(Event):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    index: VectorStoreIndex


class RetrievalEvent(Event):
    documents: list[NodeWithScore]


async def get_llm(*args, **kwargs) -> LLM:
    return OpenAI(model="gpt-4.1")


class RAGWorkflow(Workflow):
    @step
    async def document_processing_step(
        self, ev: StartEvent, ctx: Context
    ) -> IndexCreatedEvent:
        async with ctx.store.edit_state() as state:
            state.query = ev.query
        docs = await SimpleDirectoryReader(ev.path).aload_data()
        index = VectorStoreIndex.from_documents(documents=docs)
        return IndexCreatedEvent(index=index)

    @step
    async def retrieve_step(
        self, ev: IndexCreatedEvent, ctx: Context
    ) -> RetrievalEvent:
        state = await ctx.store.get_state()
        retrieved_documents = await ev.index.as_retriever(top_k=5).aretrieve(
            state.query
        )
        return RetrievalEvent(documents=retrieved_documents)

    @step
    async def generate_step(
        self, ev: RetrievalEvent, llm: Annotated[LLM, Resource(get_llm)], ctx: Context
    ) -> StopEvent:
        state = await ctx.store.get_state()
        docs = "\\n\\n---\\n\\n".join(
            [
                f"Content: {node.text}\\nScore: {node.score if node.score else -1}"
                for node in ev.documents
            ]
        )
        prompt = f"Based on these documents:\\n\\n```md\\n{docs}\\n```\\n\\nAnswer this query: {state.query}"
        response = await llm.acomplete(prompt)
        return StopEvent(result=response.text)


async def main(path: str, query: str):
    w = RAGWorkflow(timeout=300)
    result = await w.run(path=path, query=query)
    print(str(result))


if __name__ == "__main__":
    import os
    import asyncio
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument(
        "-p",
        "--path",
        help="Path to the directory with the files to ingest",
        required=True,
    )
    parser.add_argument("-q", "--query", help="Retrieval query", required=True)
    args = parser.parse_args()

    if not os.getenv("OPENAI_API_KEY", None):
        raise ValueError(
            "You need to set OPENAI_API_KEY in your environment before using this workflow"
        )

    asyncio.run(main(args.path, args.query))
