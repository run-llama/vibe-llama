from pathlib import Path
import pytest
import os


from src.vibe_llama.scaffold import create_scaffold
import src.vibe_llama.scaffold.scaffold as scaffold_module
from src.vibe_llama.scaffold.terminal import app1, app2
from prompt_toolkit.application import Application


@pytest.fixture()
def fake_copier(monkeypatch):
    def _run_copy(_src: str, dst: str, *args, **kwargs):
        # create minimal project structure with workflow.py, README.md, pyproject.toml
        # infer module name from final path component
        os.makedirs(dst, exist_ok=True)
        # try to detect module directory name from dst
        # if dst ends with '/basic', module is 'basic' etc.
        module_name = os.path.basename(dst).replace("-", "_")
        # write pyproject
        (Path(dst) / "pyproject.toml").write_text(
            f"""
[project]
name = "{module_name.replace("_", "-")}"
version = "0.1.0"
description = "Test template"
readme = "README.md"
dependencies = ["llama-index-core>=0.13.3"]
""".strip()
        )
        # write README
        (Path(dst) / "README.md").write_text("# Template\n")
        # write minimal workflow module
        pkg_dir = Path(dst) / "src" / module_name
        os.makedirs(pkg_dir, exist_ok=True)
        (pkg_dir / "__init__.py").write_text("")
        (pkg_dir / "workflow.py").write_text(
            "from llama_index.core.workflow import Workflow\nworkflow = Workflow()\n"
        )

    monkeypatch.setattr(scaffold_module, "run_copy", _run_copy)
    return _run_copy


@pytest.mark.asyncio
async def test_create_scaffold_defaults(tmp_path: Path, fake_copier):
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
async def test_create_scaffold_custom(tmp_path: Path, fake_copier):
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
