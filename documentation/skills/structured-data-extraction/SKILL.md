---
name: Extract structured data from unstructured files (PDF, PPTX, DOCX...)
description: Extract structured data from PDFs and other unstructured file types in order to get the most relevant information from them. Requires llama_cloud_services package and LLAMA_CLOUD_API_KEY as an environment variable.
---

# Structured Data Extraction

## Quick start

- Define a schema for the for the data you would like to extract:

```python
from pydantic import BaseModel, Field


class Resume(BaseModel):
    name: str = Field(description="Full name of candidate")
    email: str = Field(description="Email address")
    skills: list[str] = Field(description="Technical skills and technologies")
```

- Create a LlamaExtract instance:

```python
from llama_cloud_services import LlamaExtract

# Initialize client
extractor = LlamaExtract(
    show_progress=True,
    check_interval=5,
)
```

- Define the extraction configuration:

```python
from llama_cloud import ExtractConfig, ExtractMode

# Configure extraction settings
extract_config = ExtractConfig(
    # Basic options
    extraction_mode=ExtractMode.MULTIMODAL,  # FAST, BALANCED, MULTIMODAL, PREMIUM
    extraction_target=ExtractTarget.PER_DOC,  # PER_DOC, PER_PAGE
    system_prompt="<Insert relevant context for extraction>",  # set system prompt - can leave blank
    # Advanced options
    chunk_mode=ChunkMode.PAGE,  # PAGE, SECTION
    high_resolution_mode=True,  # Enable for better OCR
    nvalidate_cache=False,  # Set to True to bypass cache
    # Extensions
    cite_sources=True,  # Enable citations
    use_reasoning=True,  # Enable reasoning (not available in FAST mode)
    confidence_scores=True,  # Enable confidence scores (MULTIMODAL/PREMIUM only)
)
```

- Extract the data from the document:

```python
result = extractor.extract(Resume, config, "resume.pdf")
print(result.data)
```

For more detailed code implementations, see [REFERENCE.md](REFERENCE.md).

## Requirements

The `llama_cloud_services` package must be installed in your environment (with it come the `pydantic` and `llama_cloud` packages):

```bash
pip install llama_cloud_services
```

And the `LLAMA_CLOUD_API_KEY` must be available as an environment variable:

```bash
export LLAMA_CLOUD_API_KEY="..."
```
