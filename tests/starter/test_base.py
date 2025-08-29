import pytest
import httpx
import os
from pathlib import Path

from src.vibe_llama.starter import starter, services
from src.vibe_llama.starter.terminal import app1, app2, app3
from prompt_toolkit.application import Application
from src.vibe_llama.starter.utils import write_file, get_instructions


@pytest.mark.asyncio
async def test_starter() -> None:
    try:
        await starter(agent="GitHub Copilot", service="LlamaIndex", verbose=False)
        success = True
    except Exception:
        success = False
    assert success
    assert Path(".github/copilot-instructions.md").is_file()
    os.remove(".github/copilot-instructions.md")
    r = await starter(agent="GitHub Copilot")  # type: ignore
    assert r is None
    with pytest.raises(KeyError):
        await starter(agent="GitHub Copilo", service="LlamaIndex")
    with pytest.raises(KeyError):
        await starter(agent="GitHub Copilot", service="LlamaInde")


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


def test_terminal_apps() -> None:
    assert isinstance(app1, Application)
    assert isinstance(app2, Application)
    assert isinstance(app3, Application)
