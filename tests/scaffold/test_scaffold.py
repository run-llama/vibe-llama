from pathlib import Path
import httpx
import pytest
import toml

from src.vibe_llama.scaffold import PROJECTS
from src.vibe_llama.scaffold.project_files import generate_pyproject
from src.vibe_llama.scaffold.copy_templates import get_template_files, base_url, files


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
