import pytest

from llama_index.core.llms import MockLLM
from workflows import Context
from workflows.context.state_store import InMemoryStateStore
from workflows.events import InputRequiredEvent

from src.vibe_llama.docuflows.agent.utils import AgentConfig
from src.vibe_llama.docuflows.commons.typed_state import WorkflowState
from src.vibe_llama.docuflows.commons.core import DocumentComplexityAssessment
from src.vibe_llama.docuflows.agent import LlamaVibeWorkflow
from src.vibe_llama.docuflows.handlers.workflow_generation import (
    assess_document_complexity,
    handle_folder_name_input,
    handle_generate_workflow,
)


@pytest.fixture()
def llm() -> MockLLM:
    return MockLLM(max_tokens=20)


@pytest.fixture()
def reference_path() -> str:
    return "data/test/"


@pytest.fixture()
def ctx() -> Context[WorkflowState]:
    agent_config = AgentConfig(project_id="hello", organization_id="hello")
    ctx = Context[WorkflowState](LlamaVibeWorkflow())
    ctx._state_store = InMemoryStateStore(
        initial_state=WorkflowState(config=agent_config)
    )  # type: ignore
    return ctx


@pytest.mark.asyncio
async def test_assess_document_complexity(
    ctx: Context[WorkflowState], llm: MockLLM, reference_path: str
) -> None:
    retval = await assess_document_complexity(
        "edit this workflow", reference_path, llm, ctx
    )
    assert (
        retval.model_dump_json()
        == DocumentComplexityAssessment(
            complexity_level="moderate",
            parse_mode="agentic",
            extract_mode="MULTIMODAL",
            needs_citations=False,
            needs_reasoning=False,
            reasoning="Fallback to moderate complexity due to assessment error",
        ).model_dump_json()
    )


@pytest.mark.asyncio
async def test_handle_folder_name_input(
    ctx: Context[WorkflowState], llm: MockLLM, reference_path: str
) -> None:
    retval = await handle_folder_name_input(
        ctx, user_input="This is an input", default_folder_name=reference_path, llm=llm
    )
    assert isinstance(retval, InputRequiredEvent)


@pytest.mark.asyncio
async def test_handle_generate_workflow(
    ctx: Context[WorkflowState], llm: MockLLM, reference_path: str
) -> None:
    retval = await handle_generate_workflow(
        ctx, "generate a workflow", reference_path, llm
    )
    assert isinstance(retval, InputRequiredEvent)
