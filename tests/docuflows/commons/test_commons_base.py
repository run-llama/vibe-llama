import pytest
import uuid

from src.vibe_llama.docuflows.commons import (
    validate_reference_path,
    validate_uuid,
    validate_workflow_path,
    clean_file_path,
    CLIFormatter,
)
from rich.text import Text
from rich.padding import Padding
from rich.syntax import Syntax
from rich.console import Group
from rich.markdown import Markdown


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
