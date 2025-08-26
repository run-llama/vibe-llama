import pytest

from llama_index.core.llms import MockLLM
from workflows import Context
from workflows.context.state_store import InMemoryStateStore
from workflows.events import InputRequiredEvent

from src.vibe_llama.docuflows.agent.utils import AgentConfig
from src.vibe_llama.docuflows.commons.typed_state import WorkflowState
from src.vibe_llama.docuflows.agent import LlamaVibeWorkflow
from src.vibe_llama.docuflows.handlers.workflow_help import (
    handle_answer_question,
    handle_help,
)


@pytest.fixture()
def llm() -> MockLLM:
    return MockLLM(max_tokens=20)


@pytest.fixture()
def ctx() -> Context[WorkflowState]:
    agent_config = AgentConfig(project_id="hello", organization_id="hello")
    ctx = Context[WorkflowState](LlamaVibeWorkflow())
    ctx._state_store = InMemoryStateStore(
        initial_state=WorkflowState(config=agent_config)
    )  # type: ignore
    return ctx


@pytest.mark.asyncio
async def test_handle_help(ctx: Context[WorkflowState]) -> None:
    retval = await handle_help(ctx)
    assert isinstance(retval, InputRequiredEvent)
    assert retval.prefix == "\nWhat would you like to do? "


@pytest.mark.asyncio
async def test_handle_answer_question(
    ctx: Context[WorkflowState], llm: MockLLM
) -> None:
    retval = await handle_answer_question(ctx, "hey, who are you?", llm)
    assert isinstance(retval, InputRequiredEvent)
