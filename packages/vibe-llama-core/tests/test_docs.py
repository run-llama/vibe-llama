import pytest
import os
import httpx
from pathlib import Path

from src.vibe_llama_core.docs.utils import write_file, get_instructions
from src.vibe_llama_core.docs import services, get_agent_rules

@pytest.mark.asyncio
async def test_get_instructions() -> None:
    instr = await get_instructions(services["LlamaIndex"])
    content = str(httpx.get(services["LlamaIndex"]).content, encoding="utf-8")
    assert instr is not None
    assert instr == content


def test_write_file(tmp_path: Path) -> None:
    fl = tmp_path / "hello.txt"
    write_file(str(fl), "hello world\n", False, "https://www.llamaindex.ai")
    assert fl.is_file()
    assert fl.stat().st_size > 0
    write_file(str(fl), "hello world", False, "https://www.llamaindex.ai")
    with open(fl) as f:
        content = f.read()
    assert content == "hello world\n\nhello world"
    write_file(str(fl), "hello world\n", True, "https://www.llamaindex.ai")
    with open(fl) as f:
        content = f.read()
    assert content == "hello world\n"

@pytest.mark.asyncio
async def test_get_agent_rules() -> None:
    try:
        await get_agent_rules(agent="GitHub Copilot", service="LlamaIndex", verbose=False)
        success = True
    except Exception:
        success = False
    assert success
    assert Path(".github/copilot-instructions.md").is_file()
    os.remove(".github/copilot-instructions.md")
    with pytest.raises(TypeError):
        await get_agent_rules(agent="GitHub Copilot")  # type: ignore
    with pytest.raises(KeyError):
        await get_agent_rules(agent="GitHub Copilo", service="LlamaIndex")
    with pytest.raises(KeyError):
        await get_agent_rules(agent="GitHub Copilot", service="LlamaInde") # type: ignore
