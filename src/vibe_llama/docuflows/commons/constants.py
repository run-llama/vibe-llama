"""
Constants for vibe-llama docuflows AI Agent CLI.

Contains shared configuration values and constants used across the application.
"""

# LLM Configuration
DEFAULT_MAX_TOKENS = 16384  # Default max tokens for LLM responses
DEFAULT_OPENAI_MODEL = "gpt-4.1"
DEFAULT_ANTHROPIC_MODEL = "claude-sonnet-4-20250514"

# File handling
MAX_CODE_DISPLAY_LINES = 50  # Maximum lines to show when displaying code
MAX_COMPLETION_ITEMS = 10  # Maximum items to show in @ path completion

# UI Configuration
CODE_PANEL_HEIGHT_OFFSET = (
    15  # Space to leave for UI elements when calculating code panel height
)
