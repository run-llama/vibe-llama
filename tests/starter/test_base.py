import pytest
import os
from pathlib import Path

from src.vibe_llama.starter import starter
from src.vibe_llama.starter.terminal import app1, app2, app3
from prompt_toolkit.application import Application


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
    assert not r
    with pytest.raises(KeyError):
        await starter(agent="GitHub Copilo", service="LlamaIndex")
    with pytest.raises(KeyError):
        await starter(agent="GitHub Copilot", service="LlamaInde")  # type: ignore


def test_terminal_apps() -> None:
    assert isinstance(app1, Application)
    assert isinstance(app2, Application)
    assert isinstance(app3, Application)
