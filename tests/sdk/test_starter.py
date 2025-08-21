import pytest
import os
from pathlib import Path

from src.vibe_llama.sdk import VibeLlamaStarter
from src.vibe_llama.starter import agent_rules, services


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


@pytest.mark.asyncio
async def test_write_instructions(tmp_path: Path) -> None:
    starter = VibeLlamaStarter(
        agents=["GitHub Copilot", "Cursor"],
        services=["LlamaIndex", "llama-index-workflows"],
    )
    os.chdir(tmp_path)
    await starter.write_instructions()
    assert (tmp_path / agent_rules["GitHub Copilot"]).is_file()
    assert (tmp_path / agent_rules["Cursor"]).is_file()
    assert (tmp_path / agent_rules["GitHub Copilot"]).stat().st_size > 0
    assert (tmp_path / agent_rules["Cursor"]).stat().st_size > 0
