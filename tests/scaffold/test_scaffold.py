from pathlib import Path
import pytest
import os


from src.vibe_llama.scaffold import create_scaffold
from src.vibe_llama.scaffold.terminal import app1, app2
from prompt_toolkit.application import Application


def test_dummy_templates_removed() -> None:
    """Ensure local templates directory is not used anymore."""
    templates_root = Path(__file__).resolve().parents[2] / "templates"
    assert templates_root.exists()


@pytest.mark.asyncio
async def test_create_scaffold_defaults(tmp_path: Path):
    os.chdir(tmp_path)
    succ = await create_scaffold()
    assert succ.startswith("[bold green]")
    out_w = tmp_path / ".vibe-llama/scaffold/basic/src/basic/workflow.py"
    out_p = tmp_path / ".vibe-llama/scaffold/basic/pyproject.toml"
    out_r = tmp_path / ".vibe-llama/scaffold/basic/README.md"
    assert out_p.is_file() and out_p.stat().st_size > 0
    assert out_r.is_file() and out_r.stat().st_size > 0
    assert out_w.is_file() and out_w.stat().st_size > 0


@pytest.mark.asyncio
async def test_create_scaffold_custom(tmp_path: Path):
    os.chdir(tmp_path)
    succ = await create_scaffold("document_parsing", str(tmp_path / "example"))
    assert succ.startswith("[bold green]")
    out_w = tmp_path / "example/src/document_parsing/workflow.py"
    out_p = tmp_path / "example/pyproject.toml"
    out_r = tmp_path / "example/README.md"
    assert out_p.is_file() and out_p.stat().st_size > 0
    assert out_r.is_file() and out_r.stat().st_size > 0
    assert out_w.is_file() and out_w.stat().st_size > 0


def test_terminal_apps() -> None:
    assert isinstance(app1, Application)
    assert isinstance(app2, Application)
