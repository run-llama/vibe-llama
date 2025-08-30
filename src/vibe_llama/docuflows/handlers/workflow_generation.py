"""
Workflow generation handler for AI Agent CLI.

Handles generating new workflows from natural language descriptions.
"""

import os
import re

from typing import cast
from llama_index.core.llms import LLM, MessageRole
from llama_index.core.prompts import ChatPromptTemplate
from llama_index.core.prompts import ChatMessage
from workflows import Context
from workflows.events import InputRequiredEvent

from vibe_llama.docuflows.commons.core import (
    DocumentComplexityAssessment,
    create_workflow_folder,
    generate_runbook,
    generate_workflow,
    save_runbook,
    save_workflow,
)
from vibe_llama.docuflows.commons import (
    CLIFormatter,
    StreamEvent,
    clean_file_path,
    validate_reference_path,
)
from vibe_llama.docuflows.agent.utils import AgentConfig
from vibe_llama.docuflows.commons.typed_state import WorkflowState


async def assess_document_complexity(
    task: str,
    reference_files_path: str,
    llm: LLM,
    ctx: Context[WorkflowState] | None = None,
) -> DocumentComplexityAssessment:
    """Assess document complexity to recommend appropriate parse/extract configurations"""

    # Examine files in reference directory
    file_info = []
    if os.path.isfile(reference_files_path):
        file_info = [reference_files_path]
    elif os.path.isdir(reference_files_path):
        for file in sorted(os.listdir(reference_files_path)):
            if os.path.isfile(
                os.path.join(reference_files_path, file)
            ) and not file.startswith("."):
                file_info.append(os.path.join(reference_files_path, file))

    # Limit to first 15 files to keep prompt manageable
    if len(file_info) > 15:
        file_info = file_info[:15] + [f"... and {len(file_info) - 15} more files"]

    files_str = "\n".join(file_info) if file_info else "No files found"

    complexity_prompt = """Analyze this document processing task and reference files to recommend LlamaParse and LlamaExtract configurations.

TASK: {task}

REFERENCE FILES:
{files_str}

PARSE MODE OPTIONS:
- cost_effective: Good for simple text/table docs with lightweight OCR
- agentic: Good for general docs including some visualizations/charts
- agentic_plus: For complex docs requiring pinpoint accuracy

EXTRACT MODE OPTIONS:
- BALANCED: Good for simpler extraction tasks and simpler documents
- MULTIMODAL: Default option, good for visually rich documents
- PREMIUM: For complex extraction tasks with complex documents/schemas

ADDITIONAL FEATURES:
- citations: If task mentions citing sources, attributing data, referencing sections
- reasoning: ALWAYS set to False by default (performance issues), but user can enable later if needed

Consider:
1. File names indicating complexity (scan, chart, complex, financial, SEC, etc.)
2. File types (PDFs with charts = more complex than plain text)
3. Task complexity (simple extraction vs complex analysis)
4. Whether citations are explicitly mentioned (but always keep reasoning=False)
5. Keep parse and extract quality levels consistent

Provide recommendations with brief reasoning. NOTE: Always set needs_reasoning=False regardless of task complexity."""

    chat_template = ChatPromptTemplate(
        [ChatMessage.from_str(complexity_prompt, "user")]
    )

    if ctx:
        ctx.write_event_to_stream(
            StreamEvent(  # type: ignore
                rich_content=CLIFormatter.indented_text(
                    "🔍 Assessing document complexity for optimal configuration..."
                ),
                newline_after=True,
            )
        )

    try:
        result = await llm.astructured_predict(
            DocumentComplexityAssessment, chat_template, task=task, files_str=files_str
        )
        return result
    except Exception:
        # Fallback to moderate complexity if assessment fails
        return DocumentComplexityAssessment(
            complexity_level="moderate",
            parse_mode="agentic",
            extract_mode="MULTIMODAL",
            needs_citations=False,
            needs_reasoning=False,  # Always False by default due to performance issues
            reasoning="Fallback to moderate complexity due to assessment error",
        )


async def handle_generate_workflow(
    ctx: Context[WorkflowState], task: str, reference_files_path: str, llm: LLM
) -> InputRequiredEvent:
    """Generate a new workflow"""
    config = cast(AgentConfig, (await ctx.store.get_state()).config)

    if not task:
        examples_text = """
📋 Example workflow tasks:

• "Extract the full consolidated income statement information from quarterly reports. Make sure it covers general income information you can find for any company."

• "Split document by market sector, and extract the list of companies and each company's financials for each market sector."

• "Extract key financial metrics (revenue, profit margins, growth rates) from annual reports, organized by business segment."

• "Parse contracts to extract parties, key terms, important dates, and compliance requirements."

• "Extract methodology, datasets, results, and key findings from research papers, including performance metrics."
        """
        ctx.write_event_to_stream(
            StreamEvent(  # type: ignore
                rich_content=CLIFormatter.indented_text(examples_text),
                newline_after=True,
            )
        )
        return InputRequiredEvent(
            prefix="\n💡 Describe what you want the workflow to do: "  # type: ignore
        )

    if not reference_files_path:
        return InputRequiredEvent(
            prefix="Please provide the path to your reference files.\n"  # type: ignore
            "This can be:\n"
            "• A directory containing sample files (e.g., /path/to/reports/ or ./examples/)\n"
            "• A specific file to use as reference (e.g., /path/to/sample.pdf or ./data/report.pdf)\n"
            "• Use @ symbol for path completion (e.g., @data/ then press Tab)\n\n"
            "Path: "
        )

    # Clean the reference files path (remove @ symbol if present)
    cleaned_path = clean_file_path(reference_files_path)

    # Validate reference files path with helpful suggestions
    is_valid, error_msg, suggestions = validate_reference_path(cleaned_path)
    if not is_valid:
        full_error = error_msg
        if suggestions:
            full_error += "\n\n" + suggestions
        ctx.write_event_to_stream(
            StreamEvent(  # type: ignore
                rich_content=CLIFormatter.indented_text(full_error), newline_after=True
            )
        )
        return InputRequiredEvent(
            prefix="Please provide a valid path to your reference files.\n"  # type: ignore
            "This can be a directory containing sample files or a specific sample file.\n"
            "Use @ symbol for path completion (e.g., @data/ then press Tab)\n\n"
            "Path: "
        )

    # Show tool action with bold formatting - no truncation
    ctx.write_event_to_stream(
        StreamEvent(  # type: ignore
            rich_content=CLIFormatter.tool_action("GenerateWorkflow", f"task='{task}'"),
            newline_after=True,
        )
    )
    # All subsequent outputs should be indented
    ctx.write_event_to_stream(
        StreamEvent(  # type: ignore
            rich_content=CLIFormatter.indented_text(f"📋 Task: {task}"),
            newline_after=True,
        )
    )
    # Determine if it's a file or directory and show appropriate message
    if os.path.isfile(cleaned_path):
        ctx.write_event_to_stream(
            StreamEvent(  # type: ignore
                rich_content=CLIFormatter.indented_text(
                    f"📄 Reference file: {cleaned_path}"
                ),
                newline_after=True,
            )
        )
        # Pass the actual file path for single files
        reference_files_path = cleaned_path
    else:
        ctx.write_event_to_stream(
            StreamEvent(  # type: ignore
                rich_content=CLIFormatter.indented_text(
                    f"📁 Reference files directory: {cleaned_path}"
                ),
                newline_after=True,
            )
        )
        reference_files_path = cleaned_path

    try:
        # Assess document complexity first
        complexity = await assess_document_complexity(task, cleaned_path, llm, ctx)

        # Display complexity assessment to user
        ctx.write_event_to_stream(
            StreamEvent(  # type: ignore
                rich_content=CLIFormatter.important_text(
                    f"📊 Document Complexity: {complexity.complexity_level.title()}\n"
                    f"🔧 Parse Mode: {complexity.parse_mode}\n"
                    f"⚙️ Extract Mode: {complexity.extract_mode}\n"
                    f"💭 Reasoning: {complexity.reasoning}"
                ),
                newline_after=True,
            )
        )

        # Generate the workflow with complexity recommendations
        workflow_code = await generate_workflow(
            task,
            reference_files_path=cleaned_path,
            project_id=config.project_id,
            organization_id=config.organization_id,
            complexity_assessment=complexity,
            ctx=ctx,
            llm=llm,
        )

        ctx.write_event_to_stream(
            StreamEvent(  # type: ignore
                rich_content=CLIFormatter.status_update(
                    "✅ Workflow generated successfully!"
                ),
                newline_after=True,
            )
        )

        # Generate business runbook
        ctx.write_event_to_stream(
            StreamEvent(  # type: ignore
                rich_content=CLIFormatter.status_update(
                    "📋 Generating business runbook..."
                ),
                newline_after=True,
            )
        )

        runbook_content = await generate_runbook(workflow_code, task, llm, ctx)

        # Display the full runbook
        ctx.write_event_to_stream(
            StreamEvent(  # type: ignore
                rich_content=CLIFormatter.workflow_summary(runbook_content),
                newline_after=True,
            )
        )

        # Add clear visual separator after runbook
        ctx.write_event_to_stream(
            StreamEvent(  # type: ignore
                rich_content=CLIFormatter.subtle_text("└─ End of runbook"),
                newline_after=True,
            )
        )

        # Store the workflow and generation context (after runbook is generated)
        async with ctx.store.edit_state() as state:
            state.current_workflow = workflow_code
            state.current_runbook = runbook_content
            state.generation_task = task
            state.generation_reference_path = reference_files_path

        # Store the workflow and runbook temporarily (don't save to file yet)
        async with ctx.store.edit_state() as state:
            state.pending_workflow = workflow_code
            state.pending_runbook = runbook_content
            state.pending_task = task

        # Generate a default folder name suggestion
        safe_task_name = re.sub(r"[^\w\s-]", "", task)[:40].strip().replace(" ", "_")
        default_folder_name = safe_task_name if safe_task_name else "workflow"

        # Ask user for folder name with default option
        # Set status message for chat history
        async with ctx.store.edit_state() as state:
            state.handler_status_message = f"Successfully generated workflow for task: '{task}'. The workflow and runbook are ready to be saved."

        ctx.write_event_to_stream(
            StreamEvent(  # type: ignore
                rich_content=CLIFormatter.important_text(
                    f"📁 What would you like to name this workflow folder?\n"
                    f"Press Enter for default: '{default_folder_name}'\n"
                    f"Or describe what you'd like to call it:"
                ),
                newline_after=True,
            )
        )

        return InputRequiredEvent(
            prefix="",  # type: ignore
            tag="folder_name_input",  # type: ignore
            default_folder_name=default_folder_name,  # type: ignore
        )

    except Exception as e:
        error_msg = str(e)
        ctx.write_event_to_stream(
            StreamEvent(  # type: ignore
                rich_content=CLIFormatter.indented_text(
                    f"❌ Error generating workflow: {error_msg}"
                ),
                newline_after=True,
            )
        )

        # Check for credential-related errors
        if "uuid_parsing" in error_msg or "Invalid UUID" in error_msg:
            help_text = """💡 This looks like a credential issue. Your project_id or organization_id may be invalid.

You can:
1. Type 'reconfigure' to reset your credentials
2. Type 'show config' to check your current configuration"""

            ctx.write_event_to_stream(
                StreamEvent(  # type: ignore
                    rich_content=CLIFormatter.indented_text(help_text),
                    newline_after=True,
                )
            )

        # Set error status message for chat history
        async with ctx.store.edit_state() as state:
            state.handler_status_message = (
                f"Failed to generate workflow due to error: {error_msg}"
            )

        ctx.write_event_to_stream(
            StreamEvent(  # type: ignore
                rich_content=CLIFormatter.indented_text("What would you like to do?"),
                newline_after=True,
            )
        )
        return InputRequiredEvent(prefix="")  # type: ignore


async def handle_folder_name_input(
    ctx: Context[WorkflowState], user_input: str, default_folder_name: str, llm: LLM
) -> InputRequiredEvent:
    """Handle workflow folder name input with LLM conversion"""

    # Use default if user just pressed Enter or provided empty input
    if not user_input:
        final_folder_name = default_folder_name
        ctx.write_event_to_stream(
            StreamEvent(  # type: ignore
                rich_content=CLIFormatter.indented_text(
                    f"Using default folder name: {final_folder_name}"
                ),
                newline_after=True,
            )
        )
    else:
        # Use LLM to convert natural language to folder name
        folder_messages = [
            ChatMessage(
                role=MessageRole.SYSTEM,
                content="You are a helpful assistant that converts natural language descriptions into clean folder names. Keep folder names short, descriptive, and use underscores instead of spaces. No file extensions.",
            ),
            ChatMessage(
                role=MessageRole.USER,
                content=f"Convert this description to a folder name: '{user_input}'\nJust return the folder name, nothing else.",
            ),
        ]

        ctx.write_event_to_stream(
            StreamEvent(  # type: ignore
                rich_content=CLIFormatter.indented_text(
                    f"🤔 Converting '{user_input}' to folder name..."
                ),
                newline_after=True,
            )
        )

        folder_response = await llm.achat(folder_messages)
        suggested_folder_name = folder_response.message.content.strip()  # type: ignore

        # Clean up the suggested folder name
        suggested_folder_name = re.sub(r"[^\w\.-]", "_", suggested_folder_name)

        final_folder_name = suggested_folder_name
        ctx.write_event_to_stream(
            StreamEvent(  # type: ignore
                rich_content=CLIFormatter.indented_text(
                    f"Generated folder name: {final_folder_name}"
                ),
                newline_after=True,
            )
        )

    # Create the workflow folder
    config = cast(AgentConfig, (await ctx.store.get_state()).config)
    output_dir = getattr(config, "output_directory", "generated_workflows")
    folder_path = create_workflow_folder(final_folder_name, output_dir)

    # Save the workflow and runbook to the folder
    pending_workflow = (await ctx.store.get_state()).pending_workflow
    pending_runbook = (await ctx.store.get_state()).pending_runbook

    workflow_file_path = os.path.join(folder_path, "workflow.py")
    runbook_file_path = os.path.join(folder_path, "runbook.md")

    save_workflow(cast(str, pending_workflow), workflow_file_path, ctx)
    save_runbook(cast(str, pending_runbook), runbook_file_path, ctx)

    # Update context store
    async with ctx.store.edit_state() as state:
        state.current_workflow = pending_workflow
        state.current_runbook = pending_runbook
        state.current_workflow_path = workflow_file_path
        state.current_runbook_path = runbook_file_path
        state.current_folder_path = folder_path

    # Clear pending data
    async with ctx.store.edit_state() as state:
        state.pending_workflow = None
        state.pending_runbook = None
        state.pending_task = None

    ctx.write_event_to_stream(
        StreamEvent(  # type: ignore
            rich_content=CLIFormatter.indented_text(
                f"📁 Created folder: {folder_path}"
            ),
            newline_after=True,
        )
    )
    ctx.write_event_to_stream(
        StreamEvent(  # type: ignore
            rich_content=CLIFormatter.indented_text(
                f"💾 Saved workflow to: {workflow_file_path}"
            ),
            newline_after=True,
        )
    )
    ctx.write_event_to_stream(
        StreamEvent(  # type: ignore
            rich_content=CLIFormatter.indented_text(
                f"📋 Saved runbook to: {runbook_file_path}"
            ),
            newline_after=True,
        )
    )

    # Set status message for chat history
    async with ctx.store.edit_state() as state:
        state.handler_status_message = f"Successfully saved workflow to {folder_path}. The workflow is now ready for testing, editing, or questions."

    ctx.write_event_to_stream(
        StreamEvent(  # type: ignore
            rich_content=CLIFormatter.indented_text(
                "Workflow ready! You can now:\n"
                "- Edit the workflow or runbook\n"
                "- Test it on sample data\n"
                "- Ask questions about it\n"
                "- Generate a new workflow\n"
                "What would you like to do?"
            ),
            newline_after=True,
        )
    )

    return InputRequiredEvent(prefix="")  # type: ignore
