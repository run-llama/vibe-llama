"""
Workflow testing handler for AI Agent CLI.

Handles testing workflows on sample data by running them as subprocesses.
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import cast

from llama_index.core.llms import LLM, MessageRole, ChatMessage
from llama_index.core.prompts import ChatPromptTemplate
from workflows import Context
from workflows.events import InputRequiredEvent

from vibe_llama.docuflows.commons import (
    CLIFormatter,
    StreamEvent,
    analyze_workflow_with_llm,
    get_test_file_suggestions,
    Dependencies,
    local_venv,
    install_deps,
    clean_file_path,
)
from vibe_llama.sdk import VibeLlamaStarter
from vibe_llama.docuflows.commons.typed_state import WorkflowState
from vibe_llama.docuflows.prompts import DEPENDENCY_GENERATION_PROMPT

DOCS_GETTER = VibeLlamaStarter(
    agents=["vibe-llama docuflows"],
    services=["LlamaCloud Services", "llama-index-workflows"],
)


async def handle_test_workflow(
    ctx: Context[WorkflowState], test_file_path: str, llm=None
) -> InputRequiredEvent:
    """Test the current workflow by actually running it as a subprocess"""
    current_workflow = (await ctx.store.get_state()).current_workflow

    if not current_workflow:
        ctx.write_event_to_stream(
            StreamEvent(  # type: ignore
                delta="❌ No workflow to test. Please generate a workflow first.\n"
            )
        )
        return InputRequiredEvent(prefix="What would you like to do? ")  # type: ignore

    workflow_path = (await ctx.store.get_state()).current_workflow_path
    if not workflow_path or not os.path.exists(workflow_path):
        ctx.write_event_to_stream(
            StreamEvent(delta="❌ No workflow file found to execute.\n")  # type: ignore
        )
        return InputRequiredEvent(prefix="What would you like to do? ")  # type: ignore

    # Check for cached analysis first
    cached_analysis = (await ctx.store.get_state()).workflow_analysis_cache
    cached_workflow_path = (await ctx.store.get_state()).workflow_analysis_cache_path

    if cached_analysis and cached_workflow_path == workflow_path:
        analysis = cached_analysis
        needs_input = analysis.get("accepts_input_files", True)
    else:
        # Analyze workflow to see if it needs input files
        ctx.write_event_to_stream(
            StreamEvent(delta="🔍 Analyzing workflow requirements...\n")  # type: ignore
        )

        if not llm:
            ctx.write_event_to_stream(
                StreamEvent(  # type: ignore
                    delta="⚠️ No LLM available for analysis, assuming file input required\n"
                )
            )
            needs_input = True
            analysis = {
                "has_output_flag": True,
                "has_verbose_flag": True,
                "accepts_input_files": True,
            }
        else:
            analysis = await analyze_workflow_with_llm(workflow_path, llm)
            if "error" in analysis:
                ctx.write_event_to_stream(
                    StreamEvent(delta=f"⚠️ Analysis failed: {analysis['error']}\n")  # type: ignore
                )
                needs_input = True  # Safe assumption
                analysis = {
                    "has_output_flag": True,
                    "has_verbose_flag": True,
                    "accepts_input_files": True,
                }
            else:
                needs_input = analysis.get("accepts_input_files", True)

        # Cache the analysis
        async with ctx.store.edit_state() as state:
            state.workflow_analysis_cache = analysis
            state.workflow_analysis_cache_path = workflow_path

    # If workflow needs input files but none provided, handle that
    if needs_input and not test_file_path:
        return await handle_test_file_input(ctx, llm)

    # If we have a test file path, validate and potentially show file selection
    if test_file_path:
        return await handle_test_file_validation(ctx, test_file_path, llm, analysis)

    # If no input files needed, run workflow directly
    return await execute_workflow(ctx, workflow_path, None, llm, analysis)  # type: ignore


async def handle_test_file_input(
    ctx: Context[WorkflowState], llm
) -> InputRequiredEvent:
    """Handle the case where we need to get test file input from user"""
    return InputRequiredEvent(
        prefix="Please provide the path to a sample file to test: ",  # type: ignore
        tag="test_workflow",  # type: ignore
    )


async def handle_test_file_validation(
    ctx: Context[WorkflowState], test_file_path: str, llm, analysis: dict
) -> InputRequiredEvent:
    """Validate test file path and handle directory vs file logic"""

    # Clean the test file path (remove @ symbol if present)
    cleaned_path = clean_file_path(test_file_path)

    # If user provided a directory, show available files and ask for selection
    if os.path.isdir(cleaned_path):
        files_in_dir = get_test_file_suggestions(cleaned_path)

        if not files_in_dir:
            ctx.write_event_to_stream(
                StreamEvent(  # type: ignore
                    delta=f"❌ No suitable files found in directory: {cleaned_path}\n"
                )
            )
            return InputRequiredEvent(
                prefix="Please provide a valid file path to test: ",  # type: ignore
                tag="test_workflow",  # type: ignore
            )

        # Show available files in a nice panel
        relative_files = [os.path.relpath(f, cleaned_path) for f in files_in_dir]
        ctx.write_event_to_stream(
            StreamEvent(  # type: ignore
                delta="",
                rich_content=CLIFormatter.file_list(
                    relative_files,
                    f"📁 Found {len(files_in_dir)} files in {cleaned_path}",
                ),
                newline_after=True,
            )
        )

        # Ask user to select file using natural language
        return InputRequiredEvent(
            prefix="\nWhich file would you like to test?\n"  # type: ignore
            "You can describe it in natural language (e.g., 'the PDF file', 'maritime report', 'first file') or provide a specific path: ",
            tag="file_selection",  # type: ignore
            available_files=files_in_dir,  # type: ignore
            base_directory=cleaned_path,  # type: ignore
        )

    if not os.path.exists(cleaned_path):
        ctx.write_event_to_stream(
            StreamEvent(delta=f"❌ Test file does not exist: {cleaned_path}\n")  # type: ignore
        )
        return InputRequiredEvent(
            prefix="Please provide a valid file path to test: ",  # type: ignore
            tag="test_workflow",  # type: ignore
        )

    # File exists, proceed to execute workflow
    workflow_path = (await ctx.store.get_state()).current_workflow_path
    return await execute_workflow(
        ctx, cast(str, workflow_path), cleaned_path, llm, analysis
    )


async def handle_deps_generation(
    ctx: Context[WorkflowState], workflow_path: str, llm: LLM
) -> bool:
    with open(workflow_path, "r") as wf_path:
        wf_content = wf_path.read()

    if not Path(".vibe-llama/rules/AGENTS.md").is_file():
        await DOCS_GETTER.write_instructions()

    with open(".vibe-llama/rules/AGENTS.md", "r") as ins_fl:
        ins_content = ins_fl.read()

    prompt_tmpl = ChatPromptTemplate(
        [ChatMessage(content=DEPENDENCY_GENERATION_PROMPT, role="user")]
    )
    messages = prompt_tmpl.format_messages(
        instructions=ins_content, workflow_code=wf_content
    )
    sllm = llm.as_structured_llm(Dependencies)
    response = await sllm.achat(messages)
    if response.message.content:
        deps = Dependencies.model_validate_json(response.message.content)
        with open(".vibe-llama/requirements.txt", "w") as w:
            to_write = []
            for dep in deps.dependencies:
                if dep.package_version:
                    to_write.append(f"{dep.package_name}=={dep.package_version}")
                else:
                    to_write.append(dep.package_name)
            w.write("\n".join(to_write))
        ctx.send_event(
            StreamEvent(
                delta="",
                rich_content=CLIFormatter.info(
                    ".vibe-llama/requirements.txt has been written successfully"
                ),
            )  # type: ignore
        )
        return True
    else:
        ctx.send_event(
            StreamEvent(
                delta="",
                rich_content=CLIFormatter.error(
                    "Unable to find needed dependencies. Testing will proceed, but errros might occur"
                ),
                newline_after=True,
            )  # type: ignore
        )
        return False


async def handle_venv_generation_and_deps_install(
    ctx: Context[WorkflowState], workflow_path: str, llm: LLM
) -> tuple[bool, bool]:
    deps_available = await handle_deps_generation(ctx, workflow_path, llm)
    try:
        await local_venv()
        ctx.send_event(
            StreamEvent(
                delta="",
                rich_content=CLIFormatter.info(
                    "Proceeding with .venv as virtual environment"
                ),
                newline_after=True,
            )  # type: ignore
        )
    except ValueError as ve:
        ctx.send_event(
            StreamEvent(
                delta="",
                rich_content=CLIFormatter.error(
                    "Error while finding/creating virtual environment: " + str(ve)
                ),
                newline_after=True,
            )  # type: ignore
        )
        return False, False
    if deps_available:
        try:
            await install_deps()
            return True, True
        except ValueError as de:
            ctx.send_event(
                StreamEvent(
                    delta="",
                    rich_content=CLIFormatter.error(
                        "Error while installing dependencies: " + str(de)
                    ),
                    newline_after=True,
                )  # type: ignore
            )

            return True, False
    ctx.send_event(
        StreamEvent(
            delta="",
            rich_content=CLIFormatter.info(
                "Successfully installed all the needed dependencies within the current virtual environment, proceeding..."
            ),
            newline_after=True,
        )  # type: ignore
    )
    return True, True


async def execute_workflow(
    ctx: Context[WorkflowState],
    workflow_path: str,
    test_file_path: str,
    llm,
    analysis: dict,
) -> InputRequiredEvent:
    """Execute the workflow with the given test file"""

    if test_file_path:
        ctx.write_event_to_stream(
            StreamEvent(delta=f"🧪 Testing workflow on: {test_file_path}\n")  # type: ignore
        )
    ctx.write_event_to_stream(
        StreamEvent(delta=f"📄 Using workflow: {workflow_path}\n")  # type: ignore
    )

    # Create output directory in the same folder as the workflow
    workflow_folder = Path(workflow_path).parent
    if test_file_path:
        test_name = Path(test_file_path).stem
        output_path = workflow_folder / f"test_results_{test_name}"
    else:
        output_path = workflow_folder / "test_results"

    success_venv, success_deps = await handle_venv_generation_and_deps_install(
        ctx, workflow_path, llm
    )

    if not success_venv:
        ctx.write_event_to_stream(
            StreamEvent(  # type: ignore
                delta="",
                rich_content=CLIFormatter.error(
                    "Error executing workflow: unable to find/create local virtual environment or to install needed dependencies"
                ),
                newline_after=True,
            )
        )
        async with ctx.store.edit_state() as state:
            state.handler_status_message = "Workflow testing failed because we could not find/create local virtual environment or install needed dependencies. Please check your environment and make sure that python is installed and working."  # type: ignore
        return InputRequiredEvent(
            prefix="\nWorkflow testing failed :( What would you like to do next? "  # type: ignore
            "(Options: edit workflow, test another file, ask questions, generate new workflow): "
        )

    if not success_deps:
        ctx.write_event_to_stream(
            StreamEvent(  # type: ignore
                delta="⚠️ WARNING: Could not install needed dependencies. Testing will continue, but there might be errors due to missing dependencies.",
                newline_after=True,
            )
        )

    # Analysis is now required parameter

    try:
        if sys.platform == "win32":
            venv_act = [".\\.venv\\Scripts\\activate"]
        else:
            venv_act = ["source", ".venv/bin/activate"]

        python_cmd = venv_act + ["&&", "python3"]

        # Build command based on analysis
        cmd = python_cmd + [workflow_path]

        # Add input file(s) if workflow accepts them and we have a test file
        if analysis.get("accepts_input_files", True) and test_file_path:
            cmd.append(test_file_path)

        # Add output flag if supported
        if analysis.get("has_output_flag", False):
            cmd.extend(["-o", str(output_path)])

        # Add verbose flag if supported
        if analysis.get("has_verbose_flag", False):
            cmd.append("--verbose")

        # Show the command being executed
        cmd_str = " ".join(cmd)
        ctx.write_event_to_stream(StreamEvent(delta=f"💻 Command: {cmd_str}\n\n"))  # type: ignore

        # Execute the subprocess
        ctx.write_event_to_stream(StreamEvent(delta="🔄 Execution output:\n"))  # type: ignore
        ctx.write_event_to_stream(StreamEvent(delta="=" * 50 + "\n"))  # type: ignore

        # Run the process and stream output in real-time
        process = await asyncio.create_subprocess_shell(
            " ".join(cmd),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=os.getcwd(),
        )

        # Stream output as it comes
        while True:
            line = await process.stdout.readline()  # type: ignore
            if not line:
                break
            try:
                decoded_line = line.decode("utf-8")
                ctx.write_event_to_stream(StreamEvent(delta=decoded_line))  # type: ignore
            except UnicodeDecodeError:
                # Handle non-UTF8 output gracefully
                ctx.write_event_to_stream(StreamEvent(delta="[Binary output]\n"))  # type: ignore

        # Wait for process to complete
        return_code = await process.wait()

        ctx.write_event_to_stream(StreamEvent(delta="=" * 50 + "\n"))  # type: ignore

        if return_code == 0:
            ctx.write_event_to_stream(
                StreamEvent(  # type: ignore
                    delta="",
                    rich_content=CLIFormatter.success(
                        "✅ Workflow executed successfully!"
                    ),
                    newline_after=True,
                )
            )

            # Check if output was created
            if os.path.exists(output_path):
                if os.path.isdir(output_path):
                    ctx.write_event_to_stream(
                        StreamEvent(
                            delta=f"📊 Results saved to directory: {output_path}\n"  # type: ignore
                        )
                    )
                else:
                    file_size = os.path.getsize(output_path)
                    ctx.write_event_to_stream(
                        StreamEvent(  # type: ignore
                            delta=f"📊 Results saved to: {output_path} ({file_size} bytes)\n"
                        )
                    )
            else:
                ctx.write_event_to_stream(
                    StreamEvent(  # type: ignore
                        delta="⚠️ No output was created. Check the workflow implementation.\n"
                    )
                )
        else:
            ctx.write_event_to_stream(
                StreamEvent(  # type: ignore
                    delta="",
                    rich_content=CLIFormatter.error(
                        f"❌ Workflow execution failed with exit code {return_code}"
                    ),
                    newline_after=True,
                )
            )

    except FileNotFoundError as e:
        error_msg = f"Command not found: {e.filename}. "
        if "poetry" in str(e):
            error_msg += "Poetry is not installed or not in PATH. Try installing with: pip install poetry"
        else:
            error_msg += "Python interpreter not found."

        ctx.write_event_to_stream(
            StreamEvent(  # type: ignore
                delta="", rich_content=CLIFormatter.error(error_msg), newline_after=True
            )
        )

    except Exception as e:
        ctx.write_event_to_stream(
            StreamEvent(  # type: ignore
                delta="",
                rich_content=CLIFormatter.error(f"Error executing workflow: {str(e)}"),
                newline_after=True,
            )
        )

    # Clear analysis cache after execution (whether successful or not)
    async with ctx.store.edit_state() as state:
        state.workflow_analysis_cache = None
        state.workflow_analysis_cache_path = None

    # Set status message for chat history
    if return_code == 0:  # type: ignore
        async with ctx.store.edit_state() as state:
            state.handler_status_message = "Successfully tested the workflow. The execution completed without errors."
    else:
        async with ctx.store.edit_state() as state:
            state.handler_status_message = f"Workflow testing failed with exit code {return_code}. Please check the errors above and fix the workflow if needed."  # type: ignore

    return InputRequiredEvent(
        prefix="\nWorkflow testing complete! What would you like to do next? "  # type: ignore
        "(Options: edit workflow, test another file, ask questions, generate new workflow): "
    )


async def handle_test_file_selection(
    ctx: Context[WorkflowState],
    user_input: str,
    available_files: list,
    base_directory: str,
    llm: LLM,
) -> InputRequiredEvent:
    """Handle test workflow file selection using natural language or direct path"""

    if not user_input.strip():
        ctx.write_event_to_stream(
            StreamEvent(delta="❌ Please provide a file description or path.\n")  # type: ignore
        )
        return InputRequiredEvent(
            prefix="Which file would you like to test? ",  # type: ignore
            tag="file_selection",  # type: ignore
            available_files=available_files,  # type: ignore
            base_directory=base_directory,  # type: ignore
        )

    # First, check if user provided a direct path
    if os.path.exists(user_input):
        return await handle_test_workflow(ctx, user_input, llm)

    # Check if it's a relative path from base directory
    potential_path = os.path.join(base_directory, user_input)
    if os.path.exists(potential_path):
        return await handle_test_workflow(ctx, potential_path, llm)

    # Use LLM to match natural language description to files
    file_list_str = "\n".join(
        [
            f"{i + 1}. {os.path.relpath(f, base_directory)}"
            for i, f in enumerate(available_files)
        ]
    )

    selection_messages = [
        ChatMessage(
            role=MessageRole.SYSTEM,
            content="""You are a helpful assistant that matches user descriptions to files from a list.
The user may include extra words like 'yes this one!' or 'I want' - focus on extracting the actual filename or description.
Return ONLY the relative file path (exactly as shown in the numbered list) that best matches.
If the user mentions a specific filename, return just that filename (no extra path parts).
If no good match is found, return 'NO_MATCH'.
Be flexible with matching - look for filenames, keywords, file extensions, and partial matches.""",
        ),
        ChatMessage(
            role=MessageRole.USER,
            content=f"""Available files:
{file_list_str}

User input: "{user_input}"

Extract the key filename or description and return the matching relative file path from the list above, or 'NO_MATCH' if none match.

Examples:
- "yes this one! maritime_report.pdf" → "maritime_report.pdf" (if that file exists in list)
- "the first file" → return the first file from the list
- "PDF file" → return any PDF file from the list""",
        ),
    ]

    ctx.write_event_to_stream(
        StreamEvent(delta=f"🔍 Finding file matching '{user_input}'...\n")  # type: ignore
    )

    selection_response = await llm.achat(selection_messages)
    selected_file = selection_response.message.content.strip()  # type: ignore

    if selected_file == "NO_MATCH":
        ctx.write_event_to_stream(
            StreamEvent(delta=f"❌ Could not find a file matching '{user_input}'\n")  # type: ignore
        )
        return InputRequiredEvent(
            prefix="Please try a different description or provide a specific file path: ",  # type: ignore
            tag="file_selection",  # type: ignore
            available_files=available_files,  # type: ignore
            base_directory=base_directory,  # type: ignore
        )

    # Try to find the selected file in our available files
    matched_file = None

    # First try: exact relative path match
    for file_path in available_files:
        if os.path.relpath(file_path, base_directory) == selected_file:
            matched_file = file_path
            break

    # Second try: filename-only match (user might skip directories)
    if not matched_file:
        for file_path in available_files:
            if os.path.basename(file_path) == selected_file or os.path.basename(
                file_path
            ) == os.path.basename(selected_file):
                matched_file = file_path
                break

    # Third try: partial match in file path
    if not matched_file:
        for file_path in available_files:
            if selected_file in file_path:
                matched_file = file_path
                break

    # Fourth try: looser match by keywords
    if not matched_file:
        for file_path in available_files:
            if any(
                part in file_path.lower()
                for part in selected_file.lower().split()
                if len(part) > 2
            ):
                matched_file = file_path
                break

    if matched_file:
        ctx.write_event_to_stream(
            StreamEvent(  # type: ignore
                delta=f"✅ Selected: {os.path.relpath(matched_file, base_directory)}\n"
            )
        )
        # Set status message for chat history
        async with ctx.store.edit_state() as state:
            state.handler_status_message = f"Selected file '{os.path.relpath(matched_file, base_directory)}' for testing based on user description: '{user_input}'"

        return await handle_test_workflow(ctx, matched_file, llm)
    else:
        ctx.write_event_to_stream(
            StreamEvent(  # type: ignore
                delta=f"❌ Could not locate the selected file: {selected_file}\n"
            )
        )
        # Set error status message for chat history
        async with ctx.store.edit_state() as state:
            state.handler_status_message = (
                f"Could not locate file matching description: '{user_input}'"
            )

        return InputRequiredEvent(
            prefix="Please try again with a different description: ",  # type: ignore
            tag="file_selection",  # type: ignore
            available_files=available_files,  # type: ignore
            base_directory=base_directory,  # type: ignore
        )
