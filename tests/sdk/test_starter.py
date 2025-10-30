import pytest
import os
from pathlib import Path
from unittest.mock import patch, AsyncMock

from typing import Any
from vibe_llama.sdk import VibeLlamaStarter
from vibe_llama_core.docs.data import agent_rules, services, claude_code_skills


def test_init() -> None:
    starter = VibeLlamaStarter(
        agents=["GitHub Copilot", "Cursor"],
        services=["LlamaIndex", "llama-index-workflows"],
    )
    assert starter.agent_files == [agent_rules["GitHub Copilot"], agent_rules["Cursor"]]
    assert starter.service_urls == [
        services["LlamaIndex"],
        services["llama-index-workflows"],
    ]


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
@patch("vibe_llama.sdk.base.get_claude_code_skills", new_callable=AsyncMock)
async def test_write_instructions(mock: AsyncMock, tmp_path: Path) -> None:
    mock.side_effect = mock_write_skills
    with pytest.warns(
        UserWarning, match="Skills are not available for agents other than Claude Code."
    ):
        starter = VibeLlamaStarter(
            agents=["GitHub Copilot", "Cursor"],
            services=["LlamaIndex", "llama-index-workflows"],
            skills=["PDF Parsing"],
        )
    os.chdir(tmp_path)
    await starter.write_instructions()
    assert (tmp_path / agent_rules["GitHub Copilot"]).is_file()
    assert (tmp_path / agent_rules["Cursor"]).is_file()
    prev_sz_gh = (tmp_path / agent_rules["GitHub Copilot"]).stat().st_size
    prev_sz_cur = (tmp_path / agent_rules["Cursor"]).stat().st_size
    assert prev_sz_gh > 0
    assert prev_sz_cur > 0
    await starter.write_instructions(overwrite=True)
    assert prev_sz_cur == (tmp_path / agent_rules["Cursor"]).stat().st_size
    assert prev_sz_gh == (tmp_path / agent_rules["GitHub Copilot"]).stat().st_size
    assert not (tmp_path / ".claude/skills/pdf-processing/SKILL.md").exists()
    assert not (tmp_path / ".claude/skills/pdf-processing/REFERENCE.md").exists()
    mock.assert_not_called()


@pytest.mark.asyncio
@patch("vibe_llama.sdk.base.get_claude_code_skills", new_callable=AsyncMock)
async def test_write_instructions_claude_skills(
    mock: AsyncMock, tmp_path: Path
) -> None:
    mock.side_effect = mock_write_skills
    starter = VibeLlamaStarter(
        agents=["Claude Code"],
        services=["LlamaIndex", "llama-index-workflows"],
        skills=["PDF Parsing"],
    )
    cwd = Path.cwd()
    os.chdir(tmp_path)
    await starter.write_instructions()
    assert (tmp_path / ".claude/skills/pdf-processing/SKILL.md").exists()
    assert (tmp_path / ".claude/skills/pdf-processing/REFERENCE.md").exists()
    mock.assert_called()
    os.chdir(cwd)


@pytest.mark.asyncio
async def test_write_instructions_mcp_config(tmp_path: Path) -> None:
    starter = VibeLlamaStarter(
        agents=["Claude Code"],
        services=["llama-index-workflows"],
        allow_mcp_config=True,
    )
    cwd = Path.cwd()
    os.chdir(tmp_path)
    await starter.write_instructions()
    assert (tmp_path / ".mcp.json").exists()
    with pytest.raises(FileExistsError):
        await starter.write_instructions()
    starter.mcp_config_path = "mcp.json"
    starter.allow_mcp_config = False
    await starter.write_instructions()
    assert not (tmp_path / "mcp.json").exists()
    os.chdir(cwd)
