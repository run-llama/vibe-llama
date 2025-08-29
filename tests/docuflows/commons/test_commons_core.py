import pytest
import os
import shutil
from pathlib import Path

from typing import Tuple
from workflows import Context
from workflows.context.state_store import InMemoryStateStore
from llama_index.core.llms import MockLLM

from src.vibe_llama.docuflows.agent import LlamaVibeWorkflow
from src.vibe_llama.docuflows.commons.typed_state import WorkflowState
from src.vibe_llama.docuflows.commons.core import (
    _send_event,
    load_context_files,
    load_reference_files,
    extract_python_code,
    generate_workflow,
    generate_runbook,
    save_workflow,
    save_runbook,
    create_workflow_folder,
)


@pytest.fixture()
def llm() -> MockLLM:
    return MockLLM(max_tokens=20)


@pytest.fixture()
def dir_path() -> str:
    return "data/test"


@pytest.fixture()
def code() -> Tuple[str, str]:
    return (
        """
This is some python code:

```python
def hello():
    print('Hello!')
```
""",
        """def hello():
    print('Hello!')""",
    )


@pytest.fixture()
def ctx() -> Context[WorkflowState]:
    ctx = Context[WorkflowState](LlamaVibeWorkflow())
    ctx._state_store = InMemoryStateStore(initial_state=WorkflowState())  # type: ignore
    return ctx


def test__send_event(ctx: Context[WorkflowState]) -> None:
    try:
        _send_event(ctx, "hello")
        success = True
    except Exception:
        success = False
    assert success


@pytest.mark.asyncio
async def test_load_context_files(ctx: Context[WorkflowState]) -> None:
    if os.path.exists(".vibe-llama/rules"):
        shutil.rmtree(".vibe-llama/rules")
    retval = await load_context_files(ctx)
    with open("documentation/llama-index-workflows.md") as f:
        wfs = f.read()
    with open("documentation/llamacloud.md") as s:
        lcs = s.read()
    assert wfs in retval
    assert lcs in retval


@pytest.mark.asyncio
async def test_load_reference_files(dir_path: str, ctx: Context[WorkflowState]) -> None:
    with pytest.raises(RuntimeError):
        await load_reference_files(dir_path, ctx=ctx)


def test_extract_python_code(code: Tuple[str, str]) -> None:
    assert extract_python_code(code[0]) == code[1]


@pytest.mark.asyncio
async def test_generate_workflow(dir_path: str, ctx: Context[WorkflowState]) -> None:
    with pytest.raises(RuntimeError):
        await generate_workflow(
            user_task="hello", reference_files_path=dir_path, ctx=ctx
        )


@pytest.mark.asyncio
async def test_generate_runbook(
    llm: MockLLM, code: Tuple[str, str], ctx: Context[WorkflowState]
) -> None:
    retval = await generate_runbook(
        code[1], user_task="This is a task", ctx=ctx, llm=llm
    )
    assert isinstance(retval, str)


def test_save_workflow(
    tmp_path: Path, code: Tuple[str, str], ctx: Context[WorkflowState]
) -> None:
    save_path = tmp_path / "test.py"
    save_workflow(code[1], str(save_path), ctx)
    with open(save_path, "r") as f:
        content = f.read()
    assert content == code[1]


def test_save_runbook(
    tmp_path: Path, code: Tuple[str, str], ctx: Context[WorkflowState]
) -> None:
    save_path = tmp_path / "test.md"
    save_runbook(code[0], str(save_path), ctx)
    with open(save_path, "r") as f:
        content = f.read()
    assert content == code[0]


def test_create_workflow_folder():
    folder = create_workflow_folder("data/test/")
    assert Path(folder).is_dir()
    os.removedirs(folder)
