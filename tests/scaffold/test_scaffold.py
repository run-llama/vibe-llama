from pathlib import Path
import httpx
import pytest
import toml
import os

from src.vibe_llama.scaffold import PROJECTS, create_scaffold
from src.vibe_llama.scaffold.project_files import generate_pyproject
from src.vibe_llama.scaffold.copy_templates import get_template_files, base_url, files
from src.vibe_llama.scaffold.terminal import app1, app2
from prompt_toolkit.application import Application


def test_generate_pyproject(tmp_path: Path) -> None:
    out_path = tmp_path / "pyproject.toml"
    generate_pyproject("base_example", str(out_path))
    with open(out_path, "r") as f:
        content = f.read()
    data = toml.loads(content)
    assert data["project"]["name"] == "base_example"
    assert data["project"]["version"] == "0.1.0"
    assert data["project"]["description"] == PROJECTS["base_example"]["description"]
    assert data["project"]["readme"] == "README.md"
    assert data["project"]["dependencies"] == PROJECTS["base_example"]["dependencies"]


@pytest.mark.asyncio
async def test_get_template_files() -> None:
    res = await get_template_files("base_example")
    assert res is not None
    assert "workflow.py" in res
    assert "README.md" in res
    async with httpx.AsyncClient() as client:
        for fl in files:
            response = await client.get(base_url + "base_example" + "/" + fl)
            if response.status_code == 200:
                assert response.text == res[fl]


@pytest.mark.asyncio
async def test_create_scaffold_defaults(tmp_path: Path):
    os.chdir(tmp_path)
    succ = await create_scaffold()
    assert succ.startswith("[bold green]")
    out_w = tmp_path / ".vibe-llama/scaffold/base_example/workflow.py"
    out_p = tmp_path / ".vibe-llama/scaffold/base_example/pyproject.toml"
    out_r = tmp_path / ".vibe-llama/scaffold/base_example/README.md"
    assert out_p.is_file() and out_p.stat().st_size > 0
    assert out_r.is_file() and out_r.stat().st_size > 0
    assert out_w.is_file() and out_w.stat().st_size > 0


@pytest.mark.asyncio
async def test_create_scaffold_custom(tmp_path: Path):
    os.chdir(tmp_path)
    succ = await create_scaffold("document_parsing", str(tmp_path / "example"))
    assert succ.startswith("[bold green]")
    out_w = tmp_path / "example/workflow.py"
    out_p = tmp_path / "example/pyproject.toml"
    out_r = tmp_path / "example/README.md"
    assert out_p.is_file() and out_p.stat().st_size > 0
    assert out_r.is_file() and out_r.stat().st_size > 0
    assert out_w.is_file() and out_w.stat().st_size > 0


def test_terminal_apps() -> None:
    assert isinstance(app1, Application)
    assert isinstance(app2, Application)
