import os
from pathlib import Path
from .project_files import generate_pyproject
from .copy_templates import get_template_files
from typing import Literal, Optional


async def create_scaffold(
    request: Literal[
        "base_example",
        "document_parsing",
        "human_in_the_loop",
        "invoice_extraction",
        "rag",
        "web_scraping",
    ] = "base_example",
    path: Optional[str] = None,
) -> str:
    try:
        if not path:
            actual_path = f".vibe-llama/scaffold/{request}"
            os.makedirs(actual_path, exist_ok=True)
        else:
            if Path(path).exists() and Path(path).is_dir():
                actual_path = path
            elif Path(path).exists() and Path(path).is_file():
                actual_path = os.path.dirname(path)
            elif not Path(path).exists():
                actual_path = path
                os.makedirs(path, exist_ok=True)
            else:
                actual_path = f".vibe-llama/scaffold/{request}"
                os.makedirs(actual_path, exist_ok=True)

        templates = await get_template_files(request)
        if templates:
            for file in templates:
                with open(os.path.join(actual_path, file), "w") as f:
                    f.write(templates[file])
            generate_pyproject(request, os.path.join(actual_path, "pyproject.toml"))
            return f"[bold green]SUCCESS✅[/]\nYour workflow was written to: {os.path.join(actual_path, 'workflow.py')}.\nFind project details at: {os.path.join(actual_path, 'pyproject.toml')}.\nInstall all necessary dependencies with [on gray]cd {actual_path} && pip install .[/]"
        else:
            return "[bold red]ERROR[/]\tThere was an error while trying to generate the example: Unable to fetch the templates from source. \n\tWe advise you to [bold yellow]retry[/] soon!"

    except Exception as e:
        return f"[bold red]ERROR[/]\tThere was an error while trying to generate the example: {e}"
