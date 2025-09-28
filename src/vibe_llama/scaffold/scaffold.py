import os
from pathlib import Path
from typing import Optional, Literal, get_args, cast, Tuple
import copier

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

# Map local template names to remote GitHub copier templates
TEMPLATES: dict[ProjectName, str] = {
    "basic": "gh:run-llama/template-workflow-basic",
    "document_parsing": "gh:run-llama/template-workflow-document-parsing",
    "human_in_the_loop": "gh:run-llama/template-workflow-human-in-the-loop",
    "invoice_extraction": "gh:run-llama/template-workflow-invoice-extraction",
    "rag": "gh:run-llama/template-workflow-rag",
    "web_scraping": "gh:run-llama/template-workflow-web-scraping",
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

        template_src = TEMPLATES[request]
        copier.run_copy(template_src, actual_path)

        return f"[bold green]SUCCESS✅[/]\nYour workflow was written to: {os.path.join(actual_path, 'workflow.py')}.\nFind project details at: {os.path.join(actual_path, 'pyproject.toml')}.\nInstall all necessary dependencies with [on gray]cd {actual_path} && pip install .[/]"

    except Exception as e:
        return f"[bold red]ERROR[/]\tThere was an error while trying to generate the example: {e}"
