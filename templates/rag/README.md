# Retrieval-Augmented Generation (RAG) Workflow Example

This workflow demonstrates how to use [llama-index-workflows](https://github.com/run-llama/llama-index-workflows) to build a retrieval-augmented generation pipeline. Documents are ingested, indexed, retrieved, and used to answer queries with an LLM.

## Installation

Install all required dependencies (including llama-index-workflows and OpenAI LLM support):

```bash
pip install -e .
```

## Usage

Run the workflow from the command line:

```bash
python workflow.py \
  --path /path/to/documents/ \
  --query "What are the main findings in these reports?"
```

**Note:**

- You must set your `OPENAI_API_KEY` in the environment before running.

## Workflow Overview

- **document_processing_step**:
  Loads documents from the specified directory and creates a vector index.

- **retrieve_step**:
  Retrieves the top-k relevant documents for the input query.

- **generate_step**:
  Uses an LLM to answer the query based on the retrieved documents.

## Customization

- Adjust the retrieval parameters (e.g., `top_k`) for different use cases.
- Extend the workflow to support other document formats or post-processing.

## References

- [llama-index-workflows documentation](https://github.com/run-llama/llama-index-workflows)
