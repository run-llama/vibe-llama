import pytest

from workflows import Workflow
from workflows.errors import WorkflowValidationError
from llama_index.core.llms import MockLLM

from src.vibe_llama.docuflows.editing import DiffEditingWorkflow


@pytest.fixture()
def llm() -> MockLLM:
    return MockLLM(max_tokens=20)


def test_workflow_basics(llm: MockLLM) -> None:
    assert issubclass(DiffEditingWorkflow, Workflow)
    try:
        DiffEditingWorkflow(llm=llm)._validate()
        is_valid = True
    except WorkflowValidationError:
        is_valid = False
    assert is_valid
    wf = DiffEditingWorkflow(timeout=60, llm=llm)
    assert wf._timeout == 60
    assert wf.llm == llm
