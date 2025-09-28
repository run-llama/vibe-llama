import os
from pathlib import Path
from typing import Optional, Literal, get_args, cast, Tuple, Dict
from copier import run_copy


# enum-like type for project names
ProjectName = Literal[
    "basic",
    "document_parsing",
    "human_in_the_loop",
    "invoice_extraction",
    "rag",
    "web_scraping",
]

# Expose a typed tuple of just the allowed names for convenience/choices
PROJECTS: Tuple[ProjectName, ...] = cast(Tuple[ProjectName, ...], get_args(ProjectName))


# Map template names to their remote GitHub repositories
REMOTE_TEMPLATES: Dict[ProjectName, str] = {
    "basic": "https://github.com/run-llama/template-workflow-basic",
    "document_parsing": "https://github.com/run-llama/template-workflow-document-parsing",
    "human_in_the_loop": "https://github.com/run-llama/template-workflow-human-in-the-loop",
    "invoice_extraction": "https://github.com/run-llama/template-workflow-invoice-extraction",
    "rag": "https://github.com/run-llama/template-workflow-rag",
    "web_scraping": "https://github.com/run-llama/template-workflow-web-scraping",
}


async def create_scaffold(
    request: ProjectName = "basic",
    path: Optional[str] = None,
) -> str:
    try:
        if not path:
            actual_path = f".vibe-llama/scaffold/{request}"
        else:
            if Path(path).exists() and Path(path).is_file():
                actual_path = os.path.dirname(path)
            else:
                actual_path = path

        # Ensure destination directory exists
        os.makedirs(actual_path, exist_ok=True)

        # Copy the selected template from remote GitHub repository using Copier
        template_src = REMOTE_TEMPLATES[request]
        # Use defaults to avoid interactive prompts; overwrite existing files in destination
        run_copy(template_src, actual_path)

        return f"[bold green]SUCCESS✅[/]\nYour workflow was written to: {os.path.join(actual_path, 'workflow.py')}.\nFind project details at: {os.path.join(actual_path, 'pyproject.toml')}.\nInstall all necessary dependencies with [on gray]cd {actual_path} && pip install .[/]"

    except Exception as e:
        return f"[bold red]ERROR[/]\tThere was an error while trying to generate the example: {e}"
