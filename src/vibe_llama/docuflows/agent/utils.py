import json
import os
from typing import Any, cast

from llama_index.core.llms import LLM, MessageRole
from llama_index.core.prompts import ChatMessage
from llama_index.core.tools import BaseTool
from pydantic import BaseModel

# Rich imports for beautiful CLI formatting
from rich.console import Console

# Workflows imports
from workflows import Context
from workflows.events import (
    Event,
    InputRequiredEvent,
)

from rich.live import Live
from rich.spinner import Spinner

from vibe_llama.docuflows.commons import CLIFormatter, StreamEvent
from vibe_llama.docuflows.prompts import AGENT_SYSTEM_PROMPT
from vibe_llama.docuflows.commons.typed_state import WorkflowState

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

# Initialize rich console
console = Console()

# Global debug flag
DEBUG_MODE = False


def set_debug_mode(enabled: bool):
    """Set global debug mode"""
    global DEBUG_MODE
    DEBUG_MODE = enabled


def debug_print(*args, **kwargs):
    """Print debug message only if debug mode is enabled"""
    if DEBUG_MODE:
        console.print("[dim cyan]DEBUG:[/dim cyan]", *args, **kwargs)


# =============================================================================
# CONFIGURATION MANAGEMENT
# =============================================================================


class AgentConfig(BaseModel):
    """Configuration for LlamaVibe"""

    project_id: str | None = None
    organization_id: str | None = None
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    llama_cloud_api_key: str | None = None
    default_reference_files_path: str | None = None
    output_directory: str = "generated_workflows"
    current_model: str = "gpt-4.1"

    def save_to_file(self, config_path: str = ".ai_agent_config.json"):
        """Save configuration to file"""
        with open(config_path, "w") as f:
            json.dump(self.model_dump(), f, indent=2)

    @classmethod
    def load_from_file(
        cls, config_path: str = ".ai_agent_config.json"
    ) -> "AgentConfig":
        """Load configuration from file"""
        if os.path.exists(config_path):
            with open(config_path) as f:
                data = json.load(f)
                return cls(**data)
        return cls()


# =============================================================================
# WORKFLOW EVENTS
# =============================================================================


class ToolCallsEvent(Event):
    """Event containing tool calls to execute"""

    tool_calls: list[Any]
    user_msg: str


# =============================================================================
# SLASH COMMAND HANDLER
# =============================================================================


async def handle_slash_command(
    ctx: Context[WorkflowState], command: str
) -> InputRequiredEvent:
    """Handle slash commands like /help and /config"""
    command = command.lower().strip()

    if command == "/help":
        current_model = (await ctx.store.get_state()).current_model or "gpt-4.1"
        help_text = f"""
🎵 **vibe-llama docuflows - Slash Commands**

Available commands:
• `/help` - Show this help message
• `/config` - Configure your LlamaCloud credentials and settings
• `/model` - Configure OpenAI model (currently: {current_model})
• `help` - Show general workflow help
• `quit`, `exit`, `bye` - Exit LlamaVibe

**Regular Commands:**
• "Generate a workflow" - Create new workflows from natural language
• "Test it on sample data" - Test your current workflow
• "Edit the workflow" - Modify existing workflows
• "Show config" - Display current configuration

**Examples:**
> /config
> Generate a workflow to extract financial data from PDFs
> Test it on examples/test_files/sample.pdf
        """

        ctx.write_event_to_stream(
            StreamEvent(  # type: ignore # type: ignore
                delta="",
                rich_content=CLIFormatter.info(help_text.strip()),
                newline_after=True,
            )
        )

        ctx.write_event_to_stream(
            StreamEvent(  # type: ignore # type: ignore
                rich_content=CLIFormatter.indented_text("What would you like to do?"),
                newline_after=True,
            )
        )
        return InputRequiredEvent(prefix="")  # type: ignore

    elif command == "/config":
        config = cast(AgentConfig, (await ctx.store.get_state()).config)

        config_text = f"""
🔧 **Current Configuration:**

1. Project ID: {config.project_id or "[Not Set]"}
2. Organization ID: {config.organization_id or "[Not Set]"}
3. Output Directory: {config.output_directory}

**API Keys:**
• OpenAI API Key: {"[Set]" if config.openai_api_key else "[Not Set]"}
• Anthropic API Key: {"[Set]" if config.anthropic_api_key else "[Not Set]"}
• LlamaCloud API Key: {"[Set]" if config.llama_cloud_api_key else "[Not Set]"}

**Commands:**
• Type a number (1-3) to edit that field
• Type 'done' to finish
• Type 'reset' to clear all settings
        """

        ctx.write_event_to_stream(
            StreamEvent(  # type: ignore
                delta="",
                rich_content=CLIFormatter.info(config_text.strip()),
                newline_after=True,
            )
        )

        return InputRequiredEvent(
            prefix="What would you like to edit? (1-3, done, reset): ",  # type: ignore
            tag="config_menu",  # type: ignore
        )

    elif command == "/model":
        current_model = (await ctx.store.get_state()).current_model
        if not current_model:
            config = cast(AgentConfig, (await ctx.store.get_state()).config)
            current_model = config.current_model

        model_text = f"""
🤖 **LLM Model Configuration**

Current model: {current_model}

Available models:
**OpenAI Models:**
1. gpt-5 (Latest flagship)
2. gpt-5-mini (Balanced performance)
3. gpt-5-nano (Fastest)
4. gpt-4.1 (Previous flagship)
5. gpt-4.1-mini (Balanced)
6. gpt-4o (Optimized)
7. gpt-4o-mini (Fast & efficient)

**Claude 4 Models:**
8. claude-sonnet-4-20250514 (Balanced performance)
9. claude-opus-4-20250514 (Most capable)
10. claude-opus-4-1-20250805 (Latest Opus)

Choose a number (1-10) or type 'cancel' to keep current:
        """

        ctx.write_event_to_stream(
            StreamEvent(  # type: ignore
                delta="",
                rich_content=CLIFormatter.info(model_text.strip()),
                newline_after=True,
            )
        )

        return InputRequiredEvent(
            prefix="Select model (1-10) or 'cancel': ",
            tag="model_selection",  # type: ignore
        )

    else:
        ctx.write_event_to_stream(
            StreamEvent(  # type: ignore
                delta="",
                rich_content=CLIFormatter.error(
                    f"Unknown command: {command}\nType /help for available commands"
                ),
                newline_after=True,
            )
        )

        ctx.write_event_to_stream(
            StreamEvent(  # type: ignore
                rich_content=CLIFormatter.indented_text("What would you like to do?"),
                newline_after=True,
            )
        )
        return InputRequiredEvent(prefix="")  # type: ignore


# =============================================================================
# CORE CHAT HANDLER
# =============================================================================


async def handle_chat(
    ctx: Context[WorkflowState], user_input: str, llm: LLM, tools: list[BaseTool]
) -> ToolCallsEvent | InputRequiredEvent | None:
    """Handle regular chat and determine tool calls"""
    chat_history = (await ctx.store.get_state()).chat_history

    # Add user message to history
    chat_history.append(ChatMessage(role=MessageRole.USER, content=user_input))
    async with ctx.store.edit_state() as state:
        state.chat_history = chat_history

    # Prepare full chat history with system message
    full_chat_history = [
        ChatMessage(role=MessageRole.SYSTEM, content=AGENT_SYSTEM_PROMPT),
        *chat_history[-10:],  # Keep last 10 messages for context
    ]

    # Show thinking spinner throughout entire response generation

    console = Console()
    spinner = Spinner("dots", text="Thinking...")

    # Get tool calls from LLM with spinner
    response = await llm.astream_chat_with_tools(  # type: ignore
        tools=tools, chat_history=full_chat_history, allow_parallel_tool_calls=False
    )

    # Collect the entire response while showing spinner
    full_response = ""

    with Live(spinner, refresh_per_second=10, console=console):
        async for r in response:
            if r.delta:
                full_response += r.delta
        # Spinner stops automatically when the with block exits

    # Get tool calls from the final response (r is the last response object)
    tool_calls = llm.get_tool_calls_from_response(r, error_on_no_tool_call=False)  # type: ignore

    # Only stream response to user if no tool calls (to avoid showing JSON tool outputs)
    if not tool_calls and full_response.strip():
        # Format agent response with proper indentation under Response header

        formatted_response = CLIFormatter.agent_response(full_response.strip())
        ctx.write_event_to_stream(
            StreamEvent(  # type: ignore
                rich_content=formatted_response, newline_after=True
            )
        )

    debug_print(f"Full chat history: {full_chat_history}")
    debug_print(f"Tool calls: {tool_calls}")
    debug_print(f"LLM type: {type(llm)}")

    if tool_calls:
        return ToolCallsEvent(tool_calls=tool_calls, user_msg=user_input)
    else:
        # Add assistant response to history and continue
        chat_history.append(
            ChatMessage(role=MessageRole.ASSISTANT, content=full_response)
        )
        async with ctx.store.edit_state() as state:
            state.chat_history = chat_history

        ctx.write_event_to_stream(
            StreamEvent(  # type: ignore
                rich_content=CLIFormatter.indented_text(
                    "What would you like to do next?"
                ),
                newline_after=True,
            )
        )
        return InputRequiredEvent(prefix="")  # type: ignore
