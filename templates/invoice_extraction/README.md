# Invoice Extraction Workflow Example

This workflow demonstrates how to use [llama-index-workflows](https://github.com/run-llama/llama-index-workflows) and LlamaExtract to extract invoice data from documents in a human-in-the-loop, event-driven fashion. The workflow supports three extraction modes: base, advanced, and premium, and allows human approval before finalizing results.

## Installation

Install all required dependencies (including llama-index-workflows and LlamaCloud services):

```bash
pip install -e .
```

## Usage

Run the workflow from the command line:

```bash
python workflow.py \
  --path /path/to/invoice.pdf \
  --mode advanced
```

**Modes:**

- `base`: Fast extraction, minimal reasoning.
- `advanced`: Multimodal extraction with improved OCR and reasoning.
- `premium`: Highest accuracy, citations, and confidence scores.

**Note:**

- You must set your `LLAMA_CLOUD_API_KEY` in the environment before running.

## Workflow Overview

- **invoice_extraction**:
  Extracts invoice data using LlamaExtract and the selected extraction mode.
  Emits a `FeedbackRequiredEvent` with the extracted results.

- **human_feedback**:
  Waits for human approval of the extracted data.
  If approved, outputs the result; if declined, restarts extraction.

## Human-in-the-Loop Pattern

- The workflow pauses for human feedback after extraction.
- Input is provided interactively via the command line.

## Customization

- Extend the `InvoiceData` schema for additional invoice fields.
- Integrate with other LlamaIndex components for downstream analytics.

## References

- [llama-index-workflows documentation](https://github.com/run-llama/llama-index-workflows)
- [LlamaExtract documentation](https://docs.cloud.llamaindex.ai/llamaextract/getting_started)
