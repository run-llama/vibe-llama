# Document Parsing Workflow Example

This workflow demonstrates how to use [llama-index-workflows](https://github.com/run-llama/llama-index-workflows) to parse documents with LlamaParse in three modes: cost-effective, agentic, and agentic plus. The workflow is event-driven and async-first, making it suitable for intelligent automation and scalable document processing.

## Installation

Install all required dependencies (including llama-index-workflows and LlamaCloud services):

```bash
pip install -e .
```

## Usage

Run the workflow from the command line:

```bash
python workflow.py \
  --path /path/to/document.pdf \
  --mode agentic
```

**Modes:**

- `cost_effective`: Uses LLM-based parsing for lower cost.
- `agentic`: Uses agentic parsing with OpenAI GPT-4.
- `agentic_plus`: Uses agentic parsing with Anthropic Sonnet.

**Note:**

- You must set your `LLAMA_CLOUD_API_KEY` in the environment before running.

## Workflow Overview

- **choose_document_parsing_mode**:
  Selects the parsing mode based on user input and emits the corresponding event.

- **parse_document_cost_effective / agentic / agentic_plus**:
  Parses the document using the selected LlamaParse mode and outputs the result as markdown.

## Customization

- Extend the workflow to add post-processing, validation, or data extraction steps.
- Integrate with other LlamaIndex components for advanced document analytics.

## References

- [llama-index-workflows documentation](https://github.com/run-llama/llama-index-workflows)
- [LlamaParse documentation](https://docs.cloud.llamaindex.ai/llamaparse/getting_started)
