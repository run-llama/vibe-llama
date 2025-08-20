#!/usr/bin/env python3
"""
LlamaVibe - Interactive Workflow Generation and Management

LlamaVibe uses LlamaIndex workflows to create an interactive agent that can:
1. Generate workflows from natural language descriptions
2. Edit and refine workflows based on user feedback
3. Test workflows on sample data
4. Answer questions about generated workflows
5. Maintain conversation history and state
"""

import json
import os
from typing import Any, Optional

from llama_index.core.llms import LLM, MessageRole
from llama_index.core.prompts import ChatMessage
from llama_index.core.tools import BaseTool, FunctionTool
from llama_index.llms.openai import OpenAI
from pydantic import BaseModel

# Rich imports for beautiful CLI formatting
from rich.console import Console

# Workflows imports
from workflows import Context, Workflow, step
from workflows.events import (
    Event,
    HumanResponseEvent,
    InputRequiredEvent,
    StartEvent,
    StopEvent,
)

from .constants import DEFAULT_MAX_TOKENS
from .utils import CLIFormatter

# Import the shared workflow generation functions
from .handlers.other_handlers import (
    handle_answer_question,
    handle_configuration,
    handle_help,
    handle_load_workflow,
    handle_reconfigure,
    handle_show_config,
    validate_uuid,
)
from .handlers.workflow_editing import (
    handle_edit_workflow,
    handle_generate_runbook_after_diff,
    interpret_user_intent,
)

# Import handlers from separate modules
from .handlers.workflow_generation import (
    handle_folder_name_input,
    handle_generate_workflow,
)
from .handlers.workflow_testing import (
    handle_test_file_selection,
    handle_test_workflow,
)

# Import utility classes
from .utils import StreamEvent, boxed_input_async

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
# TOOLS FOR THE AGENT
# =============================================================================


def create_agent_tools() -> list[BaseTool]:
    """Create tools that the agent can use"""

    def generate_workflow_tool(task: str, reference_files_path: str) -> str:
        """Generate a workflow based on a task description and reference files directory"""
        return json.dumps(
            {
                "action": "generate_workflow",
                "task": task,
                "reference_files_path": reference_files_path,
            }
        )

    def edit_workflow_tool(edit_request: str) -> str:
        """Edit the current workflow based on user request"""
        return json.dumps({"action": "edit_workflow", "edit_request": edit_request})

    def test_workflow_tool(test_file_path: str = "") -> str:
        """Test the current workflow on sample data. Only provide test_file_path if user specified a specific file path."""
        return json.dumps({"action": "test_workflow", "test_file_path": test_file_path})

    def answer_question_tool(question: str) -> str:
        """Answer questions about the current workflow"""
        return json.dumps({"action": "answer_question", "question": question})

    def show_config_tool() -> str:
        """Show current configuration"""
        return json.dumps({"action": "show_config"})

    def reconfigure_tool() -> str:
        """Reconfigure credentials (project_id and organization_id)"""
        return json.dumps({"action": "reconfigure"})

    def load_workflow_tool(workflow_path: str) -> str:
        """Load an existing workflow from a file"""
        return json.dumps({"action": "load_workflow", "workflow_path": workflow_path})

    return [
        FunctionTool.from_defaults(
            fn=generate_workflow_tool,
            name="generate_workflow",
            description="Generate a NEW workflow from scratch based on task description and reference files directory path. ONLY use when user wants to CREATE a new workflow. DO NOT use for testing existing workflows - use test_workflow instead.",
        ),
        FunctionTool.from_defaults(
            fn=edit_workflow_tool,
            name="edit_workflow",
            description="Edit the current workflow based on user feedback or requirements",
        ),
        FunctionTool.from_defaults(
            fn=test_workflow_tool,
            name="test_workflow",
            description="Test the current/existing workflow on sample data or a specific file. ALWAYS use this tool for ANY testing request including: 'test', 'test it', 'test on sample data', 'run it on a file', 'try it out', or similar. DO NOT use generate_workflow for testing.",
        ),
        FunctionTool.from_defaults(
            fn=answer_question_tool,
            name="answer_question",
            description="Answer questions about the current workflow's functionality or structure",
        ),
        FunctionTool.from_defaults(
            fn=show_config_tool,
            name="show_config",
            description="Show the current configuration settings",
        ),
        FunctionTool.from_defaults(
            fn=reconfigure_tool,
            name="reconfigure",
            description="Reconfigure credentials (useful when project_id or organization_id are invalid)",
        ),
        FunctionTool.from_defaults(
            fn=load_workflow_tool,
            name="load_workflow",
            description="Load an existing workflow from a Python file. ONLY use when user explicitly wants to 'load', 'open', or 'switch to' a different workflow file. Do NOT use if user wants to work with the current workflow.",
        ),
    ]


# =============================================================================
# SYSTEM PROMPTS
# =============================================================================

AGENT_SYSTEM_PROMPT = """
You are LlamaVibe, an intelligent assistant that helps users create, edit, and manage LlamaIndex workflows for document processing.

Your capabilities:
1. Generate workflows from natural language task descriptions using the generate_workflow tool
2. Load existing workflows from files using the load_workflow tool
3. Edit and refine existing workflows using the edit_workflow tool
4. Test workflows on sample data using the test_workflow tool
5. Answer questions about workflow functionality using the answer_question tool
6. Show current configuration using the show_config tool
7. Reconfigure credentials using the reconfigure tool (useful when project_id/organization_id are invalid)

CRITICAL - Tool Selection Rules (READ CAREFULLY):

**FOR TESTING WORKFLOWS:**
- User says: "test", "test it", "test on sample data", "test the workflow", "i want to test it", "run it on a file", "try it out", "test it on sample data", etc.
- Action: ALWAYS use test_workflow tool ONLY
- DO NOT use generate_workflow or any other tool for testing requests
- The test_workflow tool will check if a current workflow exists and handle accordingly

**FOR GENERATING NEW WORKFLOWS:**
- User says: "create", "generate", "new workflow", "I want to create a workflow", etc.
- Action: Use generate_workflow tool ONLY after getting task details and reference files path
- DO NOT use generate_workflow for testing requests

**FOR OTHER ACTIONS:**
- Use load_workflow ONLY when user explicitly wants to load/open/switch to a DIFFERENT workflow file (e.g., "load my other workflow", "open generated_workflow_x.py"). DO NOT use if user wants to work with the current workflow.
- Use edit_workflow when user wants to MODIFY the current workflow
- Use answer_question when user asks questions about how the workflow works or wants explanations/summaries
- Use show_config when user wants to see current settings
- Use reconfigure when user wants to reset credentials

When users want to generate a workflow, you MUST ask for:
1. A clear task description of what the workflow should do
2. The path to reference files directory (required for workflow generation)

When users want to test a workflow, you MUST ask for:
1. The path to a sample file to test on

When users want to edit a workflow, make sure there's a current workflow loaded first.

Always use the appropriate tools to accomplish user requests. Be helpful and guide users through the workflow creation process.

Example interactions:
- User: "I want to create a workflow for extracting financial data"
  You: Use generate_workflow tool after getting task details and reference files path

- User: "Edit the workflow to handle quarterly reports differently"
  You: Use edit_workflow tool with their specific requirements

- User: "Test it on sample data", "Test the workflow", "I want to test it", "Run it on a file"
  You: Use test_workflow tool ONLY (do NOT use generate_workflow or load_workflow first)

- User: "How does this workflow handle PDF files?" or "Give me a summary of the workflow"
  You: Use answer_question tool ONLY (do NOT use load_workflow first)

- User: "Load my other workflow" or "Open generated_workflow_x.py"
  You: Use load_workflow tool to switch to a different workflow file

NEVER use load_workflow unless user explicitly wants to switch to a different workflow file.
NEVER use generate_workflow for testing requests - always use test_workflow instead.
"""

# =============================================================================
# SLASH COMMAND HANDLER
# =============================================================================


async def handle_slash_command(ctx: Context, command: str) -> InputRequiredEvent:
    """Handle slash commands like /help and /config"""
    command = command.lower().strip()

    if command == "/help":
        current_model = await ctx.store.get("current_model", "gpt-4.1")
        help_text = f"""
🎵 **LlamaVibe Slash Commands**

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
        config = await ctx.store.get("config")

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
        current_model = await ctx.store.get("current_model")
        if not current_model:
            config = await ctx.store.get("config")
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
    ctx: Context, user_input: str, llm: LLM, tools: list[BaseTool]
) -> ToolCallsEvent | InputRequiredEvent | None:
    """Handle regular chat and determine tool calls"""
    chat_history = await ctx.store.get("chat_history", [])

    # Add user message to history
    chat_history.append(ChatMessage(role=MessageRole.USER, content=user_input))
    await ctx.store.set("chat_history", chat_history)

    # Prepare full chat history with system message
    full_chat_history = [
        ChatMessage(role=MessageRole.SYSTEM, content=AGENT_SYSTEM_PROMPT),
        *chat_history[-10:],  # Keep last 10 messages for context
    ]

    # Show thinking spinner throughout entire response generation
    from rich.console import Console
    from rich.live import Live
    from rich.spinner import Spinner

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
        await ctx.store.set("chat_history", chat_history)

        ctx.write_event_to_stream(
            StreamEvent(  # type: ignore
                rich_content=CLIFormatter.indented_text(
                    "What would you like to do next?"
                ),
                newline_after=True,
            )
        )
        return InputRequiredEvent(prefix="")  # type: ignore


# =============================================================================
# MAIN AI AGENT WORKFLOW
# =============================================================================


class LlamaVibeWorkflow(Workflow):
    """Main LlamaVibe workflow with function calling"""

    def __init__(self, llm: Optional[LLM] = None, verbose: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.llm = llm or OpenAI(model="gpt-4.1")
        self.tools = create_agent_tools()
        self.verbose = verbose

    @step
    async def setup(self, ctx: Context, ev: StartEvent) -> InputRequiredEvent:
        """Initialize configuration and welcome user"""
        # Load or create config
        config = AgentConfig.load_from_file()
        await ctx.store.set("config", config)
        await ctx.store.set("chat_history", [])
        await ctx.store.set("current_workflow", None)
        await ctx.store.set("current_workflow_path", None)
        await ctx.store.set("app_state", "initializing")
        await ctx.store.set("current_model", config.current_model)

        # Initialize LLM based on saved model
        if config.current_model.startswith("claude-"):
            from llama_index.llms.anthropic import Anthropic

            self.llm = Anthropic(
                model=config.current_model, max_tokens=DEFAULT_MAX_TOKENS
            )
        else:
            from llama_index.llms.openai import OpenAI

            self.llm = OpenAI(model=config.current_model)

        if self.verbose:
            ctx.write_event_to_stream(
                StreamEvent(  # type: ignore
                    delta="🤖 vibe-llama docuflows initialized\n"
                )
            )

        # Check configuration
        if not config.project_id or not config.organization_id:
            await ctx.store.set("app_state", "configuring")
            ctx.write_event_to_stream(
                StreamEvent(  # type: ignore
                    rich_content=CLIFormatter.indented_text(
                        "Welcome to LlamaVibe! Let's set up your configuration.\n"
                        "Please provide your LlamaCloud project ID:"
                    ),
                    newline_after=True,
                )
            )
            return InputRequiredEvent(prefix="")  # type: ignore
        else:
            await ctx.store.set("app_state", "ready")
            welcome_msg = f"""Welcome back! I'm ready to help you create document processing workflows.

🚀 **LlamaVibe** transforms your documents into structured data using AI-powered workflows built with LlamaIndex + LlamaCloud.

**Current Configuration:**
  • Project: {config.project_id}
  • Organization: {config.organization_id}
  • Model: {config.current_model}
  • Status: ✅ Connected

**What I can help you build:**
  • Financial data extraction from reports (10-Ks, earnings, etc.)
  • Legal document analysis (contracts, agreements, compliance)
  • Research paper summarization and data extraction
  • Invoice/receipt processing and line item extraction
  • HR document analysis (resumes, reviews, policies)

**Available commands:**
  • **generate workflow** - Create new processing workflows from natural language
  • **edit workflow** - Modify existing workflows with conversational editing
  • **test workflow** - Run workflows on sample documents
  • **help** - Get detailed usage information

What kind of document processing workflow would you like to create?"""

            ctx.write_event_to_stream(
                StreamEvent(  # type: ignore
                    rich_content=CLIFormatter.indented_text(welcome_msg),
                    newline_after=True,
                )
            )
            return InputRequiredEvent(prefix="")  # type: ignore

    @step
    async def handle_general_input(
        self, ctx: Context, ev: HumanResponseEvent
    ) -> InputRequiredEvent | ToolCallsEvent | StopEvent | None:
        """Handle general user input (no tag or general tag)"""
        # Debug: Check if event has a tag
        tag = getattr(ev, "tag", None)
        if DEBUG_MODE:
            debug_print(f"General input received with tag: {tag}")

        # Only handle events without tags or with 'general' tag
        if hasattr(ev, "tag") and ev.tag and ev.tag != "general":
            if DEBUG_MODE:
                debug_print(f"Ignoring tagged event: {ev.tag}")
            return  # Let other steps handle tagged events

        app_state = await ctx.store.get("app_state", "initializing")
        user_input = ev.response.strip()

        # Handle configuration state
        if app_state == "configuring":
            return await handle_configuration(ctx, user_input)

        # Handle quit commands
        if user_input.lower() in ["quit", "exit", "bye"]:
            return StopEvent(result="👋 Goodbye!")

        # Handle slash commands
        if user_input.startswith("/"):
            return await handle_slash_command(ctx, user_input)

        # Handle help
        if user_input.lower() == "help":
            return await handle_help(ctx)

        # Handle regular chat
        return await handle_chat(ctx, user_input, self.llm, self.tools)

    @step
    async def handle_folder_name_input_step(
        self, ctx: Context, ev: HumanResponseEvent
    ) -> InputRequiredEvent | None:
        """Handle workflow folder name input step"""
        # Only handle events with 'folder_name_input' tag
        if not hasattr(ev, "tag") or ev.tag != "folder_name_input":
            return  # Let other steps handle non-folder-name events

        user_input = ev.response.strip()
        default_folder_name = getattr(ev, "default_folder_name", "workflow")

        return await handle_folder_name_input(
            ctx, user_input, default_folder_name, self.llm
        )

    @step
    async def handle_load_workflow_input(
        self, ctx: Context, ev: HumanResponseEvent
    ) -> InputRequiredEvent | None:
        """Handle load workflow file path input step"""
        # Only handle events with 'load_workflow' tag
        if not hasattr(ev, "tag") or ev.tag != "load_workflow":
            return  # Let other steps handle non-load-workflow events

        user_input = ev.response.strip()
        return await handle_load_workflow(ctx, user_input)

    @step
    async def handle_test_file_selection_input(
        self, ctx: Context, ev: HumanResponseEvent
    ) -> InputRequiredEvent | None:
        """Handle test workflow file selection input step"""
        # Only handle events with 'file_selection' tag
        if not hasattr(ev, "tag") or ev.tag != "file_selection":
            return  # Let other steps handle non-file-selection events

        user_input = ev.response.strip()
        available_files = getattr(ev, "available_files", [])
        base_directory = getattr(ev, "base_directory", "")

        return await handle_test_file_selection(
            ctx, user_input, available_files, base_directory, self.llm
        )

    @step
    async def handle_config_menu_input(
        self, ctx: Context, ev: HumanResponseEvent
    ) -> InputRequiredEvent | None:
        """Handle config menu selections"""
        # Only handle events with 'config_menu' tag
        if not hasattr(ev, "tag") or ev.tag != "config_menu":
            return  # Let other steps handle non-config-menu events

        user_input = ev.response.strip().lower()
        config = await ctx.store.get("config")

        if user_input == "done":
            ctx.write_event_to_stream(
                StreamEvent(  # type: ignore
                    delta="✅ Configuration updated!\n"
                )
            )
            ctx.write_event_to_stream(
                StreamEvent(  # type: ignore
                    rich_content=CLIFormatter.indented_text(
                        "What would you like to do?"
                    ),
                    newline_after=True,
                )
            )
            return InputRequiredEvent(prefix="")  # type: ignore

        elif user_input == "reset":
            from vibe_llama.docuflows.ai_agent_cli import AgentConfig

            config = AgentConfig()
            await ctx.store.set("config", config)
            config.save_to_file()
            ctx.write_event_to_stream(
                StreamEvent(  # type: ignore
                    delta="🔄 Configuration reset!\n"
                )
            )
            ctx.write_event_to_stream(
                StreamEvent(  # type: ignore
                    rich_content=CLIFormatter.indented_text(
                        "What would you like to do?"
                    ),
                    newline_after=True,
                )
            )
            return InputRequiredEvent(prefix="")  # type: ignore

        elif user_input == "1":
            return InputRequiredEvent(
                prefix=f"Current Project ID: {config.project_id or '[Not Set]'}\nEnter new Project ID: ",  # type: ignore
                tag="config_edit_project_id",  # type: ignore
            )

        elif user_input == "2":
            return InputRequiredEvent(
                prefix=f"Current Organization ID: {config.organization_id or '[Not Set]'}\nEnter new Organization ID: ",  # type: ignore
                tag="config_edit_org_id",  # type: ignore
            )

        elif user_input == "3":
            return InputRequiredEvent(
                prefix=f"Current Output Directory: {config.output_directory}\nEnter new Output Directory: ",  # type: ignore
                tag="config_edit_output_dir",  # type: ignore
            )

        else:
            ctx.write_event_to_stream(
                StreamEvent(  # type: ignore
                    delta="❌ Invalid option. Please choose 1-3, 'done', or 'reset'.\n"
                )
            )
            return InputRequiredEvent(
                prefix="What would you like to edit? (1-3, done, reset): ",  # type: ignore
                tag="config_menu",  # type: ignore
            )

    @step
    async def handle_config_edit_input(
        self, ctx: Context, ev: HumanResponseEvent
    ) -> InputRequiredEvent | None:
        """Handle individual config field editing"""
        tag = getattr(ev, "tag", None)
        if not tag or not tag.startswith("config_edit_"):
            return  # Let other steps handle non-config-edit events

        user_input = ev.response.strip()
        config = await ctx.store.get("config")

        if tag == "config_edit_project_id":
            if user_input and validate_uuid(user_input):
                config.project_id = user_input
                config.save_to_file()
                await ctx.store.set("config", config)
                ctx.write_event_to_stream(
                    StreamEvent(  # type: ignore
                        delta="✅ Project ID updated!\n"
                    )
                )
            elif user_input:
                ctx.write_event_to_stream(
                    StreamEvent(  # type: ignore
                        delta="❌ Invalid UUID format. Project ID not changed.\n"
                    )
                )
            # Return to config menu
            return await handle_slash_command(ctx, "/config")

        elif tag == "config_edit_org_id":
            if user_input and validate_uuid(user_input):
                config.organization_id = user_input
                config.save_to_file()
                await ctx.store.set("config", config)
                ctx.write_event_to_stream(
                    StreamEvent(  # type: ignore
                        delta="✅ Organization ID updated!\n"
                    )
                )
            elif user_input:
                ctx.write_event_to_stream(
                    StreamEvent(  # type: ignore
                        delta="❌ Invalid UUID format. Organization ID not changed.\n"
                    )
                )
            # Return to config menu
            return await handle_slash_command(ctx, "/config")

        elif tag == "config_edit_output_dir":
            if user_input:
                config.output_directory = user_input
                config.save_to_file()
                await ctx.store.set("config", config)
                ctx.write_event_to_stream(
                    StreamEvent(  # type: ignore
                        delta="✅ Output directory updated!\n"
                    )
                )
            # Return to config menu
            return await handle_slash_command(ctx, "/config")

        ctx.write_event_to_stream(
            StreamEvent(  # type: ignore
                rich_content=CLIFormatter.indented_text("What would you like to do?"),
                newline_after=True,
            )
        )
        return InputRequiredEvent(prefix="")  # type: ignore

    @step
    async def handle_model_selection_input(
        self, ctx: Context, ev: HumanResponseEvent
    ) -> InputRequiredEvent | None:
        """Handle model selection"""
        # Only handle events with 'model_selection' tag
        if not hasattr(ev, "tag") or ev.tag != "model_selection":
            return  # Let other steps handle non-model-selection events

        user_input = ev.response.strip().lower()

        model_map = {
            "1": "gpt-5",
            "2": "gpt-5-mini",
            "3": "gpt-5-nano",
            "4": "gpt-4.1",
            "5": "gpt-4.1-mini",
            "6": "gpt-4o",
            "7": "gpt-4o-mini",
            "8": "claude-sonnet-4-20250514",
            "9": "claude-opus-4-20250514",
            "10": "claude-opus-4-1-20250805",
        }

        if user_input == "cancel":
            ctx.write_event_to_stream(
                StreamEvent(  # type: ignore
                    delta="Model unchanged.\n"
                )
            )
            ctx.write_event_to_stream(
                StreamEvent(  # type: ignore
                    rich_content=CLIFormatter.indented_text(
                        "What would you like to do?"
                    ),
                    newline_after=True,
                )
            )
            return InputRequiredEvent(prefix="")  # type: ignore

        elif user_input in model_map:
            new_model = model_map[user_input]
            await ctx.store.set("current_model", new_model)

            # Save model to config file
            config = await ctx.store.get("config")
            config.current_model = new_model
            config.save_to_file()
            await ctx.store.set("config", config)

            # Update the LLM instance in the workflow
            if new_model.startswith("claude-"):
                from llama_index.llms.anthropic import Anthropic

                self.llm = Anthropic(model=new_model, max_tokens=DEFAULT_MAX_TOKENS)
            else:
                from llama_index.llms.openai import OpenAI

                self.llm = OpenAI(model=new_model)

            ctx.write_event_to_stream(
                StreamEvent(  # type: ignore
                    delta=f"✅ Model updated to {new_model}!\n"
                )
            )
            ctx.write_event_to_stream(
                StreamEvent(  # type: ignore
                    rich_content=CLIFormatter.indented_text(
                        "What would you like to do?"
                    ),
                    newline_after=True,
                )
            )
            return InputRequiredEvent(prefix="")  # type: ignore

        else:
            ctx.write_event_to_stream(
                StreamEvent(  # type: ignore
                    delta="❌ Invalid selection. Please choose 1-10 or 'cancel'.\n"
                )
            )
            return InputRequiredEvent(
                prefix="Select model (1-10) or 'cancel': ",
                tag="model_selection",  # type: ignore
            )

    @step
    async def handle_review_diff_input(
        self, ctx: Context, ev: HumanResponseEvent
    ) -> InputRequiredEvent | None:
        """Handle conversational diff review - approve, refine, or exit"""
        # Only handle events with 'review_diff_conversational' tag
        if not hasattr(ev, "tag") or ev.tag != "review_diff_conversational":
            return  # Let other steps handle non-review-diff events

        user_input = ev.response.strip()

        # Use LLM to interpret user intent
        intent = await interpret_user_intent(user_input, self.llm)

        if intent == "approve":
            # User approved diff - generate runbook
            return await handle_generate_runbook_after_diff(ctx, self.llm)

        elif intent == "exit":
            # User wants to exit editing mode
            ctx.write_event_to_stream(
                StreamEvent(  # type: ignore
                    delta="🔄 Exiting edit mode...\n"
                )
            )

            # Clear pending edits and conversation history
            await ctx.store.set("pending_workflow_edit", None)  # type: ignore
            await ctx.store.set("edit_session_history", None)
            await ctx.store.set("edit_conversation_history", [])

            ctx.write_event_to_stream(
                StreamEvent(  # type: ignore
                    rich_content=CLIFormatter.indented_text(
                        "What would you like to do?"
                    ),
                    newline_after=True,
                )
            )
            return InputRequiredEvent(prefix="")  # type: ignore

        else:  # intent == 'continue'
            # User wants to continue editing - get conversation history
            edit_conversation = await ctx.store.get("edit_conversation_history", [])

            # Continue editing with full conversation context
            ctx.write_event_to_stream(
                StreamEvent(  # type: ignore
                    delta=f"🔄 Refining workflow based on: {user_input}\n"
                )
            )

            # Get current workflow to continue editing
            current_workflow = await ctx.store.get("pending_workflow_edit")
            if not current_workflow:
                current_workflow = await ctx.store.get("current_workflow")

            if not current_workflow:
                ctx.write_event_to_stream(
                    StreamEvent(  # type: ignore
                        delta="❌ No workflow available for further editing.\n"
                    )
                )
                ctx.write_event_to_stream(
                    StreamEvent(  # type: ignore
                        rich_content=CLIFormatter.indented_text(
                            "What would you like to do?"
                        ),
                        newline_after=True,
                    )
                )
                return InputRequiredEvent(prefix="")  # type: ignore

            # Continue editing with structured conversation history
            return await handle_edit_workflow(
                ctx, user_input, self.llm, conversation_history=edit_conversation
            )

    @step
    async def handle_review_edit_input(
        self, ctx: Context, ev: HumanResponseEvent
    ) -> InputRequiredEvent | None:
        """Handle code review confirmation for edited workflows"""
        # Only handle events with 'review_edit' tag
        if not hasattr(ev, "tag") or ev.tag != "review_edit":
            return  # Let other steps handle non-review-edit events

        user_input = ev.response.strip().lower()

        if user_input in ["y", "yes", "save", "ok"]:
            # User approved changes - save them
            pending_workflow = await ctx.store.get("pending_workflow_edit")
            pending_runbook = await ctx.store.get("pending_runbook_edit")

            if pending_workflow:
                # Update context store
                await ctx.store.set("current_workflow", pending_workflow)
                await ctx.store.set("current_runbook", pending_runbook or "")

                # Save to files
                workflow_path = await ctx.store.get("current_workflow_path")
                runbook_path = await ctx.store.get("current_runbook_path")

                if workflow_path:
                    with open(workflow_path, "w") as f:
                        f.write(pending_workflow)
                    ctx.write_event_to_stream(
                        StreamEvent(  # type: ignore
                            delta=f"✅ Updated workflow saved to {workflow_path}\n"
                        )
                    )

                if runbook_path and pending_runbook:
                    with open(runbook_path, "w") as f:
                        f.write(pending_runbook)
                    ctx.write_event_to_stream(
                        StreamEvent(  # type: ignore
                            delta=f"📋 Updated runbook saved to {runbook_path}\n"
                        )
                    )

                # Clear pending edits
                await ctx.store.set("pending_workflow_edit", None)
                await ctx.store.set("pending_runbook_edit", None)

                ctx.write_event_to_stream(
                    StreamEvent(  # type: ignore
                        delta="🎉 Changes saved successfully!\n"
                    )
                )

                # Set status message for chat history
                await ctx.store.set(
                    "handler_status_message",
                    "Successfully saved workflow edits. The updated workflow and runbook are now active.",
                )

            ctx.write_event_to_stream(
                StreamEvent(  # type: ignore
                    rich_content=CLIFormatter.indented_text(
                        "Workflow updated! What would you like to do next?"
                    ),
                    newline_after=True,
                )
            )
            return InputRequiredEvent(prefix="")  # type: ignore

        else:
            # User rejected changes
            ctx.write_event_to_stream(
                StreamEvent(  # type: ignore
                    delta="❌ Changes discarded.\n"
                )
            )

            # Clear pending edits
            await ctx.store.set("pending_workflow_edit", None)
            await ctx.store.set("pending_runbook_edit", None)

            ctx.write_event_to_stream(
                StreamEvent(  # type: ignore
                    rich_content=CLIFormatter.indented_text(
                        "What would you like to do?"
                    ),
                    newline_after=True,
                )
            )
        return InputRequiredEvent(prefix="")  # type: ignore

    @step
    async def handle_test_workflow_input(
        self, ctx: Context, ev: HumanResponseEvent
    ) -> InputRequiredEvent | None:
        """Handle test workflow file path input.


        This step is triggered when the user is explicitly asking to test the workflow, and needs to provide a file path.

        """
        # Debug: Check if event has the right tag
        tag = getattr(ev, "tag", None)
        if DEBUG_MODE:
            debug_print(f"Test workflow input received with tag: {tag}")

        # Only handle events with 'test_workflow' tag
        if not hasattr(ev, "tag") or ev.tag != "test_workflow":
            if DEBUG_MODE:
                debug_print(f"Test workflow step ignoring event with tag: {tag}")
            return  # Let other steps handle non-test-workflow events

        if DEBUG_MODE:
            debug_print(f"Processing test workflow input: {ev.response}")
        user_input = ev.response.strip()
        return await handle_test_workflow(ctx, user_input, self.llm)

    @step
    async def execute_tools(
        self, ctx: Context, ev: ToolCallsEvent
    ) -> InputRequiredEvent | None:
        """Execute tool calls and route to appropriate handlers"""
        chat_history = await ctx.store.get("chat_history", [])

        for tool_call in ev.tool_calls:
            tool_name = tool_call.tool_name
            tool_args = tool_call.tool_kwargs

            # Execute the tool and get action description
            result = None
            for tool in self.tools:
                if tool.metadata.name == tool_name:
                    result = tool(**tool_args)
                    break

            if result:
                try:
                    # Extract content from ToolOutput
                    result_content = result.content
                    action_data = json.loads(result_content)
                    action = action_data.get("action")

                    # Clear any previous status message
                    await ctx.store.set("handler_status_message", None)

                    if action == "generate_workflow":
                        handler_result = await handle_generate_workflow(
                            ctx,
                            action_data.get("task", ""),
                            action_data.get("reference_files_path", ""),
                            self.llm,
                        )
                    elif action == "edit_workflow":
                        handler_result = await handle_edit_workflow(
                            ctx, action_data.get("edit_request", ""), self.llm
                        )
                    elif action == "test_workflow":
                        handler_result = await handle_test_workflow(
                            ctx, action_data.get("test_file_path", ""), self.llm
                        )
                    elif action == "answer_question":
                        handler_result = await handle_answer_question(
                            ctx, action_data.get("question", ""), self.llm
                        )
                    elif action == "show_config":
                        handler_result = await handle_show_config(ctx)
                    elif action == "reconfigure":
                        handler_result = await handle_reconfigure(ctx)
                    elif action == "load_workflow":
                        handler_result = await handle_load_workflow(
                            ctx, action_data.get("workflow_path", "")
                        )
                    else:
                        ctx.write_event_to_stream(
                            StreamEvent(  # type: ignore
                                rich_content=CLIFormatter.indented_text(
                                    "What would you like to do next?"
                                ),
                                newline_after=True,
                            )
                        )
                        handler_result = InputRequiredEvent(prefix="")  # type: ignore

                    # Check if handler set a status message and add it to chat history
                    status_message = await ctx.store.get("handler_status_message")
                    if status_message:
                        chat_history.append(
                            ChatMessage(
                                role=MessageRole.ASSISTANT, content=status_message
                            )
                        )
                        await ctx.store.set("chat_history", chat_history)
                        await ctx.store.set("handler_status_message", None)  # Clear it

                    return handler_result

                except json.JSONDecodeError:
                    ctx.write_event_to_stream(
                        StreamEvent(  # type: ignore
                            delta="❌ Error parsing tool result\n"
                        )
                    )

        ctx.write_event_to_stream(
            StreamEvent(  # type: ignore
                rich_content=CLIFormatter.indented_text(
                    "What would you like to do next?"
                ),
                newline_after=True,
            )
        )
        return InputRequiredEvent(prefix="")  # type: ignore


# =============================================================================
# CLI INTERFACE
# =============================================================================


async def run_cli():
    """Run the interactive CLI with rich formatting"""
    # Initialize workflow
    llm = OpenAI(model="gpt-4.1")
    workflow = LlamaVibeWorkflow(llm=llm, verbose=True, timeout=None)

    # Start the workflow
    handler = workflow.run()

    # Code streaming state
    code_buffer = ""
    live_code_panel = None

    try:
        async for event in handler.stream_events():
            # Handle human input requests
            if isinstance(event, InputRequiredEvent):
                # Close any active code panel before input
                if live_code_panel:
                    live_code_panel.stop()
                    console.print()  # Add spacing after code panel
                    live_code_panel = None
                    code_buffer = ""

                # Use our custom async boxed input
                prompt_text = event.prefix.rstrip()
                response = await boxed_input_async(prompt_text)

                # Preserve all custom attributes from InputRequiredEvent
                response_kwargs = {"response": response}
                if hasattr(event, "tag") and event.tag:
                    response_kwargs["tag"] = event.tag
                if hasattr(event, "available_files"):
                    response_kwargs["available_files"] = event.available_files
                if hasattr(event, "base_directory"):
                    response_kwargs["base_directory"] = event.base_directory
                if hasattr(event, "default_folder_name"):
                    response_kwargs["default_folder_name"] = event.default_folder_name

                response_event = HumanResponseEvent(**response_kwargs)
                handler.ctx.send_event(response_event)  # type: ignore

            # Handle streaming output with rich formatting
            elif isinstance(event, StreamEvent):
                if event.is_code:
                    # Handle streaming code with live panel
                    code_buffer += event.delta

                    # Apply tail-following: show only last N lines if content is too long
                    max_display_lines = (
                        console.size.height - 15
                    )  # Leave space for UI elements
                    lines = code_buffer.split("\n")

                    if len(lines) > max_display_lines:
                        # Show tail of the code
                        visible_lines = lines[-max_display_lines:]
                        display_code = "\n".join(visible_lines)
                        hidden_lines = len(lines) - max_display_lines
                        display_code = (
                            f"# ... ({hidden_lines} lines above)\n" + display_code
                        )
                        title = f"🔧 Generating Workflow Code... (showing last {max_display_lines}/{len(lines)} lines)"
                    else:
                        display_code = code_buffer
                        title = f"🔧 Generating Workflow Code... ({len(lines)} lines)"

                    if not live_code_panel:
                        from rich.live import Live

                        live_code_panel = Live(
                            CLIFormatter.code_output(display_code, title),
                            refresh_per_second=8,
                            console=console,
                        )
                        live_code_panel.start()
                    else:
                        live_code_panel.update(
                            CLIFormatter.code_output(display_code, title)
                        )
                elif event.rich_content:
                    # Close code panel if switching to rich content
                    if live_code_panel:
                        live_code_panel.stop()
                        console.print()  # Add spacing after code panel
                        live_code_panel = None
                        code_buffer = ""

                    console.print(event.rich_content)
                    if event.newline_after:
                        console.print()
                else:
                    # Close code panel if switching to plain text
                    if live_code_panel:
                        live_code_panel.stop()
                        console.print()  # Add spacing after code panel
                        live_code_panel = None
                        code_buffer = ""

                    # Handle plain text streaming
                    print(event.delta, end="", flush=True)

        # Get final result
        result = await handler

        # Close any remaining code panel
        if live_code_panel:
            live_code_panel.stop()
            console.print()

        if result:
            console.print(f"\n{result}")

    except KeyboardInterrupt:
        # Close code panel on interrupt
        try:
            if "live_code_panel" in locals() and live_code_panel:
                live_code_panel.stop()
        except Exception:
            pass
        console.print("\n\n👋 Goodbye!", style="bold yellow")
    except Exception as e:
        # Close code panel on error
        try:
            if "live_code_panel" in locals() and live_code_panel:
                live_code_panel.stop()
        except Exception:
            pass
        console.print(CLIFormatter.error(f"Error: {str(e)}"))
