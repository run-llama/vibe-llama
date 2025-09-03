from llama_index.llms.google_genai import GoogleGenAI
from llama_index.core.llms import ChatMessage
from google.genai.types import Tool, GenerateContentConfig, UrlContext
from typing import Annotated
from pydantic import BaseModel

from workflows import Workflow, step, Context
from workflows.events import Event, StartEvent, StopEvent
from workflows.resource import Resource


model_id = "gemini-2.5-flash"

url_context_tool = Tool(url_context=UrlContext())

config = GenerateContentConfig(
    tools=[url_context_tool],
    response_modalities=["TEXT"],
)


class URLState(BaseModel):
    processed_urls: int = 0
    final_content: str = ""


async def get_llm(*args, **kwargs) -> GoogleGenAI:
    return GoogleGenAI(model=model_id, generation_config=config)


class URLReadEvent(Event):
    url: str


class URLContentEvent(Event):
    content: str


class WebScrapeWorkflow(Workflow):
    @step
    async def process_urls(
        self, ev: StartEvent, ctx: Context[URLState]
    ) -> URLReadEvent | None:
        async with ctx.store.edit_state() as state:
            state.processed_urls = len(ev.urls)
        for url in ev.urls:
            ctx.send_event(URLReadEvent(url=url))

    @step
    async def get_url_content(
        self,
        ev: URLReadEvent,
        llm: Annotated[GoogleGenAI, Resource(get_llm)],
        ctx: Context[URLState],
    ) -> URLContentEvent:
        response = llm.chat(
            [
                ChatMessage(
                    role="user",
                    content=f"Can you please summarize the context of this URL: {ev.url}",
                )
            ]
        )
        async with ctx.store.edit_state() as state:
            state.final_content += (
                f"### Summary for {ev.url}\\n\\n{response.message.content}\\n\\n"
            )
        return URLContentEvent(content=response.message.content or "")

    @step
    async def finalize(
        self, ev: URLContentEvent, ctx: Context[URLState]
    ) -> StopEvent | None:
        state = await ctx.store.get_state()
        events = ctx.collect_events(ev, [URLContentEvent] * state.processed_urls)
        if events:
            return StopEvent(result=state.final_content)


async def main(urls: list[str]):
    w = WebScrapeWorkflow(timeout=300)
    result = await w.run(urls=urls)
    print(str(result))


if __name__ == "__main__":
    import os
    import asyncio
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument(
        "--url",
        help="URLs whose content needs to be summarised",
        required=True,
        action="append",
    )
    args = parser.parse_args()

    if not os.getenv("GOOGLE_API_KEY", None):
        raise ValueError(
            "You need to set GOOGLE_API_KEY in your environment before using this workflow"
        )

    asyncio.run(main(args.url))
