HUMAN_IN_THE_LOOP_CODE = """
from workflows import Workflow, step, Context
from workflows.events import (
    Event,
    StartEvent,
    StopEvent,
    InputRequiredEvent,
    HumanResponseEvent
)

from llama_index.llms.openai import OpenAI

class TopicEvent(StartEvent):
    topic: str

class JokeEvent(Event):
    joke: str

class FeedbackRequiredEvent(InputRequiredEvent):
    joke: str

class HumanFeedbackEvent(HumanResponseEvent):
    approved: bool

class HumanJokeFlow(Workflow):
    llm = OpenAI(model="gpt-4.1")

    @step
    async def generate_joke(self, ev: TopicEvent, ctx: Context) -> JokeEvent:
        topic = ev.topic
        async with ctx.store.edit_state() as state:
            state.topic = ev.topic
        prompt = f"Write your best joke about {topic}."
        response = await self.llm.acomplete(prompt)
        return JokeEvent(joke=str(response))

    @step
    async def give_feedback_on_joke(self, ev: JokeEvent, ctx: Context) -> FeedbackRequiredEvent:
        async with ctx.store.edit_state() as state:
            state.joke = ev.joke
        return FeedbackRequiredEvent(joke=ev.joke)

    @step
    async def collect_human_feedback_event(self, ev: HumanFeedbackEvent, ctx: Context) -> StopEvent | TopicEvent:
        state = await ctx.store.get_state()
        if ev.approved:
            return StopEvent(result=state.joke)
        else:
            return TopicEvent(topic=state.topic) # type: ignore

async def main(topic: str) -> None:
    w = HumanJokeFlow(timeout=60, verbose=False)
    handler = w.run(start_event=TopicEvent(topic=topic))
    async for ev in handler.stream_events():
        if isinstance(ev, FeedbackRequiredEvent):
            print("Joke: " + ev.joke)
            res = input("Approve? [yes/no]: ")
            if res.lower().strip() == "yes":
                handler.ctx.send_event(HumanFeedbackEvent(approved=True)) # type: ignore
            else:
                handler.ctx.send_event(HumanFeedbackEvent(approved=False)) # type: ignore
    result = await handler
    print(str(result))

if __name__ == "__main__":
    import asyncio
    import os
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument("-t", "--topic", required=True, help="Joke Topic")
    args = parser.parse_args()

    if not os.getenv("OPENAI_API_KEY", None):
        raise ValueError("You need to set OPENAI_API_KEY in your environment before using this workflow")

    asyncio.run(main(topic=args.topic))
"""

HUMAN_IN_THE_LOOP_REQUIREMENTS = """
llama-index-workflows
llama-index-llms-openai
"""
