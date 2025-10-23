### Extract

### Quick Start

The simplest way to get started is to use the stateless API with the extraction configuration and the file/text to extract from:

```python
from llama_cloud_services import LlamaExtract
from llama_cloud import ExtractConfig, ExtractMode
from pydantic import BaseModel, Field

# Initialize client
extractor = LlamaExtract(
    show_progress=True,
    check_interval=5,
    project_id=project_id,
    organization_id=organization_id,
)


# Define schema using Pydantic
class Resume(BaseModel):
    name: str = Field(description="Full name of candidate")
    email: str = Field(description="Email address")
    skills: list[str] = Field(description="Technical skills and technologies")


# Configure extraction settings
extract_config = ExtractConfig(
    # Basic options
    extraction_mode=ExtractMode.MULTIMODAL,  # FAST, BALANCED, MULTIMODAL, PREMIUM
    extraction_target=ExtractTarget.PER_DOC,  # PER_DOC, PER_PAGE
    system_prompt="<Insert relevant context for extraction>",  # set system prompt - can leave blank
    # Advanced options
    high_resolution_mode=True,  # Enable for better OCR
    nvalidate_cache=False,  # Set to True to bypass cache
    # Extensions
    cite_sources=True,  # Enable citations
    use_reasoning=True,  # Enable reasoning (not available in FAST mode)
    confidence_scores=True,  # Enable confidence scores (MULTIMODAL/PREMIUM only)
)

# Extract data directly from document - no agent needed!
result = extractor.extract(Resume, config, "resume.pdf")
print(Resume.model_validate(result.data))
```

### Supported File Types

LlamaExtract supports the following file formats:

- **Documents**: PDF (.pdf), Word (.docx)
- **Text files**: Plain text (.txt), CSV (.csv), JSON (.json), HTML (.html, .htm), Markdown (.md)
- **Images**: PNG (.png), JPEG (.jpg, .jpeg)

### Different Input Types

```python
# From file path (string or Path)
result = extractor.extract(Resume, config, "resume.pdf")

# From file handle
with open("resume.pdf", "rb") as f:
    result = extractor.extract(Resume, config, f)

# From bytes with filename
with open("resume.pdf", "rb") as f:
    file_bytes = f.read()
from llama_cloud_services.extract import SourceText

result = extractor.extract(
    Resume, config, SourceText(file=file_bytes, filename="resume.pdf")
)

# From text content
text = "Name: John Doe\\nEmail: john@example.com\\nSkills: Python, AI"
result = extractor.extract(Resume, config, SourceText(text_content=text))
```

### Async Extraction

For better performance with multiple files or when integrating with async applications.
Here `queue_extraction` will enqueue the extraction jobs and exit. Alternatively, you
can use `aextract` to poll for the job and return the extraction results.

```python
import asyncio


async def extract_resumes():
    # Async extraction
    result = await extractor.aextract(Resume, config, "resume.pdf")
    print(result.data)

    # Queue extraction jobs (returns immediately)
    jobs = await extractor.queue_extraction(
        Resume, config, ["resume1.pdf", "resume2.pdf"]
    )
    print(f"Queued {len(jobs)} extraction jobs")
    return jobs


# Run async function
jobs = asyncio.run(extract_resumes())
# Check job status
for job in jobs:
    status = agent.get_extraction_job(job.id).status
    print(f"Job {job.id}: {status}")

# Get results when complete
results = [agent.get_extraction_run_for_job(job.id) for job in jobs]
```

### Core Concepts

- **Data Schema**: Structure definition for the data you want to extract in the form of a JSON schema or a Pydantic model.
- **Extraction Config**: Settings that control how extraction is performed (e.g., speed vs accuracy trade-offs).
- **Extraction Jobs**: Asynchronous extraction tasks that can be monitored.
- **Extraction Agents** (Advanced): Reusable extractors configured with a specific schema and extraction settings.

### Defining Schemas

Schemas define the structure of data you want to extract. You can use either Pydantic models or JSON Schema:

### Using Pydantic (Recommended)

```python
from pydantic import BaseModel, Field
from typing import List, Optional
from llama_cloud import ExtractConfig, ExtractMode


class Experience(BaseModel):
    company: str = Field(description="Company name")
    title: str = Field(description="Job title")
    start_date: Optional[str] = Field(description="Start date of employment")
    end_date: Optional[str] = Field(description="End date of employment")


class Resume(BaseModel):
    name: str = Field(description="Candidate name")
    experience: List[Experience] = Field(description="Work history")


# Use the schema for extraction
config = ExtractConfig(extraction_mode=ExtractMode.FAST)
result = extractor.extract(Resume, config, "resume.pdf")
```

### Using JSON Schema

```python
schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string", "description": "Candidate name"},
        "experience": {
            "type": "array",
            "description": "Work history",
            "items": {
                "type": "object",
                "properties": {
                    "company": {
                        "type": "string",
                        "description": "Company name",
                    },
                    "title": {"type": "string", "description": "Job title"},
                    "start_date": {
                        "anyOf": [{"type": "string"}, {"type": "null"}],
                        "description": "Start date of employment",
                    },
                    "end_date": {
                        "anyOf": [{"type": "string"}, {"type": "null"}],
                        "description": "End date of employment",
                    },
                },
            },
        },
    },
}

# Use the schema for extraction
config = ExtractConfig(extraction_mode=ExtractMode.FAST)
result = extractor.extract(schema, config, "resume.pdf")
```

### Important restrictions on JSON/Pydantic Schema

_LlamaExtract only supports a subset of the JSON Schema specification._ While limited, it should
be sufficient for a wide variety of use-cases.

- All fields are required by default. Nullable fields must be explicitly marked as such,
  using `anyOf` with a `null` type. See `"start_date"` field above.
- Root node must be of type `object`.
- Schema nesting must be limited to within 5 levels.
- The important fields are key names/titles, type and description. Fields for
  formatting, default values, etc. are **not supported**. If you need these, you can add the
  restrictions to your field description and/or use a post-processing step. e.g. default values can be supported by making a field optional and then setting `"null"` values from the extraction result to the default value.
- There are other restrictions on number of keys, size of the schema, etc. that you may
  hit for complex extraction use cases. In such cases, it is worth thinking how to restructure
  your extraction workflow to fit within these constraints, e.g. by extracting subset of fields
  and later merging them together.

### Extraction Configuration

Configure how extraction is performed using `ExtractConfig`. The schema is the most important part, but several configuration options can significantly impact the extraction process.

```python
from llama_cloud import ExtractConfig, ExtractMode, ExtractTarget

# Basic configuration
config = ExtractConfig(
    extraction_mode=ExtractMode.BALANCED,  # FAST, BALANCED, MULTIMODAL, PREMIUM
    extraction_target=ExtractTarget.PER_DOC,  # PER_DOC, PER_PAGE
    system_prompt="Focus on the most recent data",
    page_range="1-5,10-15",  # Extract from specific pages
)

# Advanced configuration
advanced_config = ExtractConfig(
    extraction_mode=ExtractMode.MULTIMODAL,
    high_resolution_mode=True,  # Better OCR accuracy
    invalidate_cache=False,  # Bypass cached results
    cite_sources=True,  # Enable source citations
    use_reasoning=True,  # Enable reasoning (not in FAST mode)
    confidence_scores=True,  # MULTIMODAL/PREMIUM only
)
```

### Key Configuration Options

**Extraction Mode**: Controls processing quality and speed

- `FAST`: Fastest processing, suitable for simple documents with no OCR
- `BALANCED`: Good speed/accuracy tradeoff for text-rich documents
- `MULTIMODAL`: For visually rich documents with text, tables, and images (recommended)
- `PREMIUM`: Highest accuracy with OCR, complex table/header detection

**Extraction Target**: Defines extraction scope

- `PER_DOC`: Apply schema to entire document (default)
- `PER_PAGE`: Apply schema to each page, returns array of results

**Advanced Options**:

- `system_prompt`: Additional system-level instructions
- `page_range`: Specific pages to extract (e.g., "1,3,5-7,9")
- `high_resolution_mode`: Better OCR for small text (slower processing)

**Extensions** (return additional metadata):

- `cite_sources`: Source tracing for extracted fields
- `use_reasoning`: Explanations for extraction decisions
- `confidence_scores`: Quantitative confidence measures (MULTIMODAL/PREMIUM only)

For complete configuration options, advanced settings, and detailed examples, see the [LlamaExtract Configuration Documentation](https://developers.llamaindex.ai/python/cloud/llamaextract/features/options).

### Extraction Agents (Advanced)

For reusable extraction workflows, you can create extraction agents that encapsulate both schema and configuration:

### Creating Agents

```python
from llama_cloud_services import LlamaExtract
from llama_cloud import ExtractConfig, ExtractMode
from pydantic import BaseModel, Field

# Initialize client
extractor = LlamaExtract()


# Define schema
class Resume(BaseModel):
    name: str = Field(description="Full name of candidate")
    email: str = Field(description="Email address")
    skills: list[str] = Field(description="Technical skills and technologies")


# Configure extraction settings
config = ExtractConfig(extraction_mode=ExtractMode.FAST)

# Create extraction agent
agent = extractor.create_agent(
    name="resume-parser", data_schema=Resume, config=config
)

# Use the agent
result = agent.extract("resume.pdf")
print(Resume.model_validate(result.data))
```

### Agent Batch Processing

Process multiple files with an agent:

```python
# Queue multiple files for extraction
jobs = await agent.queue_extraction(["resume1.pdf", "resume2.pdf"])

# Check job status
for job in jobs:
    status = agent.get_extraction_job(job.id).status
    print(f"Job {job.id}: {status}")

# Get results when complete
results = [agent.get_extraction_run_for_job(job.id) for job in jobs]
```

### Updating Agent Schemas

Schemas can be modified and updated after creation:

```python
# Update schema
agent.data_schema = new_schema

# Save changes
agent.save()
```

### Managing Agents

```python
# List all agents
agents = extractor.list_agents()

# Get specific agent
agent = extractor.get_agent(name="resume-parser")

# Delete agent
extractor.delete_agent(agent.id)
```

### When to Use Agents vs Direct Extraction

**Use Direct Extraction When:**

- One-off extractions
- Different schemas for different documents
- Simple workflows
- Getting started quickly

**Use Extraction Agents When:**

- Repeated extractions with the same schema
- Team collaboration (shared, named extractors)
- Complex workflows requiring state management
- Production systems with consistent extraction patterns
