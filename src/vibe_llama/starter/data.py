from typing import Literal

from vibe_llama.constants import BASE_URL

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

services: dict[LibraryName, str] = {
    "LlamaIndex": f"{BASE_URL}/documentation/llamaindex.md",
    "LlamaCloud Services": f"{BASE_URL}/documentation/llamacloud.md",
    "llama-index-workflows": f"{BASE_URL}/documentation/llama-index-workflows.md",
    "LlamaDeploy": f"{BASE_URL}/documentation/llamadeploy.md",
}
