import pytest
import uuid
import os

from src.vibe_llama.docuflows.commons import (
    validate_reference_path,
    validate_uuid,
    validate_workflow_path,
    clean_file_path,
    is_file_path,
    CLIFormatter,
    local_venv,
    install_deps,
)
from rich.text import Text
from rich.padding import Padding
from rich.syntax import Syntax
from rich.console import Group
from rich.markdown import Markdown

SKIP_CONDITION = not os.getenv("IS_NOT_CI_ENV", None)
VENV_FAILED = False


@pytest.fixture()
def reference_path() -> str:
    return "data/test/file.txt"


@pytest.fixture()
def wf_path() -> str:
    return "data/test/workflow.py"


@pytest.fixture()
def test_text() -> str:
    return "def hello():\n\tprint('hello!')\n"


def test_validate_reference_path(reference_path: str) -> None:
    truth, path, val = validate_reference_path(reference_path)
    assert truth
    assert not path and not val


def test_validate_workflow_path(wf_path: str) -> None:
    truth, path, val = validate_workflow_path(wf_path)
    assert truth
    assert path == wf_path
    assert not val


def test_validate_uuid() -> None:
    test_uuid = str(uuid.uuid4())
    assert validate_uuid(test_uuid)


def test_clean_file_path(reference_path: str) -> None:
    path1 = f"./{reference_path}"
    path2 = f"@/{reference_path}"
    assert "./" not in clean_file_path(path1)
    assert "@" not in clean_file_path(path2)


def test_is_file_path() -> None:
    """Test file path vs command detection"""
    # File paths should return True
    assert is_file_path("/Users/user/documents/file.pdf")
    assert is_file_path("@data/test.pdf")
    assert is_file_path("/absolute/path/with/file.txt")

    # Commands should return False
    assert not is_file_path("/help")
    assert not is_file_path("/config")
    assert not is_file_path("/model")


def test_clean_file_path_with_at_symbol() -> None:
    """Test @ symbol removal in file paths"""
    assert clean_file_path("@data/test.pdf").endswith("data/test.pdf")
    assert clean_file_path("/absolute/path.pdf") == os.path.abspath(
        "/absolute/path.pdf"
    )
    assert "@" not in clean_file_path("@some/file.txt")


def test_cli_formatter(test_text: str, reference_path: str) -> None:
    formatter = CLIFormatter()
    assert isinstance(formatter.agent_response(test_text), (Text, Padding))
    assert isinstance(formatter.code(test_text), Syntax)
    assert isinstance(formatter.code_output(test_text), Group)
    assert isinstance(formatter.diff_preview(test_text), Syntax)
    assert isinstance(formatter.error(test_text), Text)
    assert isinstance(formatter.file_list([reference_path]), Group)
    assert isinstance(formatter.heading(test_text), Text)
    assert isinstance(formatter.important_text(test_text), Text)
    assert isinstance(formatter.indented_text(test_text), Text)
    assert isinstance(formatter.info(test_text), Text)
    assert isinstance(formatter.markdown(test_text), Markdown)
    assert isinstance(formatter.runbook_output(test_text), Group)
    assert isinstance(formatter.subtle_text(test_text), Text)
    assert isinstance(formatter.status_update(test_text), Text)
    assert isinstance(formatter.workflow_summary(test_text), Group)
    assert isinstance(formatter.success(test_text), Text)
    assert isinstance(formatter.tool_action(test_text), Text)
    assert isinstance(formatter._get_terminal_width(), int)


@pytest.mark.asyncio
@pytest.mark.skipif(condition=SKIP_CONDITION, reason="Avoid venv in CI environment")
async def test_local_venv() -> None:
    global VENV_FAILED
    try:
        await local_venv()
        success = True
    except ValueError:
        success = False
        VENV_FAILED = True
    assert success


@pytest.mark.asyncio
@pytest.mark.skipif(
    condition=SKIP_CONDITION or VENV_FAILED,
    reason="Avoid deps installation in CI environment or no available venv",
)
async def test_install_deps() -> None:
    with open(".vibe-llama/requirements.txt", "w") as w:
        w.write("termcolor")
    try:
        await install_deps()
        success = True
    except ValueError:
        success = False
    assert success
