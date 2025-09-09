import pytest
import os
from pathlib import Path
from rich.console import Console

from src.vibe_llama.sdk import VibeLlamaScaffold


def test_init() -> None:
    scaffolder = VibeLlamaScaffold()
    assert scaffolder.colored_output
    assert isinstance(scaffolder._console, Console)


@pytest.mark.asyncio
async def test_get_scaffold_defaults(tmp_path: Path):
    os.chdir(tmp_path)
    scaffolder = VibeLlamaScaffold()
    await scaffolder.get_template()
    out_w = tmp_path / ".vibe-llama/scaffold/basic/src/basic/workflow.py"
    out_p = tmp_path / ".vibe-llama/scaffold/basic/pyproject.toml"
    out_r = tmp_path / ".vibe-llama/scaffold/basic/README.md"
    assert out_p.is_file() and out_p.stat().st_size > 0
    assert out_r.is_file() and out_r.stat().st_size > 0
    assert out_w.is_file() and out_w.stat().st_size > 0


@pytest.mark.asyncio
async def test_get_scaffold_custom(tmp_path: Path):
    os.chdir(tmp_path)
    scaffolder = VibeLlamaScaffold()
    await scaffolder.get_template("document_parsing", str(tmp_path / "example"))
    out_w = tmp_path / "example/src/document_parsing/workflow.py"
    out_p = tmp_path / "example/pyproject.toml"
    out_r = tmp_path / "example/README.md"
    assert out_p.is_file() and out_p.stat().st_size > 0
    assert out_r.is_file() and out_r.stat().st_size > 0
    assert out_w.is_file() and out_w.stat().st_size > 0
