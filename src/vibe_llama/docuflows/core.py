"""
Core functionality for LlamaIndex workflow generation.

This module contains shared functions used by both the simple script generator
and the AI agent CLI for generating document processing workflows.
"""

import os
import re

from llama_index.core.llms import LLM
from llama_index.core.prompts import ChatMessage, ChatPromptTemplate
from llama_index.llms.openai import OpenAI
from pydantic import BaseModel, Field

# Import for event streaming (optional to support legacy usage)
try:
    from workflows import Context

    from .utils import StreamEvent
except ImportError:
    Context = None
    StreamEvent = None

# Environment Variables for the generator
DEFAULT_PROJECT_ID = os.environ.get("LLAMA_CLOUD_PROJECT_ID", "your-project-id")
DEFAULT_ORGANIZATION_ID = os.environ.get("LLAMA_CLOUD_ORG_ID", "your-organization-id")

# Initialize default LLM for code generation
DEFAULT_LLM = OpenAI(model="gpt-5")


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
    ctx: Context | None,  # type: ignore
    message: str,
    end: str = "\n",
    flush: bool = True,
    is_code: bool = False,
):
    """Send an event or print message depending on context availability"""
    if ctx and StreamEvent:
        from .utils import CLIFormatter

        if is_code:
            ctx.write_event_to_stream(StreamEvent(delta=message + end, is_code=is_code))
        else:
            ctx.write_event_to_stream(
                StreamEvent(
                    rich_content=CLIFormatter.indented_text(message), newline_after=True
                )
            )
    else:
        print(message, end=end, flush=flush)


# =============================================================================
# CORE FUNCTIONS
# =============================================================================


def load_context_files(
    data_files_path: str = "core/data_files",
    ctx: Context | None = None,  # type: ignore
) -> str:
    """
    Load specific priority context files for workflow generation

    Args:
        data_files_path: Path to directory containing context files
        ctx: Optional context for event streaming

    Returns:
        Combined content of priority context files only
    """
    context_files = []

    # Priority files for workflow generation (in order of importance)
    priority_files = [
        "llama-index-workflows.md",
        "asset_manager_fund_analysis.md",
        "workflow_template.py",
        "extract_data_with_citations.md",
        "extract_config_options.md",
    ]

    try:
        # Check if directory exists
        if not os.path.exists(data_files_path):
            _send_event(ctx, f"Warning: Directory '{data_files_path}' not found")
            return "No context files found"

        # Load only priority files
        for filename in priority_files:
            file_path = os.path.join(data_files_path, filename)
            if os.path.exists(file_path):
                try:
                    with open(file_path, encoding="utf-8") as f:
                        content = f.read()
                        context_files.append(f"{filename}:\n{content}")
                        # Debug only - don't show to user: _send_event(ctx, f"Loaded: {filename}")
                except Exception as e:
                    _send_event(ctx, f"Warning: Could not read {filename}: {e}")
                    context_files.append(f"{filename}: Error reading file - {e}")
            else:
                _send_event(ctx, f"Warning: Priority file not found: {filename}")

        if not context_files:
            _send_event(ctx, f"Warning: No priority files found in '{data_files_path}'")
            return "No context files found"

    except Exception as e:
        _send_event(ctx, f"Error loading context files: {e}")
        return f"Error loading context files: {e}"

    return "\n\n".join(context_files)


async def load_reference_files(
    reference_files_path: str | None = None,
    project_id: str | None = None,
    organization_id: str | None = None,
    ctx: Context | None = None,  # type: ignore
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
        from llama_cloud_services import LlamaParse

        parser = LlamaParse(
            premium_mode=False,  # Use free mode for reference files
            result_type="markdown",  # type: ignore
            project_id=project_id,
            organization_id=organization_id,
        )

        # Get all files in the directory, excluding system files and unsupported formats
        all_files = [
            f
            for f in os.listdir(reference_files_path)
            if os.path.isfile(os.path.join(reference_files_path, f))
        ]

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
            file_path = os.path.join(reference_files_path, filename)
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


# =============================================================================
# WORKFLOW GENERATION PROMPTS
# =============================================================================

RUNBOOK_GENERATION_PROMPT = """
You are a business process analyst who creates precise, actionable runbooks for document processing workflows.

Given a Python workflow code, create a business-focused runbook that shows users exactly what they'll get from this workflow. The runbook should be concrete and specific enough that users can determine if the output meets their needs before running it.

WORKFLOW CODE:
```python
{workflow_code}
```

USER TASK DESCRIPTION:
{user_task}

Create a runbook with the following structure:

# Document Processing Runbook

## Overview
[Brief description of what this workflow accomplishes from a business perspective]

## Input Requirements
[What documents or files are needed - be specific about formats, types, content requirements]

## Processing Steps

### Step 1: [Document Parsing/Loading]
[Explain what happens to input documents and why this step is necessary]

### Step 2: [Main Processing Step - extraction, analysis, etc.]
[Explain the core processing logic and what gets captured/analyzed]

### Step 3: [Additional steps as needed]
[Continue for each major processing step, focusing on business value]

## Output Specification

### Output Format
[Specify exactly what format the output takes - CSV file, JSON structure, text summary, etc.]

### Data Structure
[For structured outputs like CSV/JSON, include a detailed schema table showing every field]

**Column/Field Schema:**
| Field | Type | Description | Example |
|-------|------|-------------|---------|
[List every column/field with type, clear description, and realistic example]

**Sample Output:**
```
[Include actual sample output showing the exact format users will receive]
```

### Output Characteristics
- **Granularity**: [One record per document? Per section? Per data point?]
- **Data Types**: [What types of information - text, numbers, categories, dates, etc.]
- **Completeness**: [What gets included vs. excluded, how missing data is handled]

## Expected Data Fields
[List the specific types of information that will be captured, organized by category]

**[Category 1]:**
- [Specific field 1]: [What this contains and format]
- [Specific field 2]: [What this contains and format]

**[Category 2]:**
- [Additional fields as relevant]

## Usage Guidelines
- **Best Results**: [What document types/formats work best]
- **Limitations**: [What won't work well or key constraints]
- **Customization**: [What can be easily modified or adjusted]

CRITICAL REQUIREMENTS:
- Be CONCRETE and SPECIFIC - show users exactly what output format and data fields they'll receive
- Include REALISTIC EXAMPLES based on the actual code structure and data schema
- For structured outputs (CSV, JSON), ALWAYS include the detailed schema table with every field/column
- Make it clear what the workflow will and won't capture
- Focus on actionable details that help users evaluate if this meets their needs
- Write for business users but be precise about technical outputs
- KEEP IT CONCISE - aim for under 400 words total, use bullet points, avoid verbose explanations
- Each section should be 2-4 sentences maximum, focus on essential information only

The runbook should give users complete clarity on what they'll receive in a quick, scannable format that allows them to make informed decisions about using or modifying the workflow.

Output the runbook in markdown format.
"""

WORKFLOW_GENERATION_PROMPT = """
You are an assistant who is tasked with creating a document workflow through code.
- You are supposed to use LlamaIndex to orchestrate a workflow.
- You are to take in a natural language input describing a task to be done. You are then supposed to build the workflow.
- You are allowed to use a core set of building blocks, like parsing, extraction, as described through code.
- You are supposed to fill in workflow_template.py with the final workflow with the LlamaIndex workflow syntax.

IMPORTANT: Output ONLY the Python code that should go in the generated_workflow.py file. Do not include any markdown formatting, explanations, or commentary in the code block. The code should be ready to run immediately.

You are given a set of context that describes the following:
- A lot of files describing the overall syntax of LlamaIndex workflows.
- An example complete tutorial notebook ("asset_manager_fund_analysis.md") which shows users how to build a functional e2e workflow using LlamaIndex workflows + core components around parsing + extraction.
    - This notebook takes in a fidelity report, splits it, and then outputs a consolidated dataframe.
- A workflow_template.py - this is the code template you are supposed to fill out. Output a final code file that preserves existing functions, but also generates the final workflow.

Below, we describe all the context. We also present the user task.

>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> CONTEXT >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
{context_str}
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> END CONTEXT >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> REFERENCE FILES >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
{reference_files_content}
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> END REFERENCE FILES >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

{complexity_guidance}

>>>> Modules
As you can see from workflow_template.py and asset_manager_fund_analysis.md, here are the modules you're allowed to use:
- LlamaParse
    - As you can see from the example, this converts an input doc into markdown text.
- LlamaExtract
    - note: if you want to use LlamaExtract, you will need to infer the Pydantic schema from the user task.
    - You can enter the definition of the Pydantic schema in your generated code, and feed that to LlamaExtract
- LLMs
    - You can use LLMs to analyze outputs, reason, and generate final results.
    - Please use the LlamaIndex wrappers provided.
    - For OpenAI models: `from llama_index.llms.openai import OpenAI`
    - For Anthropic models: `from llama_index.llms.anthropic import Anthropic`
    - Use the model name provided in the template to determine which LLM class to use
- document_utils.py
    - Contains utility functions for document splitting: `afind_categories_and_splits`, `afind_split_categories`, `afind_splits`, etc.
    - Import with: `from core.document_utils import afind_categories_and_splits`
    - Only import if splitting is needed in the workflow

>>>> Configuration
Use these values for project_id and organization_id:
- project_id: "{project_id}"
- organization_id: "{organization_id}"

Current LLM model: "{current_model}"
- If the model starts with "gpt-", use: `from llama_index.llms.openai import OpenAI` and `llm = OpenAI(model="{current_model}")`
- If the model starts with "claude-", use: `from llama_index.llms.anthropic import Anthropic` and `llm = Anthropic(model="{current_model}")`

>>>> User task:
{user_task}

>>>> END USER TASK

Output ONLY the Python code that should go in generated_workflow.py. The code should:
1. Import all necessary modules - include all imports from workflow_template.py
2. Set up environment variables (assume they exist - do NOT set them in the code)
3. Initialize LlamaParse, LlamaExtract, and LLMs
4. Define appropriate Pydantic schemas based on the reference files and task
5. Implement the complete workflow functions
6. Include a main() function that runs the workflow

IMPORTANT GUIDELINES:
- Do NOT include any os.environ["OPENAI_API_KEY"] = "..." or os.environ["LLAMA_CLOUD_API_KEY"] = "..." statements. Assume these environment variables are already set.
- Analyze the reference files to understand the document structure and infer the appropriate Pydantic schema
- Only implement document splitting if the task explicitly requires it (e.g., "split by sections", "process each chapter separately")
- If splitting is needed, import the splitting functions from document_utils.py: `from core.document_utils import afind_categories_and_splits`
- Do NOT copy the entire function definition from asset_manager_fund_analysis.md - just import from document_utils.py
- Do NOT use global declarations for project_id and organization_id in the main function - they should be set at module level
- If no splitting is needed, go directly from parsing to extraction
- Make the workflow flexible to handle different document types based on the reference files
- The main() function should accept input file paths as arguments (e.g., via argparse) so it can process multiple files
- Do NOT hardcode any specific file paths in the workflow - make it configurable
- The workflow should be able to process a single file or multiple files based on the input arguments

CONFIGURATION INSTRUCTIONS:
- Use the CONFIGURATION RECOMMENDATIONS above to set up LlamaParse and ExtractConfig
- For LlamaParse: Choose the appropriate parse mode from workflow_template.py (cost_effective, agentic, agentic_plus)
- For ExtractConfig: Include ALL available options as comments with the recommended ones uncommented
- When generating ExtractConfig, show users all available toggles by including commented lines like:
  ```python
  extract_config = ExtractConfig(
      extraction_mode=ExtractMode.MULTIMODAL,  # Recommended based on complexity
      # extraction_target=ExtractTarget.PER_DOC,   # PER_DOC, PER_PAGE
      # system_prompt="<Insert relevant context>", # Custom instructions
      # chunk_mode=ChunkMode.PAGE,     # PAGE, SECTION
      # high_resolution_mode=True,     # Better OCR for small text
      # invalidate_cache=False,        # Bypass cache for fresh results
      # cite_sources=True,             # Enable source citations
      # use_reasoning=False,           # ALWAYS False by default (performance issues)
      # confidence_scores=True         # Enable confidence scores (MULTIMODAL/PREMIUM only)
  )
  ```
- This gives users visibility into all available options for future editing

CRITICAL SCHEMA REQUIREMENTS FOR LLAMAEXTRACT COMPATIBILITY:
- NEVER use Dict[str, Any] or Dict[str, float] or any Dict types in Pydantic schemas - LlamaExtract does not support them
- Instead of Dict types, use one of these alternatives:
  1. Define specific fields for known categories (e.g., investment_banking_revenue: Optional[float])
  2. Use List[NestedModel] where NestedModel has category: str and value: float fields
  3. Convert Dict data to JSON strings in the workflow output processing (not in the schema itself)
- Only use these supported types in schemas: str, int, float, bool, Optional[...], List[...], and nested BaseModel classes
- Test your schema mentally - if you see Dict anywhere, replace it with supported alternatives

Do not include any markdown formatting, explanations, or commentary - just pure Python code.
"""


async def generate_workflow(
    user_task: str,
    data_files_path: str = "core/data_files",
    reference_files_path: str | None = None,
    project_id: str | None = None,
    organization_id: str | None = None,
    complexity_assessment: DocumentComplexityAssessment | None = None,
    llm: LLM | None = None,
    ctx: Context | None = None,  # type: ignore
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
    context_str = load_context_files(data_files_path, ctx)
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

    # Debug: Save formatted chat messages to file
    # print(llm.metadata)
    # try:
    #     with open("debug_messages.txt", "w", encoding="utf-8") as f:
    #         f.write("=== FORMATTED CHAT MESSAGES ===\n")
    #         f.write(f"Total messages: {len(messages)}\n\n")
    #         for idx, msg in enumerate(messages, start=1):
    #             role_str = str(getattr(msg, "role", "unknown"))
    #             content_str = getattr(msg, "content", "")
    #             f.write(f"[{idx}] role={role_str}\n")
    #             f.write(content_str)
    #             f.write("\n\n")
    #     _send_event(ctx, f"📝 Prompt messages saved to debug_messages.txt ({len(messages)} messages)")
    # except Exception as e:
    #     _send_event(ctx, f"Warning: Failed to save debug messages: {e}")
    # raise Exception

    # Try to use Rich Live Spinner until first token, then stream tokens
    use_spinner = ctx and StreamEvent
    if use_spinner:
        try:
            from rich.console import Console
            from rich.live import Live
            from rich.spinner import Spinner

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

        except ImportError:
            use_spinner = False

    if not use_spinner:
        # Fallback: simple progress message + streaming
        if ctx and StreamEvent:
            from .utils import CLIFormatter

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
        from .utils import CLIFormatter

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
        from .utils import CLIFormatter

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
        from .utils import CLIFormatter

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
    ctx: Context | None = None,  # type: ignore
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
    ctx: Context | None = None,  # type: ignore
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
        from .utils import CLIFormatter

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
    ctx: Context | None = None,  # type: ignore
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
        from .utils import CLIFormatter

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
    import re
    from pathlib import Path

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
