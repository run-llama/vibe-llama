"""
Other handlers for AI Agent CLI.

Contains configuration, Q&A, workflow loading, and utility handlers.
"""

import os

from llama_index.core.llms import LLM, MessageRole
from llama_index.core.prompts import ChatMessage
from workflows import Context
from workflows.events import InputRequiredEvent

from vibe_llama.docuflows.utils import (
    CLIFormatter,
    StreamEvent,
    clean_file_path,
    validate_workflow_path,
)


def validate_uuid(uuid_string: str) -> bool:
    """Validate if a string is a proper UUID format"""
    try:
        import uuid

        uuid.UUID(uuid_string)
        return True
    except ValueError:
        return False


async def handle_configuration(
    ctx: Context, user_input: str
) -> InputRequiredEvent | None:
    """Handle configuration setup"""
    config = await ctx.store.get("config")

    if not config.project_id:
        if not validate_uuid(user_input):
            ctx.write_event_to_stream(
                StreamEvent(  # type: ignore
                    delta="❌ Invalid project ID format. Please provide a valid UUID.\n"
                )
            )
            ctx.write_event_to_stream(
                StreamEvent(delta="Example: 12345678-1234-1234-1234-123456789abc\n")  # type: ignore
            )
            return InputRequiredEvent(
                prefix="Please provide your LlamaCloud project ID: "  # type: ignore
            )

        config.project_id = user_input
        config.save_to_file()
        await ctx.store.set("config", config)
        return InputRequiredEvent(
            prefix="Great! Now please provide your organization ID: "  # type: ignore
        )

    if config.project_id and not config.organization_id:
        if not validate_uuid(user_input):
            ctx.write_event_to_stream(
                StreamEvent(  # type: ignore
                    delta="❌ Invalid organization ID format. Please provide a valid UUID.\n"
                )
            )
            ctx.write_event_to_stream(
                StreamEvent(delta="Example: 12345678-1234-1234-1234-123456789abc\n")  # type: ignore
            )
            return InputRequiredEvent(prefix="Please provide your organization ID: ")  # type: ignore

        config.organization_id = user_input
        config.save_to_file()
        await ctx.store.set("config", config)
        await ctx.store.set("app_state", "ready")
        ctx.write_event_to_stream(StreamEvent(delta="✅ Configuration saved!\n"))  # type: ignore
        return InputRequiredEvent(
            prefix="Perfect! Now, what would you like to do?\n"  # type: ignore
            "(Examples: 'generate a workflow', 'edit workflow', 'help'): "
        )


async def handle_help(ctx: Context) -> InputRequiredEvent:
    """Show help information"""
    help_text = """
🤖 AI Agent CLI Help:

Available actions:
- **Generate workflow**: Create a new workflow from a task description
  Example: "Generate a workflow for extracting income statements from 10-K reports"

- **Load workflow**: Load an existing workflow from a file
  Example: "Load my previous workflow", "Open generated_workflow_maritime.py"

- **Edit workflow**: Modify the current workflow
  Example: "Edit the workflow to handle quarterly reports better"

- **Test workflow**: Test current workflow on sample data
  Example: "Test the workflow on my sample PDF file"

- **Ask questions**: Ask about the current workflow
  Example: "How does this workflow handle table extraction?"

- **Show config**: Display current configuration
- **Reconfigure**: Reset and reconfigure credentials (useful for fixing invalid project/org IDs)
- **Help**: Show this help message
- **Quit/exit**: Exit the CLI

For workflow generation, I'll need:
1. A clear description of what you want the workflow to do
2. Path to directory containing reference files
    """
    ctx.write_event_to_stream(StreamEvent(delta=help_text))  # type: ignore
    return InputRequiredEvent(prefix="\nWhat would you like to do? ")  # type: ignore


async def handle_answer_question(
    ctx: Context, question: str, llm: LLM
) -> InputRequiredEvent:
    """Answer questions about the current workflow with full context"""
    current_workflow = await ctx.store.get("current_workflow")

    if not current_workflow:
        ctx.write_event_to_stream(
            StreamEvent(delta="❌ No workflow loaded to ask questions about.\n")  # type: ignore
        )
        return InputRequiredEvent(prefix="What would you like to do? ")  # type: ignore

    if not question:
        return InputRequiredEvent(
            prefix="What would you like to know about the workflow? "  # type: ignore
        )

    try:
        # Use full workflow context (no truncation)
        qa_messages = [
            ChatMessage(
                role=MessageRole.SYSTEM,
                content="You are an expert at explaining LlamaIndex workflow code. Answer the user's question about the workflow clearly and helpfully.",
            ),
            ChatMessage(
                role=MessageRole.USER,
                content=f"""Based on this workflow code, please answer the user's question:

Workflow Code:
```python
{current_workflow}
```

User Question: {question}

Please provide a helpful and detailed answer about the workflow, referencing specific parts of the code when relevant.""",
            ),
        ]

        ctx.write_event_to_stream(StreamEvent(delta=f"🤔 {question}\n\n🤖 "))  # type: ignore

        qa_response = await llm.astream_chat(qa_messages)
        async for r in qa_response:
            if r.delta:
                ctx.write_event_to_stream(StreamEvent(delta=r.delta))  # type: ignore

        # Set status message for chat history
        await ctx.store.set(
            "handler_status_message",
            f"Answered question about the workflow: '{question}'",
        )

        return InputRequiredEvent(
            prefix="\n\nAny other questions? Or what would you like to do next? "  # type: ignore
        )

    except Exception as e:
        ctx.write_event_to_stream(
            StreamEvent(delta=f"❌ Error answering question: {str(e)}\n")  # type: ignore
        )
        # Set error status message for chat history
        await ctx.store.set(
            "handler_status_message",
            f"Failed to answer question due to error: {str(e)}",
        )

        return InputRequiredEvent(
            prefix="Please try asking again. What would you like to do? "  # type: ignore
        )


async def handle_show_config(ctx: Context) -> InputRequiredEvent:
    """Show current configuration"""
    config = await ctx.store.get("config")
    config_text = f"""
Current Configuration:
- Project ID: {config.project_id}
- Organization ID: {config.organization_id}
- Default Reference Files: {config.default_reference_files_path or "Not set"}
- Output Directory: {config.output_directory}
    """
    ctx.write_event_to_stream(StreamEvent(delta=config_text))  # type: ignore
    # Set status message for chat history
    await ctx.store.set(
        "handler_status_message", "Displayed current configuration settings."
    )

    return InputRequiredEvent(prefix="\nWhat would you like to do next? ")  # type: ignore


async def handle_reconfigure(ctx: Context) -> InputRequiredEvent:
    """Handle reconfiguration of credentials"""
    from vibe_llama.docuflows.ai_agent_cli import (
        AgentConfig,
    )

    # Reset configuration state
    config = AgentConfig()
    await ctx.store.set("config", config)
    await ctx.store.set("app_state", "configuring")

    ctx.write_event_to_stream(StreamEvent(delta="🔄 Reconfiguring credentials...\n"))  # type: ignore
    # Set status message for chat history
    await ctx.store.set(
        "handler_status_message",
        "Reset configuration and started reconfiguration process.",
    )

    return InputRequiredEvent(prefix="Please provide your LlamaCloud project ID: ")  # type: ignore


async def handle_load_workflow(ctx: Context, workflow_path: str) -> InputRequiredEvent:
    """Load an existing workflow from file"""

    if not workflow_path:
        # Show available workflow files in current directory
        workflow_files = []
        for file in os.listdir("."):
            if file.endswith(".py") and (
                "workflow" in file.lower() or file.startswith("generated_")
            ):
                workflow_files.append(file)

        if workflow_files:
            ctx.write_event_to_stream(
                StreamEvent(delta="📁 Available workflow files:\n")  # type: ignore
            )
            for i, file in enumerate(workflow_files[:10], 1):
                ctx.write_event_to_stream(StreamEvent(delta=f"  {i}. {file}\n"))  # type: ignore
            ctx.write_event_to_stream(StreamEvent(delta="\n"))  # type: ignore

        return InputRequiredEvent(
            prefix="Please provide the path to the workflow file to load: ",  # type: ignore
            tag="load_workflow",  # type: ignore
            available_files=workflow_files,  # type: ignore
        )

    # Clean and validate the workflow path with intelligent path resolution
    cleaned_path = clean_file_path(workflow_path)
    is_valid, actual_path, error_msg = validate_workflow_path(cleaned_path)

    if not is_valid:
        ctx.write_event_to_stream(StreamEvent(delta=error_msg + "\n"))  # type: ignore
        return InputRequiredEvent(
            prefix="Please provide a valid workflow path (folder or .py file): ",  # type: ignore
            tag="load_workflow",  # type: ignore
        )

    # Use the actual resolved path
    cleaned_path = actual_path

    try:
        # Read the workflow file
        with open(cleaned_path) as f:
            workflow_code = f.read()

        # Store as current workflow
        await ctx.store.set("current_workflow", workflow_code)
        await ctx.store.set("current_workflow_path", cleaned_path)

        # Try to load runbook if it exists in the same directory
        workflow_dir = os.path.dirname(cleaned_path)
        runbook_path = os.path.join(workflow_dir, "runbook.md")
        if os.path.exists(runbook_path):
            with open(runbook_path) as f:
                runbook_content = f.read()
            await ctx.store.set("current_runbook", runbook_content)
            await ctx.store.set("current_runbook_path", runbook_path)

        ctx.write_event_to_stream(
            StreamEvent(delta=f"✅ Loaded workflow from: {cleaned_path}\n")  # type: ignore
        )

        # Display the loaded code in a formatted panel with truncation
        max_lines = 50  # Show first 50 lines
        lines = workflow_code.split("\n")

        if len(lines) > max_lines:
            # Truncate and show first 50 lines with indicator
            truncated_code = "\n".join(lines[:max_lines])
            truncated_code += (
                f"\n\n# ... truncated ({len(lines) - max_lines} more lines)"
            )
            title = f"📄 Loaded Workflow Code (showing {max_lines}/{len(lines)} lines)"
        else:
            truncated_code = workflow_code
            title = f"📄 Loaded Workflow Code ({len(lines)} lines)"

        ctx.write_event_to_stream(
            StreamEvent(  # type: ignore
                delta="",
                rich_content=CLIFormatter.code_output(truncated_code, title),
                newline_after=True,
            )
        )

        # Set status message for chat history
        await ctx.store.set(
            "handler_status_message",
            f"Successfully loaded workflow from {cleaned_path}. The workflow is now active and ready for testing, editing, or questions.",
        )

        return InputRequiredEvent(
            prefix="\nWorkflow loaded! You can now:\n"  # type: ignore
            "- Edit the workflow\n"
            "- Test it on sample data\n"
            "- Ask questions about it\n"
            "- Generate a new workflow\n"
            "- Load a different workflow\n"
            "What would you like to do? "
        )

    except Exception as e:
        ctx.write_event_to_stream(
            StreamEvent(delta=f"❌ Error loading workflow: {str(e)}\n")  # type: ignore
        )
        return InputRequiredEvent(
            prefix="Please try again. What would you like to do? "  # type: ignore
        )
