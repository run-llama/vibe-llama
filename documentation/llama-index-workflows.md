# High-level workflows doc for LLMs and Humans

# LlamaIndex Workflows - A Practical Compendium

## 0. Introduction

`llama-index-workflows` are an event-driven, async-first, step-based way to provide and control the execution flow of applications aimed at intelligent automation (AI agents, for instance).

## 1. Installation

You can install workflows using `pip` with:

```bash
pip install llama-index-workflows
```

or add them to a `uv` project with:

```bash
uv add llama-index-workflows
```

Once you installed them, you can use them within your code under the `workflows` namespace:

```python
from workflows import Workflow, Context, step
```

## 2. The Core Components

### 2.1 Event

`Event`is the base class for designing the events that will drive your workflow. There are five types of events:

- `StartEvent` : it’s the input event that kicks off the workflow
- `Event` : base class from which all intermediate workflow events should inherit
- `StopEvent` : last event of the workflow, should contain the output. The workflow will stop as soon as the event is returned from a step
- `InputRequiredEvent`: this event is emitted when an external input is required
- `HumanResponseEvent`: this event is emitted when a human response is returned.

> `InputRequiredEvent` and `HumanResponseEvent` are often coupled and often used to build human-in-the-loop (HITL) workflows. See the _Design Patterns_ section to gain more insight on this.

You should design the workflow around these events, and they are highly customizable (you can subclass them to add specific data transferred with them):

```python
from workflows.events import Event, StartEvent, StopEvent


class CustomStartEvent(StartEvent):
    message: str


class GreetingEvent(Event):
    greeting: str
    is_formal: bool
    time: float


class OutputEvent(StopEvent):
    output: list[str]
```

Events behave like Pydantic `BaseModel` subclasses, so their attributes can be set, modified and fetched very easily:

```python
from workflows.events import Event


class SomeEvent(Event):
    data: str


event = SomeEvent(data="hello world")
event.data = "hello universe"
print(event.data)
```

### 2.2 Context

Context is arguably the most important piece of workflows, since it holds:

- Control over statefulness execution
- Control over stored information
- Control over events emission and collection

**2.2.a Stateful execution**

Context contains a State, which is a representation of the current state of the execution flow. By default, you can access to the state and edit its property with these operations:

```python
from workflows import Workflow, Context, step


class ExampleWorkflow(Workflow):
    @step
    async def modify_state(self, ev: StartEvent, ctx: Context) -> SecondEvent:
        async with ctx.store.edit_state() as state:
            state.age = ev.age
            state.username = ev.username
            state.email = ev.email
        ## rest of the step implementation
```

You can also specify a customized model for the state, and initialize the context with that:

```python
from workflows import Workflow, Context, step
from pydantic import BaseModel


class WorkflowState(BaseModel):
    username: str
    email: str
    age: int


class ExampleWorkflow(Workflow):
    @step
    async def modify_state(
        self, ev: StartEvent, ctx: Context[WorkflowState]
    ) -> SecondEvent:
        async with ctx.store.edit_state() as state:
            state.age = ev.age
            state.username = ev.username
            state.email = ev.email
        ## rest of the step implementation
```

It is advisable to use a customized State to avoid unexpected behaviors.

**2.2.b Store**

Store is, by default, a dict-like object contained in the Context: it is mainly used for more long-term storage, and you can get and set values in this way:

```python
from workflows import Workflow, Context, step


class ExampleWorkflow(Workflow):
    @step
    async def get_set_store(self, ev: StartEvent, ctx: Context) -> SecondEvent:
        n_iterations = ctx.store.get("n_iterations", default=None)
        if n_iterations:
            n_iterations += 1
            ctx.store.set("n_iterations", n_iterations)
        else:
            ctx.store.set("n_iterations", 1)
        ## rest of the step implementation
```

Unless motivated by specific reasons, it is advisable to use `state` over `store` .

**2.2.c Emitting and collecting events**

Context can be used also to emit and collect events, as well as writing them to the event stream.

```python
class ParallelFlow(Workflow):
    @step
    async def start(self, ctx: Context, ev: StartEvent) -> StepTwoEvent | None:
        ctx.send_event(StepTwoEvent(query="Query 1"))

    @step
    async def step_two(self, ctx: Context, ev: StepTwoEvent) -> StopEvent:
        print("Running slow query ", ev.query)
        await asyncio.sleep(random.randint(1, 5))

        return StopEvent(result=ev.query)
```

As you can see, emitting an event with `ctx.send_event` sends it directly to the step that receive that event as input.

You can also implement a fan-in/fan-out pattern sending out event, having one or more worker steps that process those events, and then collecting the events with `ctx.collect_events` in a last step and emitting an output:

```python
class ConcurrentFlow(Workflow):
    @step
    async def start(
        self, ctx: Context, ev: StartEvent
    ) -> StepAEvent | StepBEvent | StepCEvent | None:
        ctx.send_event(StepAEvent(query="Query 1"))
        ctx.send_event(StepBEvent(query="Query 2"))
        ctx.send_event(StepCEvent(query="Query 3"))

    @step
    async def step_a(self, ctx: Context, ev: StepAEvent) -> StepACompleteEvent:
        print("Doing something A-ish")
        return StepACompleteEvent(result=ev.query)

    @step
    async def step_b(self, ctx: Context, ev: StepBEvent) -> StepBCompleteEvent:
        print("Doing something B-ish")
        return StepBCompleteEvent(result=ev.query)

    @step
    async def step_c(self, ctx: Context, ev: StepCEvent) -> StepCCompleteEvent:
        print("Doing something C-ish")
        return StepCCompleteEvent(result=ev.query)

    @step
    async def step_three(
        self,
        ctx: Context,
        ev: StepACompleteEvent | StepBCompleteEvent | StepCCompleteEvent,
    ) -> StopEvent:
        print("Received event ", ev.result)

        # wait until we receive 3 events
        if (
            ctx.collect_events(
                ev,
                [StepCCompleteEvent, StepACompleteEvent, StepBCompleteEvent],
            )
            is None
        ):
            return None

        # do something with all 3 results together
        return StopEvent(result="Done")
```

**2.2.d Serializing Context**

The context can be serialized into a dict. This is useful for saving state between `.run()` calls and letting steps access state store variables from previous runs, or even checkpointing state as a workflow is running.

The context is bound to a specific workflow, and tracks all the inner state and machinery needed for the runtime of the workflow.

```python
from workflows import Context

w = MyWorkflow()
ctx = Context(w)

result = await w.run(..., ctx=ctx)
# run again with access to previous state
result = await w.run(..., ctx=ctx)

# Serialize
ctx_dict = ctx.to_dict()

# Re-create
restored_ctx = Context.from_dict(w, ctx_dict)
result = await w.run(..., ctx=ctx)
```

Context serialization relies on your workflow events and workflow state store containing serializable data. If you store arbitrary objects, or don’t leverage pydantic functionalities to control serialization of state/events, you may encounter errors.

### 2.3 Resources

Resources are external dependencies injected into workflow steps. Use `Annotated[Type, Resource(factory_function)]` in step parameters to inject them.

**Example:**

```python
from workflows.resource import Resource
from llama_index.core.memory import Memory


def get_memory(*args, **kwargs):
    return Memory.from_defaults("user_id_123", token_limit=60000)


class WorkflowWithResource(Workflow):
    @step
    async def first_step(
        self,
        ev: StartEvent,
        memory: Annotated[Memory, Resource(get_memory)],
    ) -> SecondEvent:
        await memory.aput(ChatMessage(role="user", content="First step"))
        return SecondEvent(msg="Input for step 2")

    @step
    async def second_step(
        self, ev: SecondEvent, memory: Annotated[Memory, Resource(get_memory)]
    ) -> StopEvent:
        await memory.aput(ChatMessage(role="user", content=ev.msg))
        return StopEvent(result="Messages stored")
```

**Key Points:**

- Factory function return type must match declared type
- Resources are shared across steps by default (cached)
- Use `Resource(factory_func, cache=False)` to avoid steps sharing the same resource

### 2.4 The Workflow

There have been already several examples that implemented the `Workflow` class, but let’s understand it better:

- When you want to create a workflow, that has to be a subclass of the `Workflow` class
- Each of the functions of the workflow representing a step must be decorated with the `@step` decorator
- Each of the functions of the workflow must take at least an event type as an input and emit at least an event type as an output, although it is also allowed to output None. If these rules are not respected, you will encounter a validation error.
- Workflows can have linear, parallel/concurrent or cyclic execution patterns
- Every workflow instance has a timeout (by default 45 seconds): remember to set it at a higher value when needed by passing `timeout=Nseconds` when initializing your workflow (as in `wf = MyWorkflow(timeout=300)`)

Let’s see a complete example of a workflow:

```python
from workflows import Workflow, step
from workflows.events import Event, StartEvent, StopEvent

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


w = JokeFlow(timeout=60, verbose=False)
result = await w.run(topic="pirates")
print(str(result))
```

As you can see, running a workflow is an asynchronous operation. You can also create an asynchronous iterator over the events produced by the workflow (you need to explicitly emit them with `ctx.write_event_to_stream` within the workflow) and read these events _while_ they are produced:

```python
from workflows import Workflow, step, Context
from workflows.events import Event, StartEvent, StopEvent

# `pip install llama-index-llms-openai` if you don't already have it
from llama_index.llms.openai import OpenAI


class JokeEvent(Event):
    joke: str


class JokeFlow(Workflow):
    llm = OpenAI()

    @step
    async def generate_joke(self, ev: StartEvent, ctx: Context) -> JokeEvent:
        topic = ev.topic

        prompt = f"Write your best joke about {topic}."
        response = await self.llm.acomplete(prompt)
        ctx.write_event_to_stream(JokeEvent(joke=str(response)))
        return JokeEvent(joke=str(response))

    @step
    async def critique_joke(self, ev: JokeEvent, ctx: Context) -> StopEvent:
        joke = ev.joke

        prompt = f"Give a thorough analysis and critique of the following joke: {joke}"
        response = await self.llm.acomplete(prompt)
        ctx.write_event_to_stream(StopEvent(result=str(response)))
        return StopEvent(result=str(response))


async def main():
    w = JokeFlow(timeout=60, verbose=False)
    handler = w.run(topic="pirates")
    async for event in handler.stream_events():
        if isinstance(event, JokeEvent):
            print("Produced joke:", event.joke)

    result = await handler
    print(str(result))


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
```

## 3. Design Patterns

### 3.1 Human-In-The-Loop

Workflows support human-in-the-loop patterns using `InputRequiredEvent` and `HumanResponseEvent` during event streaming.

**Basic Implementation:**

```python
from workflows.events import InputRequiredEvent, HumanResponseEvent


class HumanInTheLoopWorkflow(Workflow):
    @step
    async def step1(self, ev: StartEvent) -> InputRequiredEvent:
        return InputRequiredEvent(prefix="Enter a number: ")

    @step
    async def step2(self, ev: HumanResponseEvent) -> StopEvent:
        return StopEvent(result=ev.response)


workflow = HumanInTheLoopWorkflow()
handler = workflow.run()

async for event in handler.stream_events():
    if isinstance(event, InputRequiredEvent):
        response = input(event.prefix)
        handler.ctx.send_event(HumanResponseEvent(response=response))

final_result = await handler
```

**Pausable Implementation:**
You can break out of the loop and resume later:

```python
handler = workflow.run()

# Pause at human input
async for event in handler.stream_events():
    if isinstance(event, InputRequiredEvent):
        break

# Handle response
response = input(event.prefix)
handler.ctx.send_event(HumanResponseEvent(response=response))

# Resume workflow
async for event in handler.stream_events():
    continue

final_result = await handler
```

The workflow waits for `HumanResponseEvent` emission and supports flexible input handling (input(), websockets, async state, etc.).

### 3.2 Branching and Looping

Workflows enable branching and looping logic more simply and flexibly than graph-based approaches.

**3.2.a Loops**

Create loops by adding custom event types and conditional returns:

```python
class LoopEvent(Event):
    loop_output: str


@step
async def step_one(self, ev: StartEvent | LoopEvent) -> FirstEvent | LoopEvent:
    if random.randint(0, 1) == 0:
        print("Bad thing happened")
        return LoopEvent(loop_output="Back to step one.")
    else:
        print("Good thing happened")
        return FirstEvent(first_output="First step complete.")
```

You can create loops from any step to any other step by defining appropriate event and return types.

**3.2.b Branches**

Branch workflows by conditionally returning different events:

```python
class BranchA1Event(Event):
    payload: str


class BranchA2Event(Event):
    payload: str


class BranchB1Event(Event):
    payload: str


class BranchB2Event(Event):
    payload: str


class BranchWorkflow(Workflow):
    @step
    async def start(self, ev: StartEvent) -> BranchA1Event | BranchB1Event:
        if random.randint(0, 1) == 0:
            return BranchA1Event(payload="Branch A")
        else:
            return BranchB1Event(payload="Branch B")

    @step
    async def step_a1(self, ev: BranchA1Event) -> BranchA2Event:
        return BranchA2Event(payload=ev.payload)

    @step
    async def step_b1(self, ev: BranchB1Event) -> BranchB2Event:
        return BranchB2Event(payload=ev.payload)

    @step
    async def step_a2(self, ev: BranchA2Event) -> StopEvent:
        return StopEvent(result="Branch A complete.")

    @step
    async def step_b2(self, ev: BranchB2Event) -> StopEvent:
        return StopEvent(result="Branch B complete.")
```

You can combine branches and loops in any order. Later sections cover running multiple branches in parallel using `send_event` and synchronizing them with `collect_events`.

### 3.3 Fan in/Fan out

Using async concurrency, users can dispatch multiple events at once, run work concurrently, and collecting the results. With workflows, this happens using the `send_event` and `collect_events` methods.

```python
class ProcessEvent(Event):
    pass


class ResultEvent(Event):
    pass


class FanInFanOut(Workflow):
    @step
    def init_run(self, ctx: Context, ev: StartEvent) -> ProcessEvent:
        await ctx.store.set("num_to_collect", len(ev.items))
        for item in ev.items:
            ctx.send_event(ProcessEvent())

    @step
    def process(self, ev: ProcessEvent) -> ResultEvent:
        await some_work()
        return ResultEvent()

    @step
    def finalize(self, ctx: Context, ev: ResultEvent) -> StopEvent | None:
        num_to_collect = await ctx.store.get("num_to_collect")
        events = ctx.collect_events(ev, [ResultEvent] * num_to_collect)
        if events is None:
            # Not enough collected yet
            return None

        await finalize_results(events)
        return StopEvent(result="Done!")
```

The `init_run` step emits several `ProcessEvent`s. The step signature is still annotated that it returns `ProcessEvent` even though it doesn't technically, in order to help validate the workflow.

`finalize()` will be triggered each time a `ResultEvent` comes in, and will only complete once all events are present.
