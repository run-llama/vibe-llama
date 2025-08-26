import pytest

from workflows import Workflow, Context
from workflows.context.state_store import InMemoryStateStore
from workflows.errors import WorkflowValidationError
from workflows.events import InputRequiredEvent
from llama_index.core.llms import MockLLM, ChatMessage
from llama_index.core.tools import FunctionTool, BaseTool
from typing import List, Sequence, Any

from src.vibe_llama.docuflows.commons.typed_state import WorkflowState
from src.vibe_llama.docuflows.agent import LlamaVibeWorkflow
from src.vibe_llama.docuflows.agent.utils import handle_slash_command, handle_chat


class MockLLMWithTools(MockLLM):
    async def astream_chat_with_tools(
        self,
        tools: List[BaseTool],
        chat_history: Sequence[ChatMessage],
        allow_parallel_tool_calls: bool,
    ):
        return await self.astream_chat(chat_history)

    def get_tool_calls_from_response(self, r: Any, error_on_no_tool_call: bool):
        return []


@pytest.fixture()
def llm() -> MockLLM:
    return MockLLM(max_tokens=20)


@pytest.fixture()
def llm_with_tools() -> MockLLMWithTools:
    return MockLLMWithTools(max_tokens=20)


@pytest.fixture()
def tools() -> List[BaseTool]:
    return [
        FunctionTool.from_defaults(
            fn=lambda x: print(x),
            name="print_tool",
            description="this tool prints things",
        )
    ]


def test_workflow_basics(llm: MockLLM) -> None:
    assert issubclass(LlamaVibeWorkflow, Workflow)
    try:
        LlamaVibeWorkflow()._validate()
        is_valid = True
    except WorkflowValidationError:
        is_valid = False
    assert is_valid
    wf = LlamaVibeWorkflow(timeout=60, llm=llm)
    assert wf._timeout == 60
    assert wf.llm == llm


@pytest.mark.asyncio
async def test_handle_slash_command() -> None:
    ctx = Context[WorkflowState](LlamaVibeWorkflow())
    ctx._state_store = InMemoryStateStore(initial_state=WorkflowState())  # type: ignore
    retval = await handle_slash_command(ctx=ctx, command="/help")
    assert isinstance(retval, InputRequiredEvent)
    assert retval.prefix == ""


@pytest.mark.asyncio
async def test_handle_chat(
    llm_with_tools: MockLLMWithTools, tools: List[BaseTool]
) -> None:
    ctx = Context[WorkflowState](LlamaVibeWorkflow())
    ctx._state_store = InMemoryStateStore(initial_state=WorkflowState())  # type: ignore
    retval = await handle_chat(ctx, "hello world", llm_with_tools, tools)
    assert isinstance(retval, InputRequiredEvent)
