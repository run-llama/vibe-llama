import os
from pathlib import Path
from typing import Optional, Literal, get_args, cast, Tuple, Dict, Any
from copier import run_copy



# enum-like type for project names
ProjectName = Literal[
    "base_example",
    "document_parsing",
    "human_in_the_loop",
    "invoice_extraction",
    "rag",
    "web_scraping",
]

# Catalog with descriptions and dependencies (kept in sync with templates/*/pyproject.toml)
PROJECTS: Dict[ProjectName, Dict[str, Any]] = {
    "base_example": {
        "description": "A base example that showcases usage patterns for workflows",
        "dependencies": [
            "llama-index-workflows",
            "llama-index-llms-openai",
        ],
    },
    "document_parsing": {
        "description": "A workflow that, using LlamaParse, parses unstructured documents and returns their raw text content.",
        "dependencies": [
            "llama-index-workflows",
            "llama-cloud-services",
        ],
    },
    "human_in_the_loop": {
        "description": "A workflow showcasing how to use human in the loop",
        "dependencies": [
            "llama-index-workflows",
            "llama-index-llms-openai",
        ],
    },
    "invoice_extraction": {
        "description": "A workflow that, given an invoice, extracts several key details using LlamaExtract",
        "dependencies": [
            "llama-index-workflows",
            "llama-cloud-services",
        ],
    },
    "rag": {
        "description": "A workflow that embeds, indexes and queries your documents on the fly, providing you with a simple RAG pipeline.",
        "dependencies": [
            "llama-index-llms-openai",
            "llama-index-embeddings-openai",
            "llama-index-workflows",
        ],
    },
    "web_scraping": {
        "description": "A workflow that, given several urls, scrapes and summarizes their content.",
        "dependencies": [
            "llama-index-workflows",
            "llama-index-llms-google-genai",
        ],
    },
}

# Expose a typed tuple of just the allowed names for convenience/choices
PROJECT_NAMES: Tuple[ProjectName, ...] = cast(Tuple[ProjectName, ...], get_args(ProjectName))


async def create_scaffold(
    request: ProjectName = "base_example",
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
        template_src = str(Path(__file__).resolve().parents[3] / "templates" / request)
        run_copy(template_src, actual_path)

        return f"[bold green]SUCCESS✅[/]\nYour workflow was written to: {os.path.join(actual_path, 'workflow.py')}.\nFind project details at: {os.path.join(actual_path, 'pyproject.toml')}.\nInstall all necessary dependencies with [on gray]cd {actual_path} && pip install .[/]"

    except Exception as e:
        return f"[bold red]ERROR[/]\tThere was an error while trying to generate the example: {e}"
