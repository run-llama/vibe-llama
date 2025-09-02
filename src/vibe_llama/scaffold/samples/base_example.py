BASE_EXAMPLE_CODE = """
from workflows import Workflow, step
from workflows.events import (
    Event,
    StartEvent,
    StopEvent,
)

# `pip install llama-index-llms-openai` if you don't already have it
from llama_index.llms.openai import OpenAI


class JokeEvent(Event):
    joke: str


class JokeFlow(Workflow):
    llm = OpenAI()

    @step
    async def generate_joke(self, ev: StartEvent) -> JokeEvent:
        topic = ev.topic

        prompt = f"Write your best joke about {topic}."
        response = await self.llm.acomplete(prompt)
        return JokeEvent(joke=str(response))

    @step
    async def critique_joke(self, ev: JokeEvent) -> StopEvent:
        joke = ev.joke

        prompt = f"Give a thorough analysis and critique of the following joke: {joke}"
        response = await self.llm.acomplete(prompt)
        return StopEvent(result=str(response))

async def main(topic: str) -> None:
    w = JokeFlow(timeout=60, verbose=False)
    result = await w.run(topic=topic)
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

BASE_EXAMPLE_REQUIREMENTS = """
llama-index-workflows
llama-index-llms-openai
"""
