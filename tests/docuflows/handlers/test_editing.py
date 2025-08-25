import pytest

from llama_index.core.llms import MockLLM
from workflows import Context
from workflows.context.state_store import InMemoryStateStore
from workflows.events import InputRequiredEvent

from src.vibe_llama.docuflows.agent.utils import AgentConfig
from src.vibe_llama.docuflows.commons.typed_state import WorkflowState
from src.vibe_llama.docuflows.agent import LlamaVibeWorkflow
from src.vibe_llama.docuflows.handlers.workflow_editing import (
    handle_edit_workflow,
    handle_generate_runbook_after_diff,
    interpret_user_intent,
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
async def test_handle_edit_workflow(ctx: Context[WorkflowState], llm: MockLLM) -> None:
    retval = await handle_edit_workflow(ctx, "edit this workflow", llm)
    assert isinstance(retval, InputRequiredEvent)


@pytest.mark.asyncio
async def test_handle_generate_runbook_after_diff(
    ctx: Context[WorkflowState], llm: MockLLM
) -> None:
    retval = await handle_generate_runbook_after_diff(ctx, llm)
    assert isinstance(retval, InputRequiredEvent)


@pytest.mark.asyncio
async def test_interpret_user_intent(llm: MockLLM) -> None:
    retval = await interpret_user_intent("what is my intent?", llm)
    assert isinstance(retval, str)
