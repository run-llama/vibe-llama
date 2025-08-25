import os

from workflows import Context
from workflows.events import InputRequiredEvent

from vibe_llama.docuflows.commons import (
    CLIFormatter,
    StreamEvent,
    clean_file_path,
    validate_workflow_path,
)
from vibe_llama.docuflows.commons.typed_state import WorkflowState


async def handle_load_workflow(
    ctx: Context[WorkflowState], workflow_path: str
) -> InputRequiredEvent:
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
        async with ctx.store.edit_state() as state:
            state.current_workflow = workflow_code
            state.current_workflow_path = cleaned_path

        # Try to load runbook if it exists in the same directory
        workflow_dir = os.path.dirname(cleaned_path)
        runbook_path = os.path.join(workflow_dir, "runbook.md")
        if os.path.exists(runbook_path):
            with open(runbook_path) as f:
                runbook_content = f.read()
            async with ctx.store.edit_state() as state:
                state.current_runbook = runbook_content
                state.current_runbook_path = runbook_path

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
        async with ctx.store.edit_state() as state:
            state.handler_status_message = f"Successfully loaded workflow from {cleaned_path}. The workflow is now active and ready for testing, editing, or questions."

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
