import pytest

from workflows import Context
from workflows.context.state_store import InMemoryStateStore
from workflows.events import InputRequiredEvent

from src.vibe_llama.docuflows.agent.utils import AgentConfig
from src.vibe_llama.docuflows.commons.typed_state import WorkflowState
from src.vibe_llama.docuflows.agent import LlamaVibeWorkflow
from src.vibe_llama.docuflows.handlers.workflow_config import (
    handle_configuration,
    handle_reconfigure,
    handle_show_config,
)


@pytest.fixture()
def ctx() -> Context[WorkflowState]:
    agent_config = AgentConfig(project_id="hello", organization_id="hello")
    ctx = Context[WorkflowState](LlamaVibeWorkflow())
    ctx._state_store = InMemoryStateStore(
        initial_state=WorkflowState(config=agent_config)
    )  # type: ignore
    return ctx


@pytest.mark.asyncio
async def test_handle_configuration(ctx: Context[WorkflowState]) -> None:
    retval = await handle_configuration(ctx, user_input="hello")
    assert retval is None


@pytest.mark.asyncio
async def test_handle_reconfigure(ctx: Context[WorkflowState]) -> None:
    retval = await handle_reconfigure(ctx)
    assert isinstance(retval, InputRequiredEvent)


@pytest.mark.asyncio
async def test_handle_show_config(ctx: Context[WorkflowState]) -> None:
    retval = await handle_show_config(ctx)
    assert isinstance(retval, InputRequiredEvent)
