from pydantic import BaseModel, Field
from workflows import Workflow, step, Context
from workflows.events import (
    StartEvent,
    StopEvent,
    InputRequiredEvent,
    HumanResponseEvent,
)
from workflows.resource import Resource
from typing import Annotated
from llama_cloud_services import LlamaExtract
from llama_cloud_services.extract import ExtractConfig, ExtractMode


class InvoiceData(BaseModel):
    invoice_date: str = Field(description="Date on the invoice")
    customer: str = Field(description="Customer reported on the invoice")
    amount_due: float = Field(description="Amount due")


class FeedbackRequiredEvent(InputRequiredEvent):
    extraction_result: str


class HumanFeedbackEvent(HumanResponseEvent):
    approved: bool


async def get_invoice_extractor(*args, **kwargs):
    return LlamaExtract()


class InvoiceExtractWorkflow(Workflow):
    @step
    async def invoice_extraction(
        self,
        ev: StartEvent,
        ctx: Context,
        extractor: Annotated[LlamaExtract, Resource(get_invoice_extractor)],
    ) -> FeedbackRequiredEvent:
        async with ctx.store.edit_state() as state:
            state.extraction_mode = ev.extraction_mode
            state.path = ev.path

        if ev.extraction_mode == "base":
            config = ExtractConfig(
                extraction_mode=ExtractMode.FAST,
                high_resolution_mode=False,  # Better OCR accuracy
                invalidate_cache=False,  # Bypass cached results
                cite_sources=False,  # Enable source citations
                use_reasoning=False,  # Enable reasoning (not in FAST mode)
                confidence_scores=False,  # MULTIMODAL/PREMIUM only
            )
        elif ev.extraction_mode == "advanced":
            config = ExtractConfig(
                extraction_mode=ExtractMode.MULTIMODAL,
                high_resolution_mode=True,  # Better OCR accuracy
                invalidate_cache=False,  # Bypass cached results
                cite_sources=False,  # Enable source citations
                use_reasoning=True,  # Enable reasoning (not in FAST mode)
                confidence_scores=False,  # MULTIMODAL/PREMIUM only
            )
        else:
            config = ExtractConfig(
                extraction_mode=ExtractMode.PREMIUM,
                high_resolution_mode=True,  # Better OCR accuracy
                invalidate_cache=False,  # Bypass cached results
                cite_sources=True,  # Enable source citations
                use_reasoning=True,  # Enable reasoning (not in FAST mode)
                confidence_scores=True,  # MULTIMODAL/PREMIUM only
            )

        result = await extractor.aextract(
            data_schema=InvoiceData, config=config, files=[ev.path]
        )
        extracted_data: list[InvoiceData] = []
        if isinstance(result, list):
            for r in result:
                extracted_data.append(InvoiceData.model_validate(r.data))
        else:
            extracted_data.append(InvoiceData.model_validate(result.data))
        async with ctx.store.edit_state() as state:
            state.extraction_result = "\\n\\n---\\n\\n".join(
                [
                    f"Invoice Date: {d.invoice_date}\\nCustomer: {d.customer}\\nAmount Due: {d.amount_due}"
                    for d in extracted_data
                ]
            )
        return FeedbackRequiredEvent(
            extraction_result="\\n\\n---\\n\\n".join(
                [
                    f"Invoice Date: {d.invoice_date}\\nCustomer: {d.customer}\\nAmount Due: {d.amount_due}"
                    for d in extracted_data
                ]
            )
        )

    @step
    async def human_feedback(
        self, ev: HumanFeedbackEvent, ctx: Context
    ) -> StopEvent | StartEvent:
        state = await ctx.store.get_state()
        if ev.approved:
            return StopEvent(result=state.extraction_result)
        else:
            return StartEvent(path=state.path, extraction_mode=state.extraction_mode)  # type: ignore


async def main(path: str, extraction_mode: str) -> None:
    w = InvoiceExtractWorkflow(timeout=1800, verbose=False)
    handler = w.run(path=path, extraction_mode=extraction_mode)
    async for ev in handler.stream_events():
        if isinstance(ev, FeedbackRequiredEvent):
            print("Extraction Result:\\n\\n" + ev.extraction_result + "\\n\\n")
            res = input("Approve? [yes/no]: ")
            if res.lower().strip() == "yes":
                handler.ctx.send_event(HumanFeedbackEvent(approved=True))  # type: ignore
            else:
                handler.ctx.send_event(HumanFeedbackEvent(approved=False))  # type: ignore
    result = await handler
    print(str(result))


workflow = InvoiceExtractWorkflow(timeout=None)

if __name__ == "__main__":
    import asyncio
    import os
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument(
        "-p", "--path", required=True, help="Path to the invoice to extract"
    )
    parser.add_argument(
        "-m",
        "--mode",
        required=True,
        help="Extraction mode",
        choices=["base", "advanced", "premium"],
    )
    args = parser.parse_args()

    if not os.getenv("LLAMA_CLOUD_API_KEY", None):
        raise ValueError(
            "You need to set LLAMA_CLOUD_API_KEY in your environment before using this workflow"
        )

    asyncio.run(main(path=args.path, extraction_mode=args.mode))
