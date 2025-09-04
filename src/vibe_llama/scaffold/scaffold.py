import os
from pathlib import Path
from typing import Optional
from copier import run_copy



from enum import Enum

class PROJECTS(Enum):
    BASE_EXAMPLE = "base_example"
    DOCUMENT_PARSING = "document_parsing"
    HUMAN_IN_THE_LOOP = "human_in_the_loop"
    INVOICE_EXTRACTION = "invoice_extraction"
    RAG = "rag"
    WEB_SCRAPING = "web_scraping"


async def create_scaffold(
    request: PROJECTS = PROJECTS.BASE_EXAMPLE,
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

        # Copy the selected template directory into destination using Copier
        template_src = str(Path(__file__).resolve().parents[3] / "templates" / request.value)
        run_copy(template_src, actual_path)

        return f"[bold green]SUCCESS✅[/]\nYour workflow was written to: {os.path.join(actual_path, 'workflow.py')}.\nFind project details at: {os.path.join(actual_path, 'pyproject.toml')}.\nInstall all necessary dependencies with [on gray]cd {actual_path} && pip install .[/]"

    except Exception as e:
        return f"[bold red]ERROR[/]\tThere was an error while trying to generate the example: {e}"
