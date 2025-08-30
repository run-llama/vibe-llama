import json
from typing import Optional, cast

from llama_index.core.llms import LLM, MessageRole
from llama_index.core.prompts import ChatMessage
from llama_index.llms.openai import OpenAI
from llama_index.llms.anthropic import Anthropic

# Rich imports for beautiful CLI formatting
from rich.console import Console

# Workflows imports
from workflows import Context, Workflow, step
from workflows.events import (
    HumanResponseEvent,
    InputRequiredEvent,
    StartEvent,
    StopEvent,
)

from vibe_llama.docuflows.commons.constants import DEFAULT_MAX_TOKENS
from vibe_llama.docuflows.commons import CLIFormatter
from vibe_llama.docuflows.tools import create_agent_tools
from .utils import (
    handle_chat,
    handle_slash_command,
    AgentConfig,
    debug_print,
    ToolCallsEvent,
    DEBUG_MODE,
)
from vibe_llama.docuflows.commons.typed_state import WorkflowState

# Import the shared workflow generation functions
from vibe_llama.docuflows.handlers.workflow_help import (
    handle_answer_question,
    handle_help,
)

from vibe_llama.docuflows.handlers.workflow_config import (
    handle_configuration,
    handle_reconfigure,
    handle_show_config,
)

from vibe_llama.docuflows.handlers.workflow_load import (
    handle_load_workflow,
)

from vibe_llama.docuflows.handlers.workflow_editing import (
    handle_edit_workflow,
    handle_generate_runbook_after_diff,
    interpret_user_intent,
)

# Import handlers from separate modules
from vibe_llama.docuflows.handlers.workflow_generation import (
    handle_folder_name_input,
    handle_generate_workflow,
)
from vibe_llama.docuflows.handlers.workflow_testing import (
    handle_test_file_selection,
    handle_test_workflow,
)

# Import utility classes
from vibe_llama.docuflows.commons import StreamEvent, validate_uuid, is_file_path

# Initialize rich console
console = Console()

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
    async def setup(
        self, ctx: Context[WorkflowState], ev: StartEvent
    ) -> InputRequiredEvent:
        """Initialize configuration and welcome user"""
        # Load or create config
        config = AgentConfig.load_from_file()
        async with ctx.store.edit_state() as state:
            state.config = config
            state.chat_history = []
            state.current_workflow = None
            state.current_workflow_path = None
            state.app_state = "initializing"
            state.current_model = config.current_model
        # Initialize LLM based on saved model
        if config.current_model.startswith("claude-"):
            self.llm = Anthropic(
                model=config.current_model, max_tokens=DEFAULT_MAX_TOKENS
            )
        else:
            self.llm = OpenAI(model=config.current_model)

        if self.verbose:
            ctx.write_event_to_stream(
                StreamEvent(  # type: ignore
                    delta="🤖 vibe-llama docuflows initialized\n"
                )
            )

        # Check configuration
        if not config.project_id or not config.organization_id:
            async with ctx.store.edit_state() as state:
                state.app_state = "configuring"
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
            async with ctx.store.edit_state() as state:
                state.app_state = "ready"
            welcome_msg = f"""Welcome back! I'm ready to help you create document processing workflows.

🚀 **vibe-llama docuflows** transforms your documents into structured data using AI-powered workflows built with LlamaIndex + LlamaCloud.

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
        self, ctx: Context[WorkflowState], ev: HumanResponseEvent
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

        app_state = (await ctx.store.get_state()).app_state
        user_input = ev.response.strip()

        # Handle configuration state
        if app_state == "configuring":
            return await handle_configuration(ctx, user_input)

        # Handle quit commands
        if user_input.lower() in ["quit", "exit", "bye"]:
            return StopEvent(result="👋 Goodbye!")

        # Handle slash commands (but not file paths)
        if user_input.startswith("/") and not is_file_path(user_input):
            return await handle_slash_command(ctx, user_input)

        # Handle help
        if user_input.lower() == "help":
            return await handle_help(ctx)

        # Handle regular chat
        return await handle_chat(ctx, user_input, self.llm, self.tools)

    @step
    async def handle_folder_name_input_step(
        self, ctx: Context[WorkflowState], ev: HumanResponseEvent
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
        self, ctx: Context[WorkflowState], ev: HumanResponseEvent
    ) -> InputRequiredEvent | None:
        """Handle load workflow file path input step"""
        # Only handle events with 'load_workflow' tag
        if not hasattr(ev, "tag") or ev.tag != "load_workflow":
            return  # Let other steps handle non-load-workflow events

        user_input = ev.response.strip()
        return await handle_load_workflow(ctx, user_input)

    @step
    async def handle_test_file_selection_input(
        self, ctx: Context[WorkflowState], ev: HumanResponseEvent
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
        self, ctx: Context[WorkflowState], ev: HumanResponseEvent
    ) -> InputRequiredEvent | None:
        """Handle config menu selections"""
        # Only handle events with 'config_menu' tag
        if not hasattr(ev, "tag") or ev.tag != "config_menu":
            return  # Let other steps handle non-config-menu events

        user_input = ev.response.strip().lower()
        config = cast(Optional[AgentConfig], (await ctx.store.get_state()).config)

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
            config = AgentConfig()
            async with ctx.store.edit_state() as state:
                state.config = config
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
        self, ctx: Context[WorkflowState], ev: HumanResponseEvent
    ) -> InputRequiredEvent | None:
        """Handle individual config field editing"""
        tag = getattr(ev, "tag", None)
        if not tag or not tag.startswith("config_edit_"):
            return  # Let other steps handle non-config-edit events

        user_input = ev.response.strip()
        config = cast(AgentConfig, (await ctx.store.get_state()).config)

        if tag == "config_edit_project_id":
            if user_input and validate_uuid(user_input):
                config.project_id = user_input
                config.save_to_file()
                async with ctx.store.edit_state() as state:
                    state.config = config
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
                async with ctx.store.edit_state() as state:
                    state.config = config
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
                async with ctx.store.edit_state() as state:
                    state.config = config
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
        self, ctx: Context[WorkflowState], ev: HumanResponseEvent
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
            async with ctx.store.edit_state() as state:
                state.current_model = new_model

            # Save model to config file
            config = cast(AgentConfig, (await ctx.store.get_state()).config)
            config.current_model = new_model
            config.save_to_file()
            async with ctx.store.edit_state() as state:
                state.config = config

            # Update the LLM instance in the workflow
            if new_model.startswith("claude-"):
                self.llm = Anthropic(model=new_model, max_tokens=DEFAULT_MAX_TOKENS)
            else:
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
        self, ctx: Context[WorkflowState], ev: HumanResponseEvent
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
            async with ctx.store.edit_state() as state:
                state.pending_workflow_edit = None
                state.edit_session_history = None
                state.edit_conversation_history = []

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
            edit_conversation = (await ctx.store.get_state()).edit_conversation_history

            # Continue editing with full conversation context
            ctx.write_event_to_stream(
                StreamEvent(  # type: ignore
                    delta=f"🔄 Refining workflow based on: {user_input}\n"
                )
            )

            # Get current workflow to continue editing
            current_workflow = (await ctx.store.get_state()).pending_workflow_edit
            if not current_workflow:
                current_workflow = (await ctx.store.get_state()).current_workflow

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
        self, ctx: Context[WorkflowState], ev: HumanResponseEvent
    ) -> InputRequiredEvent | None:
        """Handle code review confirmation for edited workflows"""
        # Only handle events with 'review_edit' tag
        if not hasattr(ev, "tag") or ev.tag != "review_edit":
            return  # Let other steps handle non-review-edit events

        user_input = ev.response.strip().lower()

        if user_input in ["y", "yes", "save", "ok"]:
            # User approved changes - save them
            pending_workflow = (await ctx.store.get_state()).pending_workflow_edit
            pending_runbook = (await ctx.store.get_state()).pending_runbook_edit

            if pending_workflow:
                # Update context store
                async with ctx.store.edit_state() as state:
                    state.current_workflow = pending_workflow
                    state.current_runbook = pending_runbook or ""

                # Save to files
                workflow_path = (await ctx.store.get_state()).current_workflow_path
                runbook_path = (await ctx.store.get_state()).current_runbook_path

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
                async with ctx.store.edit_state() as state:
                    state.pending_runbook_edit = None
                    state.pending_workflow_edit = None
                    state.handler_status_message = "Successfully saved workflow edits. The updated workflow and runbook are now active."

                ctx.write_event_to_stream(
                    StreamEvent(  # type: ignore
                        delta="🎉 Changes saved successfully!\n"
                    )
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
            async with ctx.store.edit_state() as state:
                state.pending_runbook_edit = None
                state.pending_workflow_edit = None

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
        self, ctx: Context[WorkflowState], ev: HumanResponseEvent
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
        self, ctx: Context[WorkflowState], ev: ToolCallsEvent
    ) -> InputRequiredEvent | None:
        """Execute tool calls and route to appropriate handlers"""
        chat_history = (await ctx.store.get_state()).chat_history

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
                    async with ctx.store.edit_state() as state:
                        state.handler_status_message = None

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
                    status_message = (
                        await ctx.store.get_state()
                    ).handler_status_message
                    if status_message:
                        chat_history.append(
                            ChatMessage(
                                role=MessageRole.ASSISTANT, content=status_message
                            )
                        )
                        async with ctx.store.edit_state() as state:
                            state.chat_history = chat_history
                            state.handler_status_message = None

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
