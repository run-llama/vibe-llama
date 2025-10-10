from pathlib import Path
import pytest
import os


from src.vibe_llama_core.templates import download_template


@pytest.fixture(autouse=True)
def stub_copier_run_copy(monkeypatch, tmp_path):
    """Stub out copier.run_copy used by scaffold to avoid network access.

    Writes minimal project files into the destination directory so tests
    can assert their presence without cloning remote templates.
    """
    import copier

    def _stub_run_copy(template_src, dst_path, *args, **kwargs):
        # Infer module name from the template source string
        src = str(template_src)
        src = src.split("/")[-1]
        src = src.removeprefix("template-workflow-")
        module_name = (src or "basic").replace("-", "_")

        dst = Path(dst_path)
        (dst / "src" / module_name).mkdir(parents=True, exist_ok=True)
        (dst / "pyproject.toml").write_text(
            """[project]
name = "{name}"
version = "0.1.0"
description = "Test template"
readme = "README.md"
dependencies = []
""".format(name=module_name.replace("_", "-"))
        )
        (dst / "README.md").write_text(f"# {module_name}\n")
        (dst / "src" / module_name / "workflow.py").write_text("workflow = object()\n")

    monkeypatch.setattr(copier, "run_copy", _stub_run_copy)
    yield


@pytest.mark.asyncio
async def test_download_template_defaults(tmp_path: Path):
    os.chdir(tmp_path)
    succ = await download_template()
    assert succ.startswith("[bold green]")
    out_w = tmp_path / ".vibe-llama/scaffold/basic/src/basic/workflow.py"
    out_p = tmp_path / ".vibe-llama/scaffold/basic/pyproject.toml"
    out_r = tmp_path / ".vibe-llama/scaffold/basic/README.md"
    assert out_p.is_file() and out_p.stat().st_size > 0
    assert out_r.is_file() and out_r.stat().st_size > 0
    assert out_w.is_file() and out_w.stat().st_size > 0


@pytest.mark.asyncio
async def test_download_template_custom(tmp_path: Path):
    os.chdir(tmp_path)
    succ = await download_template("document_parsing", str(tmp_path / "example"))
    assert succ.startswith("[bold green]")
    out_w = tmp_path / "example/src/document_parsing/workflow.py"
    out_p = tmp_path / "example/pyproject.toml"
    out_r = tmp_path / "example/README.md"
    assert out_p.is_file() and out_p.stat().st_size > 0
    assert out_r.is_file() and out_r.stat().st_size > 0
    assert out_w.is_file() and out_w.stat().st_size > 0
