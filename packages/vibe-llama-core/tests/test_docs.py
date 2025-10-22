import pytest
import os
import httpx
from pathlib import Path
from unittest.mock import patch, AsyncMock

from typing import Any
from vibe_llama_core.docs.utils import write_file, get_instructions
from vibe_llama_core.docs import services, get_agent_rules, claude_code_skills

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

async def mock_write_skills(skills: list[str], *args: Any, **kwargs: Any) -> None:
    for i in skills:
        for j in claude_code_skills:
            if j["name"] == i:
                os.makedirs(j["local_path"], exist_ok=True)
                Path(j["local_path"] + "SKILL.md").touch()
                if "reference_md_url" in j:
                    Path(j["local_path"] + "REFERENCE.md").touch()
    return None

@pytest.mark.asyncio
@patch("vibe_llama_core.docs.utils.get_claude_code_skills", new_callable=AsyncMock)
async def test_get_agent_rules_skills(mock: AsyncMock) -> None:
    mock.side_effect = mock_write_skills
    with pytest.warns(UserWarning, match="Skills are not available for agents other than Claude Code."):
        await get_agent_rules(
            agent="GitHub Copilot", service="LlamaIndex", verbose=False, skills=["PDF Parsing"],overwrite_files=True,
        )
    assert (
        not Path(".claude/skills/pdf-processing/SKILL.md").exists()
    )
    assert (
        not Path(".claude/skills/pdf-processing/REFERENCE.md").exists()
    )
    mock.assert_not_called()
    os.remove(".github/copilot-instructions.md")
    await get_agent_rules(agent="Claude Code", service="LlamaIndex", verbose=False, skills=["PDF Parsing", "Information Retrieval"])
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
