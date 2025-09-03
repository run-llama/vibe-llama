from vibe_llama.constants import BASE_URL

agent_rules = {
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
    "vibe-llama docuflows": ".vibe-llama/rules/AGENTS.md",
}

services = {
    "LlamaIndex": f"{BASE_URL}/documentation/llamaindex.md",
    "LlamaCloud Services": f"{BASE_URL}/documentation/llamacloud.md",
    "llama-index-workflows": f"{BASE_URL}/documentation/llama-index-workflows.md",
}
