from vibe_llama.scaffold.samples import (
    BASE_EXAMPLE_CODE,
    BASE_EXAMPLE_REQUIREMENTS,
    DOCUMENT_PROCESSING_CODE,
    DOCUMENT_PROCESSING_REQUIREMENTS,
    HUMAN_IN_THE_LOOP_CODE,
    HUMAN_IN_THE_LOOP_REQUIREMENTS,
    INVOICE_EXTRACTOR_CODE,
    INVOICE_EXTRACTOR_REQUIREMENTS,
    RAG_CODE,
    RAG_REQUIREMENTS,
    WEB_SCRAPING_CODE,
    WEB_SCRAPING_REQUIREMENTS,
)
import os
from pathlib import Path
from typing import Literal, Optional

SCAFFOLD_DICT = {
    "base_example": {
        "code": BASE_EXAMPLE_CODE,
        "requirements": BASE_EXAMPLE_REQUIREMENTS,
    },
    "document_processing": {
        "code": DOCUMENT_PROCESSING_CODE,
        "requirements": DOCUMENT_PROCESSING_REQUIREMENTS,
    },
    "human_in_the_loop": {
        "code": HUMAN_IN_THE_LOOP_CODE,
        "requirements": HUMAN_IN_THE_LOOP_REQUIREMENTS,
    },
    "invoice_extractor": {
        "code": INVOICE_EXTRACTOR_CODE,
        "requirements": INVOICE_EXTRACTOR_REQUIREMENTS,
    },
    "rag": {
        "code": RAG_CODE,
        "requirements": RAG_REQUIREMENTS,
    },
    "web_scraping": {
        "code": WEB_SCRAPING_CODE,
        "requirements": WEB_SCRAPING_REQUIREMENTS,
    },
}


def create_scaffold(
    request: Literal[
        "base_example",
        "document_processing",
        "human_in_the_loop",
        "invoice_extractor",
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
        for fl in ["workflow.py", "requirements.txt"]:
            with open(os.path.join(actual_path, fl), "w") as f:
                if fl == "workflow.py":
                    f.write(SCAFFOLD_DICT[request]["code"])
                else:
                    f.write(SCAFFOLD_DICT[request]["requirements"])
        return f"[bold green]SUCCESS[/]\tYour workflow was written to: {os.path.join(actual_path, 'workflow.py')}. Find requirements at: {os.path.join(actual_path, 'requirements.txt')}"
    except Exception as e:
        return f"[bold red]ERROR[/]\tThere was an error while trying to generate the example: {e}"
