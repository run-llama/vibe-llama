#!/usr/bin/env python3
from llama_index.llms.openai import OpenAI

# Rich imports for beautiful CLI formatting
from rich.console import Console
from rich.live import Live

# Workflows imports
from workflows.events import (
    HumanResponseEvent,
    InputRequiredEvent,
)

from .commons import CLIFormatter
from .agent import LlamaVibeWorkflow

# Import utility classes
from .commons import StreamEvent, boxed_input_async

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

# Initialize rich console
console = Console()


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
