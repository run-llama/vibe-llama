import pytest
import httpx
import os
from pathlib import Path

from src.vibe_llama.starter import starter, agent_rules, services
from src.vibe_llama.starter.terminal import SelectAgentApp, SelectServiceApp
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
    with pytest.raises(ValueError):
        await starter(agent="GitHub Copilot")
    with pytest.raises(KeyError):
        await starter(agent="GitHub Copilo", service="LlamaIndex")
    with pytest.raises(KeyError):
        await starter(agent="GitHub Copilot", service="LlamaInde")


@pytest.mark.asyncio
async def test_agent_select_app() -> None:
    app = SelectAgentApp()
    async with app.run_test() as pilot:
        await pilot.press("enter")
        await pilot.press("ctrl", "q")
    assert app.selected == [agent_rules["GitHub Copilot"]]
    app1 = SelectAgentApp()
    app1.selected = []
    async with app1.run_test() as pilot1:
        await pilot1.press("ctrl", "q")
    assert app1.selected == []


@pytest.mark.asyncio
async def test_service_select_app() -> None:
    app = SelectServiceApp()
    async with app.run_test() as pilot:
        await pilot.press("enter")
        await pilot.press("down")
        await pilot.press("enter")
        await pilot.press("ctrl", "q")
    assert app.selected == services["LlamaIndex"]
    app1 = SelectServiceApp()
    async with app1.run_test() as pilot1:
        await pilot1.press("ctrl", "q")
    assert app1.selected is None


@pytest.mark.asyncio
async def test_get_instructions() -> None:
    instr = await get_instructions(services["LlamaIndex"])
    content = str(httpx.get(services["LlamaIndex"]).content, encoding="utf-8")
    assert instr is not None
    assert instr == content


def test_write_file(tmp_path: Path) -> None:
    fl = tmp_path / "hello.txt"
    write_file(str(fl), "hello world\n", "https://www.llamaindex.ai")
    assert fl.is_file()
    assert fl.stat().st_size > 0
    write_file(str(fl), "hello world", "https://www.llamaindex.ai")
    with open(fl) as f:
        content = f.read()
    assert content == "hello world\n\nhello world"
