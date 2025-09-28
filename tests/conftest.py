import os
from pathlib import Path
import pytest


@pytest.fixture(autouse=True)
def stub_copier_run_copy(monkeypatch, tmp_path):
    """Stub out copier.run_copy used by scaffold to avoid network access.

    Writes minimal project files into the destination directory so tests
    can assert their presence without cloning remote templates.
    """
    import vibe_llama.scaffold.scaffold as scaffold_mod

    def _stub_run_copy(template_src, dst_path, *args, **kwargs):
        # Infer module name from the template source string
        src = str(template_src)
        module_name = "basic"
        if "document-parsing" in src or "document_parsing" in src:
            module_name = "document_parsing"
        elif "human-in-the-loop" in src or "human_in_the_loop" in src:
            module_name = "human_in_the_loop"
        elif "invoice-extraction" in src or "invoice_extraction" in src:
            module_name = "invoice_extraction"
        elif "template-workflow-rag" in src:
            module_name = "rag"
        elif "web-scraping" in src or "web_scraping" in src:
            module_name = "web_scraping"

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
        (dst / "src" / module_name / "workflow.py").write_text(
            "workflow = object()\n"
        )

    monkeypatch.setattr(scaffold_mod, "run_copy", _stub_run_copy)
    yield

