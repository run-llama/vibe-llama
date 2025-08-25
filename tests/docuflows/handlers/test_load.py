import pytest

from workflows import Context
from workflows.context.state_store import InMemoryStateStore
from workflows.events import InputRequiredEvent

from src.vibe_llama.docuflows.agent.utils import AgentConfig
from src.vibe_llama.docuflows.commons.typed_state import WorkflowState
from src.vibe_llama.docuflows.agent import LlamaVibeWorkflow
from src.vibe_llama.docuflows.handlers.workflow_load import handle_load_workflow


@pytest.fixture()
def ctx() -> Context[WorkflowState]:
    agent_config = AgentConfig(project_id="hello", organization_id="hello")
    ctx = Context[WorkflowState](LlamaVibeWorkflow())
    ctx._state_store = InMemoryStateStore(
        initial_state=WorkflowState(config=agent_config)
    )  # type: ignore
    return ctx


@pytest.fixture()
def wf_path() -> str:
    return "data/test/workflow.py"


@pytest.mark.asyncio
async def test_handle_load_workflow(ctx: Context[WorkflowState], wf_path: str):
    retval = await handle_load_workflow(ctx, wf_path)
    assert isinstance(retval, InputRequiredEvent)
    assert retval.prefix == (
        "\nWorkflow loaded! You can now:\n"
        "- Edit the workflow\n"
        "- Test it on sample data\n"
        "- Ask questions about it\n"
        "- Generate a new workflow\n"
        "- Load a different workflow\n"
        "What would you like to do? "
    )
