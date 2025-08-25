import pytest
from pathlib import Path

from llama_index.core.llms import MockLLM
from workflows import Context
from workflows.context.state_store import InMemoryStateStore
from workflows.events import InputRequiredEvent

from src.vibe_llama.docuflows.agent.utils import AgentConfig
from src.vibe_llama.docuflows.commons.typed_state import WorkflowState
from src.vibe_llama.docuflows.agent import LlamaVibeWorkflow
from src.vibe_llama.docuflows.handlers.workflow_testing import (
    handle_test_file_input,
    handle_test_file_selection,
    handle_test_file_validation,
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


@pytest.fixture()
def wf_path() -> str:
    return "data/test/workflow.py"


@pytest.mark.asyncio
async def test_handle_test_file_input(
    ctx: Context[WorkflowState], llm: MockLLM
) -> None:
    retval = await handle_test_file_input(ctx, llm)
    assert isinstance(retval, InputRequiredEvent)
    assert retval.prefix == "Please provide the path to a sample file to test: "


@pytest.mark.asyncio
async def test_handle_test_file_selection(
    ctx: Context[WorkflowState], llm: MockLLM, wf_path: str, tmp_path: Path
) -> None:
    retval = await handle_test_file_selection(ctx, "", [wf_path], str(tmp_path), llm)
    assert isinstance(retval, InputRequiredEvent)
    assert retval.prefix == "Which file would you like to test? "


@pytest.mark.asyncio
async def test_handle_test_file_validation(
    ctx: Context[WorkflowState], llm: MockLLM, wf_path: str
):
    retval = await handle_test_file_validation(
        ctx, wf_path.replace("workflow", "worflow"), llm, {"pass": True}
    )
    assert isinstance(retval, InputRequiredEvent)
    assert retval.prefix == "Please provide a valid file path to test: "
