"""
Utility classes and functions for AI Agent CLI.
"""

import textwrap
import uuid
import os
import sys
import asyncio
from pathlib import Path
from typing import Any, Optional

from rich.console import Console
from rich.markdown import Markdown
from rich.padding import Padding
from rich.syntax import Syntax
from rich.text import Text
from rich.console import Group
from rich.rule import Rule

from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.styles import Style

from llama_index.core.prompts import ChatMessage, ChatPromptTemplate
from pydantic import BaseModel, Field


def validate_uuid(uuid_string: str) -> bool:
    """Validate if a string is a proper UUID format"""
    try:
        uuid.UUID(uuid_string)
        return True
    except ValueError:
        return False


class PythonPackage(BaseModel):
    package_name: str = Field(description="Name of the package")
    package_version: Optional[str] = Field(
        description="Version of the package (not required, but nice to have)",
        default=None,
    )


class Dependencies(BaseModel):
    dependencies: list[PythonPackage] = Field(
        description="List of python packages needed as dependencies for a given code"
    )


class StreamEvent:
    """Event for streaming response tokens"""

    def __init__(
        self,
        delta: str = "",
        rich_content: Any | None = None,
        newline_after: bool = False,
        is_code: bool = False,
        is_agent_response: bool = False,
    ):
        self.delta = delta
        self.rich_content = rich_content  # For rich formatting objects
        self.newline_after = newline_after  # Whether to add newline after content
        self.is_code = is_code  # Whether this is code content
        self.is_agent_response = is_agent_response  # Whether this is an agent response that should be bullet-indented


class CLIFormatter:
    """Rich formatting utilities for the CLI"""

    @staticmethod
    def _get_terminal_width() -> int:
        """Get current terminal width with fallback"""
        try:
            console = Console()
            return console.size.width
        except Exception:
            return 80  # Fallback width

    @staticmethod
    def agent_response(text: str):
        """Format agent response with markdown support and indentation"""
        if not text.strip():
            return Text("")
        # Use Markdown to preserve bold and other formatting
        content = Padding(Markdown(text.strip()), (0, 0, 0, 2))  # 2-space left indent

        return content

    @staticmethod
    def indented_text(text: str, prefix: str = "│ ", style: str = "dim white"):
        """Format text with left-side visual indicator and subtle styling"""
        if not text.strip():
            return Text("")

        # Use visual left border character with subtle styling for better hierarchy
        formatted_text = f"{prefix}{text.strip()}"
        return Text(formatted_text, style=style)

    @staticmethod
    def tool_action(action_name: str, description: str = ""):
        """Format tool action like Claude Code with bold highlighting and proper wrapping"""

        if description:
            # Handle long descriptions with proper indentation
            full_text = f"⏺ {action_name}({description})"

            # If it's a long single line, let Rich handle the wrapping naturally
            return Text(full_text, style="bold")
        else:
            return Text(f"⏺ {action_name}", style="bold")

    @staticmethod
    def success(message: str):
        """Format success message - simple and resize-friendly"""
        return Text(f"✅ {message}", style="bold green")

    @staticmethod
    def error(message: str):
        """Format error message - simple and resize-friendly"""
        return Text(f"❌ {message}", style="bold red")

    @staticmethod
    def info(message: str):
        """Format info message - simple and resize-friendly"""
        return Text(f"ℹ️  {message}", style="bold blue")

    @staticmethod
    def code(code: str, language: str = "python") -> Syntax:
        """Format code with syntax highlighting"""
        return Syntax(code, language, theme="monokai", line_numbers=True)

    @staticmethod
    def markdown(content: str) -> Markdown:
        """Format markdown content"""
        return Markdown(content)

    @staticmethod
    def heading(text: str, style: str = "bold cyan") -> Text:
        """Format heading text"""
        return Text(text, style=style)

    @staticmethod
    def status_update(text: str, prefix: str = "▸ ") -> Text:
        """Format status updates with bold styling and visual indicator"""
        return Text(f"{prefix}{text}", style="bold")

    @staticmethod
    def important_text(text: str, prefix: str = "◦ ") -> Text:
        """Format important information with highlighting"""
        return Text(f"{prefix}{text}", style="bold bright_white")

    @staticmethod
    def subtle_text(text: str, prefix: str = "│ ") -> Text:
        """Format subtle/secondary text with dim styling"""
        return Text(f"{prefix}{text}", style="dim")

    @staticmethod
    def workflow_summary(summary: str, max_width: int = 90):
        """Format workflow summary with controlled width and markdown rendering"""
        # Create a group with header and wrapped content
        header = Text("📋 Workflow Summary", style="bold cyan")

        # Apply text wrapping while preserving markdown structure
        # Split by paragraphs (double newlines) to handle markdown properly
        paragraphs = summary.strip().split("\n\n")
        wrapped_paragraphs = []

        for paragraph in paragraphs:
            # Handle markdown headers and lists specially
            lines = paragraph.split("\n")
            wrapped_lines = []

            for line in lines:
                if line.strip().startswith(("#", "-", "*", "1.")):
                    # Don't wrap headers or list items - just add them as-is
                    wrapped_lines.append(line)
                elif len(line) > max_width and not line.strip().startswith("**"):
                    # Wrap long regular text lines
                    wrapped = textwrap.fill(
                        line.strip(), width=max_width, subsequent_indent="   "
                    )
                    wrapped_lines.append(wrapped)
                else:
                    wrapped_lines.append(line)

            wrapped_paragraphs.append("\n".join(wrapped_lines))

        wrapped_summary = "\n\n".join(wrapped_paragraphs)

        # Use Markdown to render formatting properly
        content = Padding(
            Markdown(wrapped_summary), (0, 0, 0, 3)
        )  # 3-space left indent

        return Group(header, content)

    @staticmethod
    def file_list(files: list, title: str = "📁 Available Files"):
        """Format file list - simple and resize-friendly"""
        header = Text(title, style="bold yellow")
        rule = Rule(style="dim yellow")

        file_lines = []
        for i, file in enumerate(files[:10]):
            file_lines.append(Text(f"  {i + 1}. {file}", style="dim white"))

        if len(files) > 10:
            file_lines.append(
                Text(f"  ... and {len(files) - 10} more files", style="dim")
            )

        return Group(header, rule, *file_lines)

    @staticmethod
    def diff_preview(diff_text: str) -> Syntax:
        """Format diff text with syntax highlighting"""
        return Syntax(
            diff_text, "diff", theme="monokai", line_numbers=False, word_wrap=True
        )

    @staticmethod
    def code_output(
        code: str, title: str = "🔧 Generated Workflow Code", language: str = "python"
    ):
        """Format code output - indented syntax highlighting"""

        header = Text(title, style="bold green")
        rule = Rule(style="dim green")
        code_syntax = Syntax(
            code, language, theme="monokai", line_numbers=True, word_wrap=True
        )
        indented_code = Padding(code_syntax, (0, 0, 0, 2))  # Left padding of 2

        return Group(header, rule, indented_code)

    @staticmethod
    def runbook_output(content: str, title: str = "📋 Generated Runbook"):
        """Format runbook output - indented markdown"""

        header = Text(title, style="bold blue")
        rule = Rule(style="dim blue")
        markdown_content = Padding(Markdown(content), (0, 0, 0, 2))  # Left padding of 2

        return Group(header, rule, markdown_content)


class PathCompleter:
    """Custom completer for @ symbol path completion"""

    def __init__(self):
        self.Completer = Completer
        self.Completion = Completion
        self.os = os

    def get_completions(self, document, complete_event):
        """Generate completions for @ symbol paths"""
        text = document.text
        cursor_pos = document.cursor_position

        # Find the @ symbol position
        at_pos = text.rfind("@", 0, cursor_pos)
        if at_pos == -1:
            return

        # Extract the path after @
        path_part = text[at_pos + 1 : cursor_pos]

        # Determine base directory and search pattern
        if "/" in path_part:
            # e.g., @folder1/subfolde -> base_dir='folder1', pattern='subfolde'
            base_dir, pattern = path_part.rsplit("/", 1)
            search_dir = base_dir if self.os.path.exists(base_dir) else "."
        else:
            # e.g., @fold -> base_dir='.', pattern='fold'
            search_dir = "."
            pattern = path_part

        try:
            # Get matching directories/files
            items = []
            for item in self.os.listdir(search_dir):
                (self.os.path.join(search_dir, item) if search_dir != "." else item)
                full_path = self.os.path.join(search_dir, item)

                # Filter by pattern and show directories first
                if item.lower().startswith(pattern.lower()):
                    is_dir = self.os.path.isdir(full_path)
                    if is_dir:
                        display_text = f"📁 {item}/"
                        insert_text = item + "/"
                    else:
                        display_text = f"📄 {item}"
                        insert_text = item

                    # Calculate how much to replace from cursor position
                    start_pos = at_pos + 1 + len(path_part) - len(pattern)

                    completion = self.Completion(
                        insert_text,
                        start_position=start_pos - cursor_pos,
                        display=display_text,
                    )
                    # Store sort info as custom attributes
                    completion._is_dir = is_dir  # type: ignore
                    completion._sort_text = item.lower()  # type: ignore
                    items.append(completion)

            # Sort: directories first, then files alphabetically
            items.sort(key=lambda x: (not x._is_dir, x._sort_text))
            return items[:10]  # Limit to 10 items

        except (OSError, PermissionError):
            return []


async def boxed_input_async(
    prompt_text: str,
    title: str = "💬 Input Required",
    enable_path_completion: bool = True,
) -> str:
    """Create a simple, resize-friendly input prompt like Claude Code"""
    console = Console()

    # Simple prompt without rigid boxes - just like Claude Code
    # Format the prompt text as an agent response
    formatted_prompt = CLIFormatter.agent_response(prompt_text)

    # Print the formatted prompt
    console.print(formatted_prompt)
    console.print()
    try:
        style = Style.from_dict(
            {
                "prompt": "#ffaa00 bold",  # Yellow/orange prompt
                "completion-menu.completion": "bg:#444444 #ffffff",
                "completion-menu.completion.current": "bg:#00aaaa #000000 bold",
                "completion-menu.meta.completion": "bg:#222222 #bbbbbb",
                "completion-menu.meta.completion.current": "bg:#00aaaa #000000",
            }
        )

        # Set up completer if path completion is enabled
        completer = None
        if enable_path_completion:

            class CustomCompleter(Completer):
                def __init__(self):
                    self.path_completer = PathCompleter()

                def get_completions(self, document, complete_event):  # type: ignore
                    text = document.text
                    # Only activate completion if @ symbol is present
                    if "@" in text:
                        return self.path_completer.get_completions(
                            document, complete_event
                        )
                    return []

            completer = CustomCompleter()

            # Create session for async prompting
        session = PromptSession(
            HTML("<prompt>❯ </prompt>"),
            style=style,
            mouse_support=False,  # Disabled to allow terminal text selection
            complete_style="column",  # type: ignore
            completer=completer,
            wrap_lines=True,
        )

        # Use async prompt to avoid event loop conflicts
        response = await session.prompt_async()

        console.print()  # Extra spacing after input
        return response.strip()

    except KeyboardInterrupt:
        console.print()
        raise


def clean_file_path(path: str) -> str:
    """Clean file path by removing @ symbol and normalizing path"""
    if path.startswith("@"):
        path = path[1:]  # Remove @ symbol

    # Convert to absolute path and normalize
    if path.startswith("./"):
        path = path[2:]  # Remove './'

    return os.path.abspath(path) if path else path


def is_file_path(input_str: str) -> bool:
    """
    Determine if a string that starts with '/' is likely a file path rather than a command.

    Returns True if it's likely a file path, False if it's likely a command.
    """
    # Remove leading @ symbol if present
    cleaned_path = input_str[1:] if input_str.startswith("@") else input_str

    # If it has multiple path components or file extensions, it's likely a path
    if "/" in cleaned_path[1:] or "." in os.path.basename(cleaned_path):
        return True

    # If it exists as a file or directory, it's a path
    if os.path.exists(cleaned_path):
        return True

    # If it looks like a Unix absolute path (not just "/command"), it's likely a path
    if len(cleaned_path.split("/")) > 2:  # More than just "/" + single word
        return True

    return False


def validate_reference_path(path: str) -> tuple[bool, str, str]:
    """
    Validate a reference files path and provide helpful error messages.

    Args:
        path: The path to validate (can be file or directory)

    Returns:
        Tuple of (is_valid, error_message, suggestions)
    """
    if not os.path.exists(path):
        parent_dir = os.path.dirname(path)
        suggestions = []

        if os.path.exists(parent_dir):
            # Show available directories/files in parent
            try:
                items = [
                    item
                    for item in os.listdir(parent_dir)
                    if not item.startswith(".")
                    and (
                        os.path.isdir(os.path.join(parent_dir, item))
                        or item.endswith((".pdf", ".txt", ".docx", ".doc"))
                    )
                ]
                if items:
                    suggestions.append(f"📁 Available in {parent_dir}:")
                    for item in items[:5]:  # Show max 5 items
                        item_path = os.path.join(parent_dir, item)
                        icon = "📁" if os.path.isdir(item_path) else "📄"
                        suggestions.append(f"  {icon} {item}")
                    if len(items) > 5:
                        suggestions.append(f"  ... and {len(items) - 5} more")
            except PermissionError:
                suggestions.append(f"⚠️ Cannot access {parent_dir} - check permissions")

        # Check if user meant current directory
        basename = os.path.basename(path)
        if basename in ["examples", "data", "docs", "files"]:
            if os.path.exists(basename):
                suggestions.append(f"💡 Did you mean: ./{basename}/")

        error_msg = f"❌ Path does not exist: {path}"
        suggestions_str = "\n".join(suggestions) if suggestions else ""

        return False, error_msg, suggestions_str

    return True, "", ""


def validate_workflow_path(path: str) -> tuple[bool, str, str]:
    """
    Validate a workflow path, trying both folder/workflow.py and direct file paths.

    Args:
        path: The path to validate

    Returns:
        Tuple of (is_valid, actual_path_to_use, error_message)
    """
    # First try the path as-is
    if os.path.exists(path):
        if os.path.isfile(path):
            return True, path, ""
        elif os.path.isdir(path):
            # Try to find workflow.py in the directory
            workflow_file = os.path.join(path, "workflow.py")
            if os.path.exists(workflow_file):
                return True, workflow_file, ""

            # Show what's available in the directory
            try:
                files = [f for f in os.listdir(path) if f.endswith(".py")]
                if files:
                    suggestions = f"📁 Python files in {path}:\n"
                    for f in files[:5]:
                        suggestions += f"  📄 {f}\n"
                    error_msg = f"❌ No workflow.py found in {path}\n\n{suggestions}"
                else:
                    error_msg = f"❌ No Python files found in directory: {path}"
            except PermissionError:
                error_msg = f"❌ Cannot access directory: {path}"

            return False, path, error_msg

    # Try adding .py extension
    if not path.endswith(".py"):
        py_path = path + ".py"
        if os.path.exists(py_path):
            return True, py_path, ""

    # Try looking for workflow.py in the path as a directory
    workflow_path = os.path.join(path, "workflow.py")
    if os.path.exists(workflow_path):
        return True, workflow_path, ""

    # Provide suggestions from parent directory
    parent_dir = os.path.dirname(path) or "."
    suggestions = []

    if os.path.exists(parent_dir):
        try:
            # Look for workflow directories and .py files
            items = []
            for item in os.listdir(parent_dir):
                item_path = os.path.join(parent_dir, item)
                if os.path.isdir(item_path):
                    if os.path.exists(os.path.join(item_path, "workflow.py")):
                        items.append(f"📁 {item}/ (contains workflow.py)")
                elif item.endswith(".py"):
                    items.append(f"📄 {item}")

            if items:
                suggestions.append(f"📁 Available in {parent_dir}:")
                for item in items[:5]:
                    suggestions.append(f"  {item}")
                if len(items) > 5:
                    suggestions.append(f"  ... and {len(items) - 5} more")
        except PermissionError:
            suggestions.append(f"⚠️ Cannot access {parent_dir}")

    error_msg = f"❌ Workflow not found: {path}\n"
    error_msg += (
        "💡 Try: folder path (will look for workflow.py) or direct .py file path"
    )
    if suggestions:
        error_msg += "\n\n" + "\n".join(suggestions)

    return False, path, error_msg


def get_test_file_suggestions(directory: str) -> list[str]:
    """
    Get a list of suitable test files from a directory.

    Args:
        directory: Directory to search for test files

    Returns:
        List of file paths suitable for testing
    """
    if not os.path.exists(directory) or not os.path.isdir(directory):
        return []

    suitable_files = []
    supported_extensions = {".pdf", ".txt", ".docx", ".doc", ".html", ".htm", ".csv"}

    try:
        for root, _dirs, files in os.walk(directory):
            for file in files:
                if not file.startswith("."):  # Skip hidden files
                    ext = os.path.splitext(file.lower())[1]
                    if ext in supported_extensions:
                        suitable_files.append(os.path.join(root, file))
    except PermissionError:
        pass

    return suitable_files[:10]  # Limit to 10 files for display


async def analyze_workflow_with_llm(workflow_path: str, llm) -> dict:
    """
    Use LLM to analyze a workflow file and determine its execution requirements.

    Returns dict with information about how to run the workflow.
    """

    class WorkflowAnalysis(BaseModel):
        """Analysis of a workflow file's execution requirements."""

        has_main_function: bool = Field(
            ...,
            description="Whether the workflow has a main() function that can be executed",
        )
        accepts_input_files: bool = Field(
            ..., description="Whether the workflow accepts input file(s) as arguments"
        )
        input_files_arg_name: str = Field(
            default="",
            description="Name of the input files argument (e.g., 'input_files', 'file_path')",
        )
        supports_multiple_files: bool = Field(
            default=False, description="Whether it can process multiple files at once"
        )
        has_output_flag: bool = Field(
            default=False,
            description="Whether it has an output file flag like --output or -o",
        )
        has_verbose_flag: bool = Field(
            default=False,
            description="Whether it has a verbose flag like --verbose or -v",
        )
        execution_command: str = Field(
            default="", description="Recommended command to execute this workflow"
        )
        needs_directory_input: bool = Field(
            default=False,
            description="Whether this workflow expects a directory rather than individual files",
        )

    try:
        with open(workflow_path, encoding="utf-8") as f:
            workflow_code = f.read()
    except Exception as e:
        return {"error": f"Could not read workflow file: {e}"}

    # Fail on very long files rather than truncating and giving wrong analysis
    if len(workflow_code) > 200000:
        return {
            "error": f"Workflow file is too large ({len(workflow_code)} chars) for analysis. Maximum supported size is 200,000 characters."
        }

    analysis_prompt = """Analyze this Python workflow file to understand how it should be executed.

WORKFLOW CODE:
```python
{workflow_code}
```

Based on the code above, determine:
1. Does this workflow have a main() function that can be executed?
2. How does it accept input files? (command line args, specific parameter names)
3. Does it support processing multiple files or just one?
4. What command line flags does it support (--output, --verbose, etc.)?
5. What's the recommended way to execute this workflow?

Focus on the argument parsing, main function, and how the workflow expects to receive input files."""

    chat_template = ChatPromptTemplate([ChatMessage.from_str(analysis_prompt, "user")])

    try:
        response = await llm.astructured_predict(
            WorkflowAnalysis, chat_template, workflow_code=workflow_code
        )
        return response.dict()
    except Exception as e:
        # Fallback analysis based on simple text patterns
        return {
            "error": f"LLM analysis failed: {e}",
            "has_main_function": "def main(" in workflow_code
            or "if __name__ == " in workflow_code,
            "accepts_input_files": "input_files" in workflow_code
            or "file_path" in workflow_code,
            "input_files_arg_name": "input_files"
            if "input_files" in workflow_code
            else "file_path",
            "supports_multiple_files": "nargs=" in workflow_code,
            "has_output_flag": "--output" in workflow_code or "-o" in workflow_code,
            "has_verbose_flag": "--verbose" in workflow_code or "-v" in workflow_code,
            "execution_command": f"python {workflow_path}",
            "needs_directory_input": False,
        }


def boxed_input(prompt_text: str, title: str = "💬 Input Required") -> str:
    """Create a simple, resize-friendly input prompt - sync wrapper for backward compatibility"""
    try:
        # If we're already in an event loop, we need to use the async version differently
        asyncio.get_running_loop()
        # We're in an event loop, so this should not happen in our current architecture
        # But keeping this as fallback
        console = Console()

        # Simple prompt without rigid boxes
        formatted_prompt = CLIFormatter.agent_response(prompt_text)
        console.print(formatted_prompt)
        console.print()
        console.print("[bold yellow]❯[/bold yellow] ", end="")
        response = input()
        console.print()
        return response.strip()

    except RuntimeError:
        # No event loop running, safe to create one
        return asyncio.run(boxed_input_async(prompt_text, title))


async def local_venv():
    venv_path = Path(".venv")
    if venv_path.exists():
        return
    cmd = [sys.executable, "-m", "venv", ".venv"]
    program = await asyncio.create_subprocess_shell(
        " ".join(cmd), stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await program.communicate()
    if program.returncode != 0:
        raise ValueError(
            "Impossible to create venv within the given environment\nCaptured Logs:\n\tSTDOUT:\n"
            + str(stdout, encoding="utf-8")
            + "\n\tSTDERR:\n"
            + str(stderr, encoding="utf-8")
        )
    return


async def install_deps():
    if sys.platform == "win32":
        venv_cmd = ".\\.venv\\Scripts\\activate"
    else:
        venv_cmd = ["source", ".venv/bin/activate"]

    venv_cmd += [
        "&&",
        "python3",
        "-m",
        "ensurepip",
        "--upgrade",
        "&&",
        "python3",
        "-m",
        "pip",
        "install",
        "-r",
        ".vibe-llama/requirements.txt",
    ]
    program = await asyncio.create_subprocess_shell(
        " ".join(venv_cmd),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await program.communicate()
    if program.returncode != 0:
        raise ValueError(
            "Impossible to install needed dependencies in the current virtual environment\nCaptured Logs:\n\tSTDOUT:\n"
            + str(stdout, encoding="utf-8")
            + "\n\tSTDERR:\n"
            + str(stderr, encoding="utf-8")
        )
    return
