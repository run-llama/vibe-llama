import pytest
import os
from pathlib import Path
from unittest.mock import patch, AsyncMock

from typing import Any
from vibe_llama.starter import starter
from vibe_llama.starter.terminal import app1, app2, app3, app2a
from prompt_toolkit.application import Application
from vibe_llama_core.docs import claude_code_skills


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


async def mock_write_skills(skills: list[str], *args: Any, **kwargs: Any) -> None:
    for i in skills:
        for j in claude_code_skills:
            if j["name"] == i:
                os.makedirs(j["local_path"], exist_ok=True)
                Path(j["local_path"] + "SKILL.md").touch()
                if "reference_md_url" in j:
                    Path(j["local_path"] + "REFERENCE.md").touch()
    return None


@patch("vibe_llama.starter.get_claude_code_skills", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_starter_skills_claude(mock: AsyncMock) -> None:
    if not Path(".claude/skills").exists():
        os.makedirs(".claude/skills", exist_ok=True)
    mock.side_effect = mock_write_skills
    await starter(
        "Claude Code",
        "LlamaCloud Services",
        ["PDF Parsing", "Information Retrieval"],
        overwrite_files=True,
    )
    mock.assert_called()
    assert (
        Path(".claude/skills/pdf-processing/SKILL.md").exists()
        and Path(".claude/skills/pdf-processing/SKILL.md").is_file()
    )
    assert (
        Path(".claude/skills/pdf-processing/REFERENCE.md").exists()
        and Path(".claude/skills/pdf-processing/REFERENCE.md").is_file()
    )
    assert (
        Path(".claude/skills/information-retrieval/SKILL.md").exists()
        and Path(".claude/skills/information-retrieval/SKILL.md").is_file()
    )
    assert not Path(".claude/skills/information-retrieval/REFERENCE.md").exists()
    for path in [
        ".claude/skills/information-retrieval/SKILL.md",
        ".claude/skills/pdf-processing/SKILL.md",
        ".claude/skills/pdf-processing/REFERENCE.md",
    ]:
        os.remove(path)


@patch("vibe_llama.starter.get_claude_code_skills", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_starter_skills_not_claude(mock: AsyncMock) -> None:
    mock.side_effect = mock_write_skills
    await starter(
        "GitHub Copilot",
        "LlamaCloud Services",
        ["PDF Parsing", "Information Retrieval"],
        overwrite_files=True,
    )  # should not write skills because agent is not Claude Code
    assert not Path(".claude/skills/pdf-processing/SKILL.md").exists()
    assert not Path(".claude/skills/pdf-processing/REFERENCE.md").exists()
    assert not Path(".claude/skills/information-retrieval/SKILL.md").exists()
    mock.assert_not_called()


def test_terminal_apps() -> None:
    assert isinstance(app1, Application)
    assert isinstance(app2, Application)
    assert isinstance(app3, Application)
    assert isinstance(app2a, Application)
