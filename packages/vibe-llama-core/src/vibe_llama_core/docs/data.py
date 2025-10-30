from typing import Literal, TypedDict
from typing_extensions import NotRequired

from vibe_llama_core.constants import BASE_URL

agent_rules = {
    "vibe-llama docuflows": ".vibe-llama/rules/AGENTS.md",
    "GitHub Copilot": ".github/copilot-instructions.md",
    "Claude Code": "CLAUDE.md",
    "OpenAI Codex CLI": "AGENTS.md",
    "Jules": "AGENTS.md",
    "Cursor": ".cursor/rules/cursor_instructions.mdc",
    "Windsurf": ".windsurf/rules/windsurf_instructions.md",
    "Cline": ".clinerules",
    "Amp": "AGENT.md",
    "Firebase Studio": ".idx/airules.md",
    "Open Hands": ".openhands/microagents/repo.md",
    "Gemini CLI": "GEMINI.md",
    "Junie": ".junie/guidelines.md",
    "AugmentCode": ".augment/rules/augment_instructions.md",
    "Kilo Code": ".kilocode/rules/kilocode_instructions.md",
    "OpenCode": "AGENTS.md",
    "Goose": ".goosehints",
}

LibraryName = Literal[
    "LlamaIndex", "LlamaCloud Services", "llama-index-workflows", "LlamaDeploy"
]

class ClaudeCodeSkill(TypedDict):
    skill_md_url: str
    reference_md_url: NotRequired[str]
    local_path: str
    name: str

services: dict[LibraryName, str] = {
    "LlamaIndex": f"{BASE_URL}/documentation/llamaindex.md",
    "LlamaCloud Services": f"{BASE_URL}/documentation/llamacloud.md",
    "llama-index-workflows": f"{BASE_URL}/documentation/llama-index-workflows.md",
    "LlamaDeploy": f"{BASE_URL}/documentation/llamadeploy.md",
}

claude_code_skills: list[ClaudeCodeSkill] = [
    {"skill_md_url": f"{BASE_URL}/documentation/skills/pdf-processing/SKILL.md", "local_path": ".claude/skills/pdf-processing/", "reference_md_url": f"{BASE_URL}/documentation/skills/pdf-processing/REFERENCE.md", "name": "PDF Parsing"},
    {"skill_md_url": f"{BASE_URL}/documentation/skills/structured-data-extraction/SKILL.md", "reference_md_url":  f"{BASE_URL}/documentation/skills/structured-data-extraction/REFERENCE.md", "local_path": ".claude/skills/structured-data-extraction/", "name": "Structured Data Extraction"},
    {"skill_md_url": f"{BASE_URL}/documentation/skills/information-retrieval/SKILL.md", "local_path": ".claude/skills/information-retrieval/", "name": "Information Retrieval"},
    {"skill_md_url": f"{BASE_URL}/documentation/skills/text-classification/SKILL.md", "reference_md_url": f"{BASE_URL}/documentation/skills/text-classification/REFERENCE.md", "local_path": ".claude/skills/text-classification/", "name": "Text Classification"},
    {"skill_md_url": f"{BASE_URL}/documentation/skills/llamactl/SKILL.md", "reference_md_url": f"{BASE_URL}/documentation/skills/llamactl/REFERENCE.md", "local_path": ".claude/skills/llamactl/", "name": "Llamactl Usage"}
]

mcp_config = {
  "mcpServers": {
    "vibe-llama": {
      "type": "http",
      "command": "vibe-llama",
      "args": [
        "starter",
        "--mcp",
      ],
      "env": {}
    },
    "llama-index-docs": {
      "type": "http",
      "url": "https://developers.llamaindex.ai/mcp"
    }
  }
}
