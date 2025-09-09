from pathlib import Path
import pytest
import subprocess
import toml
import os


from src.vibe_llama.scaffold import PROJECTS, create_scaffold
from src.vibe_llama.scaffold.terminal import app1, app2
from prompt_toolkit.application import Application


def test_template_pyprojects_sync_with_catalog() -> None:
    """Ensure static template pyprojects match the PROJECTS catalog."""
    templates_root = Path(__file__).resolve().parents[2] / "templates"
    for name in PROJECTS:
        p = templates_root / name / "pyproject.toml"
        assert p.is_file(), f"Missing pyproject for template {name}"
        data = toml.loads(p.read_text())
        assert data["project"]["name"] == name.replace("_", "-")
        assert data["project"]["version"] == "0.1.0"
        assert data["project"]["description"] is not None
        assert data["project"]["readme"] == "README.md"
        assert data["project"]["dependencies"] is not None
        # Test that the workflow can be imported and validated

        # Change to the template directory to run the validation
        template_dir = templates_root / name
        module_name = name.replace("-", "_")

        # Run validation in a subprocess
        result = subprocess.run(
            [
                "uv",
                "run",
                "python",
                "-c",
                f"from {module_name}.workflow import workflow; workflow._validate()",
            ],
            cwd=template_dir,
            capture_output=False,
            check=True,
            text=True,
        )

        assert result.returncode == 0, (
            f"Workflow validation failed for {name}: {result.stderr}"
        )


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
