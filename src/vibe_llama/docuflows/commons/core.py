"""
Core functionality for LlamaIndex workflow generation.

This module contains shared functions used by both the simple script generator
and the AI agent CLI for generating document processing workflows.
"""

import os
import re
from pathlib import Path

from rich.console import Console
from rich.live import Live
from rich.spinner import Spinner
from llama_cloud_services import LlamaParse

from llama_index.core.llms import LLM
from llama_index.core.prompts import ChatMessage, ChatPromptTemplate
from llama_index.llms.openai import OpenAI
from pydantic import BaseModel, Field

# Import for event streaming (optional to support legacy usage)
from workflows import Context
from . import StreamEvent
from vibe_llama.sdk import VibeLlamaStarter

from vibe_llama.docuflows.prompts import (
    RUNBOOK_GENERATION_PROMPT,
    WORKFLOW_GENERATION_PROMPT,
)
from . import CLIFormatter
from vibe_llama.docuflows.commons.typed_state import WorkflowState

# Environment Variables for the generator
DEFAULT_PROJECT_ID = os.environ.get("LLAMA_CLOUD_PROJECT_ID", "your-project-id")
DEFAULT_ORGANIZATION_ID = os.environ.get("LLAMA_CLOUD_ORG_ID", "your-organization-id")

# Initialize default LLM for code generation
DEFAULT_LLM = OpenAI(model="gpt-5")
DOCS_STARTER = VibeLlamaStarter(
    agents=["vibe-llama docuflows"],
    services=["llama-index-workflows", "LlamaCloud Services"],
)


async def get_docs():
    await DOCS_STARTER.write_instructions()


class DocumentComplexityAssessment(BaseModel):
    """Assessment of document complexity for parse/extract config recommendations"""

    complexity_level: str = Field(
        ..., description="One of: 'simple', 'moderate', 'complex'"
    )
    parse_mode: str = Field(
        ...,
        description="Recommended parse mode: 'cost_effective', 'agentic', 'agentic_plus'",
    )
    extract_mode: str = Field(
        ..., description="Recommended extract mode: 'BALANCED', 'MULTIMODAL', 'PREMIUM'"
    )
    needs_citations: bool = Field(
        ..., description="Whether the task mentions needing citations"
    )
    needs_reasoning: bool = Field(
        ..., description="Whether the task would benefit from reasoning"
    )
    reasoning: str = Field(
        ..., description="Brief explanation of the complexity assessment"
    )


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def _send_event(
    ctx: Context[WorkflowState] | None,  # type: ignore
    message: str,
    end: str = "\n",
    flush: bool = True,
    is_code: bool = False,
):
    """Send an event or print message depending on context availability"""
    if ctx:
        if is_code:
            ctx.write_event_to_stream(StreamEvent(delta=message + end, is_code=is_code))  # type: ignore
        else:
            ctx.write_event_to_stream(
                StreamEvent(
                    rich_content=CLIFormatter.indented_text(message),
                    newline_after=True,  # type: ignore
                )
            )
    else:
        print(message, end=end, flush=flush)


# =============================================================================
# CORE FUNCTIONS
# =============================================================================


async def load_context_files(
    ctx: Context[WorkflowState] | None = None,  # type: ignore
) -> str:
    """
    Load specific priority context files for workflow generation

    Args:
        ctx: Optional context for event streaming

    Returns:
        Content of the documentation about LlamaIndex Workflows and LlamaCloud Services
    """

    try:
        # Check if AGENTS.md exists
        if not os.path.exists(".vibe-llama/rules/AGENTS.md"):
            _send_event(
                ctx,
                "Warning: '.vibe-llama/rules/AGENTS.md' not found, generating it...",
            )
            await get_docs()

        with open(".vibe-llama/rules/AGENTS.md", "r") as f:
            content = f.read()

    except Exception as e:
        _send_event(ctx, f"Error loading context files: {e}")
        return f"Error loading context files: {e}"

    return content


async def load_reference_files(
    reference_files_path: str | None = None,
    project_id: str | None = None,
    organization_id: str | None = None,
    ctx: Context[WorkflowState] | None = None,  # type: ignore
) -> str:
    """
    Load and parse reference files using LlamaParse

    Args:
        reference_files_path: Path to directory containing reference files
        project_id: LlamaCloud project ID
        organization_id: LlamaCloud organization ID
        ctx: Optional context for event streaming

    Returns:
        Combined content of parsed reference files
    """
    if not reference_files_path:
        return "No reference files provided"

    # Check if we have valid project and org IDs
    if (
        not project_id
        or not organization_id
        or project_id == "your-project-id"
        or organization_id == "your-organization-id"
    ):
        _send_event(ctx, "ERROR: Invalid project_id or organization_id provided.")
        _send_event(
            ctx, "Please provide valid LlamaCloud credentials to parse reference files."
        )
        raise RuntimeError(
            "Invalid project_id or organization_id for reference file parsing"
        )

    reference_files = []

    try:
        # Check if directory exists
        if not os.path.exists(reference_files_path):
            _send_event(
                ctx, f"Warning: Reference directory '{reference_files_path}' not found"
            )
            return "No reference files found"

        # Initialize LlamaParse for reference files (premium_mode=False for cost efficiency)

        parser = LlamaParse(
            premium_mode=False,  # Use free mode for reference files
            result_type="markdown",  # type: ignore
            project_id=project_id,
            organization_id=organization_id,
        )

        # Handle both single files and directories
        if os.path.isfile(reference_files_path):
            # Single file case
            directory_path = os.path.dirname(reference_files_path)
            filename = os.path.basename(reference_files_path)
            all_files = [filename]
            actual_reference_path = directory_path
        else:
            # Directory case
            all_files = [
                f
                for f in os.listdir(reference_files_path)
                if os.path.isfile(os.path.join(reference_files_path, f))
            ]
            actual_reference_path = reference_files_path

        # Filter out system files and keep only supported document types
        supported_extensions = {
            ".pdf",
            ".doc",
            ".docx",
            ".txt",
            ".rtf",
            ".html",
            ".htm",
            ".xlsx",
            ".xls",
            ".csv",
            ".ppt",
            ".pptx",
        }
        files = []
        for f in all_files:
            if f.startswith("."):  # Skip hidden/system files like .DS_Store
                continue
            ext = os.path.splitext(f.lower())[1]
            if (
                ext in supported_extensions or not ext
            ):  # Include files without extension for manual review
                files.append(f)

        if not files:
            _send_event(
                ctx,
                f"Warning: No supported reference files found in '{reference_files_path}'",
            )
            _send_event(
                ctx,
                f"Found {len(all_files)} total files, but none were supported document types",
            )
            return "No reference files found"

        # Parse each file
        for filename in sorted(files):
            file_path = os.path.join(actual_reference_path, filename)
            try:
                _send_event(ctx, f"Parsing reference file: {filename}")

                # Parse the file using LlamaParse
                result = await parser.aparse(file_path)
                markdown_nodes = await result.aget_markdown_nodes(split_by_page=True)  # type: ignore

                # Combine all nodes into a single text
                parsed_content = "\n\n".join(
                    [node.get_content(metadata_mode="all") for node in markdown_nodes]  # type: ignore
                )

                reference_files.append(f"REFERENCE_FILE_{filename}:\n{parsed_content}")
                _send_event(ctx, f"Successfully parsed: {filename}")

            except Exception as e:
                _send_event(
                    ctx, f"ERROR: Failed to parse reference file {filename}: {e}"
                )
                _send_event(
                    ctx,
                    "This is a critical error. Please check your LlamaCloud credentials and file format.",
                )
                raise RuntimeError(f"Failed to parse reference file {filename}: {e}")

    except Exception as e:
        _send_event(ctx, f"CRITICAL ERROR loading reference files: {e}")
        raise RuntimeError(f"Failed to load reference files: {e}")

    return "\n\n".join(reference_files)


def extract_python_code(response_text: str) -> str:
    """
    Extract Python code from LLM response, removing any markdown or commentary

    Args:
        response_text: Raw response from LLM

    Returns:
        Clean Python code
    """
    # Remove markdown code blocks if present
    code_pattern = r"```python\s*(.*?)\s*```"
    matches = re.findall(code_pattern, response_text, re.DOTALL)

    if matches:
        # Return the first code block found
        return matches[0].strip()

    # If no code blocks found, try to extract just the Python code
    # Look for import statements and assume everything after is code
    import_pattern = r"(import.*?)(.*)"
    import_match = re.search(import_pattern, response_text, re.DOTALL)

    if import_match:
        return import_match.group(0).strip()

    # If all else fails, return the whole response
    return response_text.strip()


async def generate_workflow(
    user_task: str,
    reference_files_path: str | None = None,
    project_id: str | None = None,
    organization_id: str | None = None,
    complexity_assessment: DocumentComplexityAssessment | None = None,
    llm: LLM | None = None,
    ctx: Context[WorkflowState] | None = None,  # type: ignore
) -> str:
    """
    Generate a complete workflow based on user task

    Args:
        user_task: Natural language description of the task
        data_files_path: Path to directory containing context files
        reference_files_path: Path to directory containing reference files
        project_id: LlamaCloud project ID
        organization_id: LlamaCloud organization ID
        llm: LLM instance to use (defaults to DEFAULT_LLM)
        ctx: Optional context for event streaming

    Returns:
        Generated workflow code as string
    """
    # Use provided IDs or defaults
    project_id = project_id or DEFAULT_PROJECT_ID
    organization_id = organization_id or DEFAULT_ORGANIZATION_ID
    llm = llm or DEFAULT_LLM

    # Load context and reference files
    context_str = await load_context_files(ctx)
    reference_files_content = await load_reference_files(
        reference_files_path, project_id, organization_id, ctx
    )

    # Create chat prompt template
    chat_template = ChatPromptTemplate(
        [ChatMessage.from_str(WORKFLOW_GENERATION_PROMPT, "user")]
    )

    # Determine current model name from LLM metadata
    current_model = llm.metadata.model_name

    # Prepare complexity guidance
    complexity_guidance = ""
    if complexity_assessment:
        complexity_guidance = f"""
CONFIGURATION RECOMMENDATIONS (based on document complexity analysis):
- Parse Mode: {complexity_assessment.parse_mode}
- Extract Mode: {complexity_assessment.extract_mode}
- Citations: {"Required" if complexity_assessment.needs_citations else "Not required"}
- Reasoning: {"Recommended" if complexity_assessment.needs_reasoning else "Not required"}
- Complexity Level: {complexity_assessment.complexity_level}
- Assessment Reasoning: {complexity_assessment.reasoning}

USE THESE RECOMMENDATIONS when configuring LlamaParse and ExtractConfig in your generated code.
"""

    # Generate workflow using LLM with streaming
    messages = chat_template.format_messages(
        context_str=context_str,
        reference_files_content=reference_files_content,
        user_task=user_task,
        project_id=project_id,
        organization_id=organization_id,
        current_model=current_model,
        complexity_guidance=complexity_guidance,
    )

    use_spinner = ctx and StreamEvent
    if use_spinner:
        console = Console()
        spinner = Spinner("dots", text="Generating workflow code...")

        resp = await llm.astream_chat(messages)
        response_text = ""
        first_token = True

        with Live(spinner, refresh_per_second=10, console=console) as live:
            async for delta in resp:
                if first_token:
                    # Stop spinner and start streaming tokens
                    live.stop()
                    first_token = False

                response_text += delta.delta  # type: ignore
                # Stream token to user via events after spinner stops
                if not first_token:
                    _send_event(ctx, delta.delta, end="", flush=True, is_code=True)  # type: ignore

    if not use_spinner:
        if ctx and StreamEvent:
            ctx.write_event_to_stream(
                StreamEvent(
                    rich_content=CLIFormatter.indented_text(
                        "⏳ Generating workflow code..."
                    ),
                    newline_after=True,
                )
            )
        else:
            print("⏳ Generating workflow code...")
        resp = await llm.astream_chat(messages)
        response_text = ""
        async for delta in resp:
            response_text += delta.delta  # type: ignore
            # Show streaming tokens
            _send_event(ctx, delta.delta, end="", flush=True, is_code=True)  # type: ignore

    if ctx and StreamEvent:
        ctx.write_event_to_stream(
            StreamEvent(
                rich_content=CLIFormatter.indented_text("🔍 Extracting Python code..."),
                newline_after=True,
            )
        )
    else:
        print("\n\n🔍 Extracting Python code...")

    # Debug: Save raw response to file
    with open("debug_response.txt", "w", encoding="utf-8") as f:
        f.write("=== RAW LLM RESPONSE ===\n")
        f.write(response_text)  # type: ignore
        f.write("\n\n=== RESPONSE LENGTH ===\n")
        f.write(f"Length: {len(response_text)} characters\n")  # type: ignore

    if ctx and StreamEvent:
        ctx.write_event_to_stream(
            StreamEvent(
                rich_content=CLIFormatter.indented_text(
                    f"📝 Raw response saved to debug_response.txt ({len(response_text)} characters)"  # type: ignore
                ),
                newline_after=True,
            )
        )
    else:
        print(
            f"📝 Raw response saved to debug_response.txt ({len(response_text)} characters)"  # type: ignore
        )

    # Extract clean Python code
    python_code = extract_python_code(response_text)  # type: ignore

    # Debug: Save extracted code to file
    with open("debug_extracted_code.txt", "w", encoding="utf-8") as f:
        f.write("=== EXTRACTED PYTHON CODE ===\n")
        f.write(python_code)
        f.write("\n\n=== CODE LENGTH ===\n")
        f.write(f"Length: {len(python_code)} characters\n")

    if ctx and StreamEvent:
        ctx.write_event_to_stream(
            StreamEvent(
                rich_content=CLIFormatter.indented_text(
                    f"💾 Extracted code saved to debug_extracted_code.txt ({len(python_code)} characters)"
                ),
                newline_after=True,
            )
        )
    else:
        print(
            f"💾 Extracted code saved to debug_extracted_code.txt ({len(python_code)} characters)"
        )

    return python_code


async def generate_runbook(
    workflow_code: str,
    user_task: str,
    llm: LLM | None = None,
    ctx: Context[WorkflowState] | None = None,  # type: ignore
) -> str:
    """
    Generate a business-focused runbook from workflow code

    Args:
        workflow_code: The generated workflow Python code
        user_task: Original user task description
        llm: LLM instance to use (defaults to DEFAULT_LLM)
        ctx: Optional context for event streaming

    Returns:
        Generated runbook content as markdown string
    """
    llm = llm or DEFAULT_LLM

    # Create chat prompt template for runbook generation
    chat_template = ChatPromptTemplate(
        [ChatMessage.from_str(RUNBOOK_GENERATION_PROMPT, "user")]
    )

    # Generate runbook using LLM
    response_text = ""

    resp = await llm.astream_chat(
        chat_template.format_messages(workflow_code=workflow_code, user_task=user_task)
    )

    async for delta in resp:
        response_text += delta.delta  # type: ignore

    return response_text.strip()


def save_workflow(
    workflow_code: str,
    output_path: str = "generated_workflow.py",
    ctx: Context[WorkflowState] | None = None,  # type: ignore
):
    """
    Save the generated workflow to a file

    Args:
        workflow_code: Generated workflow code
        output_path: Path to save the workflow
        ctx: Optional context for event streaming
    """
    with open(output_path, "w") as f:
        f.write(workflow_code)
    if ctx and StreamEvent:
        ctx.write_event_to_stream(
            StreamEvent(
                rich_content=CLIFormatter.indented_text(
                    f"Workflow saved to {output_path}"
                ),
                newline_after=True,
            )
        )
    else:
        print(f"Workflow saved to {output_path}")


def save_runbook(
    runbook_content: str,
    output_path: str = "runbook.md",
    ctx: Context[WorkflowState] | None = None,  # type: ignore
):
    """
    Save the generated runbook to a file

    Args:
        runbook_content: Generated runbook content
        output_path: Path to save the runbook
        ctx: Optional context for event streaming
    """
    with open(output_path, "w") as f:
        f.write(runbook_content)
    if ctx and StreamEvent:
        ctx.write_event_to_stream(
            StreamEvent(
                rich_content=CLIFormatter.indented_text(
                    f"Runbook saved to {output_path}"
                ),
                newline_after=True,
            )
        )
    else:
        print(f"Runbook saved to {output_path}")


def create_workflow_folder(
    base_name: str, output_dir: str = "generated_workflows"
) -> str:
    """
    Create a folder for workflow outputs with a clean name

    Args:
        base_name: Base name for the folder (will be cleaned)
        output_dir: Parent directory for all generated workflows

    Returns:
        Path to the created folder
    """
    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(exist_ok=True)

    # Clean the base name for use as folder name
    clean_name = re.sub(r"[^\w\s-]", "", base_name)[:50].strip().replace(" ", "_")
    if not clean_name:
        clean_name = "workflow"

    # Create unique folder name if it already exists
    folder_path = Path(output_dir) / clean_name
    counter = 1
    while folder_path.exists():
        folder_path = Path(output_dir) / f"{clean_name}_{counter}"
        counter += 1

    # Create the folder
    folder_path.mkdir(exist_ok=True)
    return str(folder_path)
