from pydantic import BaseModel
from typing import Annotated
from llama_cloud_services import LlamaParse
from workflows import Workflow, step, Context
from workflows.events import StartEvent, Event, StopEvent
from workflows.resource import Resource


class ParseDocumentCostEffectiveEvent(Event):
    pass


class ParseDocumentAgenticEvent(Event):
    pass


class ParseDocumentAgenticPlusEvent(Event):
    pass


async def get_llama_parse_cost_effective(*args, **kwargs) -> LlamaParse:
    return LlamaParse(
        parse_mode="parse_page_with_llm",
        high_res_ocr=True,
        adaptive_long_table=True,
        outlined_table_extraction=True,
        output_tables_as_HTML=True,
        result_type="markdown",
    )


async def get_llama_parse_agentic(*args, **kwargs) -> LlamaParse:
    return LlamaParse(
        parse_mode="parse_page_with_agent",
        model="openai-gpt-4-1-mini",
        high_res_ocr=True,
        adaptive_long_table=True,
        outlined_table_extraction=True,
        output_tables_as_HTML=True,
        result_type="markdown",
    )


async def get_llama_parse_agentic_plus(*args, **kwargs) -> LlamaParse:
    return LlamaParse(
        parse_mode="parse_page_with_agent",
        model="anthropic-sonnet-4.0",
        high_res_ocr=True,
        adaptive_long_table=True,
        outlined_table_extraction=True,
        output_tables_as_HTML=True,
        result_type="markdown",
    )


class DocumentProcessingState(BaseModel):
    document_path: str = ""


class DocumentProcessingWorkflow(Workflow):
    @step
    async def choose_document_parsing_mode(
        self, ev: StartEvent, ctx: Context[DocumentProcessingState]
    ) -> (
        ParseDocumentCostEffectiveEvent
        | ParseDocumentAgenticEvent
        | ParseDocumentAgenticPlusEvent
    ):
        async with ctx.store.edit_state() as state:
            state.document_path = ev.document_path
        if ev.parsing_mode == "cost_effective":
            return ParseDocumentCostEffectiveEvent()
        elif ev.parsing_mode == "agentic":
            return ParseDocumentAgenticEvent()
        else:
            return ParseDocumentAgenticPlusEvent()

    @step
    async def parse_document_cost_effective(
        self,
        ev: ParseDocumentCostEffectiveEvent,
        ctx: Context[DocumentProcessingState],
        parser: Annotated[LlamaParse, Resource(get_llama_parse_cost_effective)],
    ) -> StopEvent:
        state = await ctx.store.get_state()
        result = await parser.aparse(state.document_path)
        if isinstance(result, list):
            documents = []
            for r in result:
                documents.extend(await r.aget_markdown_documents())
        else:
            documents = await result.aget_markdown_documents()
        text = "\\n\\n---\\n\\n".join([document.text for document in documents])
        return StopEvent(result=text)

    @step
    async def parse_document_agentic(
        self,
        ev: ParseDocumentCostEffectiveEvent,
        ctx: Context[DocumentProcessingState],
        parser: Annotated[LlamaParse, Resource(get_llama_parse_agentic)],
    ) -> StopEvent:
        state = await ctx.store.get_state()
        result = await parser.aparse(state.document_path)
        if isinstance(result, list):
            documents = []
            for r in result:
                documents.extend(await r.aget_markdown_documents())
        else:
            documents = await result.aget_markdown_documents()
        text = "\\n\\n---\\n\\n".join([document.text for document in documents])
        return StopEvent(result=text)

    @step
    async def parse_document_agentic_plus(
        self,
        ev: ParseDocumentCostEffectiveEvent,
        ctx: Context[DocumentProcessingState],
        parser: Annotated[LlamaParse, Resource(get_llama_parse_agentic_plus)],
    ) -> StopEvent:
        state = await ctx.store.get_state()
        result = await parser.aparse(state.document_path)
        if isinstance(result, list):
            documents = []
            for r in result:
                documents.extend(await r.aget_markdown_documents())
        else:
            documents = await result.aget_markdown_documents()
        text = "\\n\\n---\\n\\n".join([document.text for document in documents])
        return StopEvent(result=text)


async def main(document_path: str, parsing_mode: str) -> None:
    wf = DocumentProcessingWorkflow(
        timeout=1800
    )  # allow processing jobs up to 30 minutes
    result = await wf.run(document_path=document_path, parsing_mode=parsing_mode)
    print(str(result))


if __name__ == "__main__":
    import os
    import asyncio
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument("-p", "--path", help="Document path", required=True)
    parser.add_argument(
        "-m",
        "--mode",
        help="Parsing Mode",
        choices=["cost_effective", "agentic", "agentic_plus"],
        required=False,
        default="agentic",
    )
    args = parser.parse_args()

    if not os.getenv("LLAMA_CLOUD_API_KEY", None):
        raise ValueError(
            "You need to set LLAMA_CLOUD_API_KEY in your environment before using this workflow"
        )

    asyncio.run(main(args.path, args.mode))
