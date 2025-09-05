# Web Scraping Workflow Example

This workflow demonstrates how to use [llama-index-workflows](https://github.com/run-llama/llama-index-workflows) and Google Gemini to summarize the content of multiple URLs in an event-driven, async-first fashion.

## Installation

Install all required dependencies (including llama-index-workflows and Google GenAI support):

```bash
pip install -e .
```

## Usage

Run the workflow from the command line:

```bash
python workflow.py \
  --url https://example.com/page1 \
  --url https://example.com/page2
```

**Note:**

- You must set your `GOOGLE_API_KEY` in the environment before running.

## Workflow Overview

- **process_urls**:
  Receives a list of URLs and emits a `URLReadEvent` for each.

- **get_url_content**:
  Uses Google Gemini to summarize the content of each URL.

- **finalize**:
  Collects all summaries and outputs the combined result.

## Customization

- Extend the workflow to extract additional metadata or perform further analysis.
- Integrate with other LlamaIndex components for downstream tasks.

## References

- [llama-index-workflows documentation](https://github.com/run-llama/llama-index-workflows)
