import tomli_w

BASE_EXAMPLE_REQUIREMENTS = [
    "llama-index-workflows",
    "llama-index-llms-openai",
]

DOCUMENT_PROCESSING_REQUIREMENTS = [
    "llama-index-workflows",
    "llama-cloud-services",
]

HUMAN_IN_THE_LOOP_REQUIREMENTS = [
    "llama-index-workflows",
    "llama-index-llms-openai",
]

INVOICE_EXTRACTOR_REQUIREMENTS = [
    "llama-index-workflows",
    "llama-cloud-services",
]

RAG_REQUIREMENTS = [
    "llama-index-llms-openai",
    "llama-index-embeddings-openai",
    "llama-index-workflows",
]

WEB_SCRAPING_REQUIREMENTS = [
    "llama-index-workflows",
    "llama-index-llms-google-genai",
]

PROJECTS = {
    "base_example": {
        "dependencies": BASE_EXAMPLE_REQUIREMENTS,
        "description": "A base example that showcases usage patterns for workflows",
    },
    "document_parsing": {
        "dependencies": DOCUMENT_PROCESSING_REQUIREMENTS,
        "description": "A workflow that, using LlamaParse, parses unstructured documents and returns their raw text content.",
    },
    "human_in_the_loop": {
        "dependencies": HUMAN_IN_THE_LOOP_REQUIREMENTS,
        "description": "A workflow showcasing how to use human in the loop",
    },
    "invoice_extraction": {
        "dependencies": INVOICE_EXTRACTOR_REQUIREMENTS,
        "description": "A workflow that, given an invoice, extracts several key details using LlamaExtract",
    },
    "rag": {
        "dependencies": RAG_REQUIREMENTS,
        "description": "A workflow that embeds, indexes and queries your documents on the fly, providing you with a simple RAG pipeline.",
    },
    "web_scraping": {
        "dependencies": WEB_SCRAPING_REQUIREMENTS,
        "description": "A workflow that, given several urls, scrapes and summarizes their content.",
    },
}


def generate_pyproject(sample_name: str, output_path: str) -> None:
    pyproject_data = {
        "project": {
            "name": sample_name,
            "version": "0.1.0",
            "description": PROJECTS[sample_name]["description"],
            "requires-python": ">=3.10",
            "readme": "README.md",
            "dependencies": PROJECTS[sample_name]["dependencies"],
        }
    }
    with open(output_path, "wb") as dest:
        tomli_w.dump(pyproject_data, dest)
