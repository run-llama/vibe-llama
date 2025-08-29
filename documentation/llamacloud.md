# High-level LlamaCloud Doc for LLMs and Humans

# Building with LlamaCloud in Python

## A compendium of examples and explanations

### Introduction

[LlamaCloud](https://cloud.llamaindex.ai/) is a cloud platform provided by LlamaIndex for intelligent document processing.

It is composed of three main services:

- [LlamaParse](https://www.llamaindex.ai/llamaparse), for parsing and extracting text, charts, tables and images from unstructured files
- [LlamaExtract](https://www.llamaindex.ai/llamaextract), for extracting structured data from files following specific patterns
- LlamaCloud Index, for storing, indexing and retrieving documents, especially oriented towards retrieval-augmented generation.

You can interact with LlamaCloud services through a python SDK, that you can easily obtain by installing it from PyPI:

```bash
# if you are using pip
pip install llama-cloud-services
# if you are in a uv project
uv add llama-cloud-services

```

It is important to remember that, before using any of these services, you need to have the `LLAMA_CLOUD_API_KEY` set in your environment:

```bash
export LLAMA_CLOUD_API_KEY="***"
```

There is thus no need to pass the API key directly as an argument to any of the services listed below.

Let's see some examples of how to interact with the various services.

<!-- sep---sep -->

### Parse

You can get started by creating simple scripts:

```python
from llama_cloud_services import LlamaParse

parser = LlamaParse(
    parse_mode="parse_page_with_agent",
    model="openai-gpt-4-1-mini",
    high_res_ocr=True,
    adaptive_long_table=True,
    outlined_table_extraction=True,
    output_tables_as_HTML=True,
    result_type="markdown",
    project_id=project_id,
    organization_id=organization_id,
)

# sync
result = parser.parse("./my_file.pdf")

# sync batch
results = parser.parse(["./my_file1.pdf", "./my_file2.pdf"])

# async
result = await parser.aparse("./my_file.pdf")

# async batch
results = await parser.aparse(["./my_file1.pdf", "./my_file2.pdf"])
```

The result object is a fully typed `JobResult` object, and you can interact with it to parse and transform various parts of the result:

```python
# get the llama-index markdown documents
markdown_documents = result.get_markdown_documents(split_by_page=True)

# get the llama-index text documents
text_documents = result.get_text_documents(split_by_page=False)

# get the image documents
image_documents = result.get_image_documents(
    include_screenshot_images=True,
    include_object_images=False,
    # Optional: download the images to a directory
    # (default is to return the image bytes in ImageDocument objects)
    image_download_dir="./images",
)

# access the raw job result
# Items will vary based on the parser configuration
for page in result.pages:
    print(page.text)
    print(page.md)
    print(page.images)
    print(page.layout)
    print(page.structuredData)

# you can also extract tables from the parse results
result = parser.get_json_result("./my_file.pdf")
tables = parser.get_tables(result)
```

See more details about the result object in the [example notebook](https://www.notion.so/llamaindex/docs/examples-py/parse/demo_json_tour.ipynb).

<!-- sep---sep -->

### Using different parse pre-sets

In the following examples, you will find some sets of arguments that you can pass to LlamaParse. Please, make sure to use only these pre-defined sets of arguments when initializing LlamaParse.

```python
from llama_cloud_services import LlamaParse

# Cost-Effective Mode
llama_parser = LlamaParse(
    # See how to get your API key at https://docs.cloud.llamaindex.ai/api_key
    parse_mode="parse_page_with_llm",
    high_res_ocr=True,
    adaptive_long_table=True,
    outlined_table_extraction=True,
    output_tables_as_HTML=True,
    result_type="markdown",
    project_id=project_id,
    organization_id=organization_id,
)

# Agentic Mode (Default)
llama_parser = LlamaParse(
    # See how to get your API key at https://docs.cloud.llamaindex.ai/api_key
    parse_mode="parse_page_with_agent",
    model="openai-gpt-4-1-mini",
    high_res_ocr=True,
    adaptive_long_table=True,
    outlined_table_extraction=True,
    output_tables_as_HTML=True,
    result_type="markdown",
    project_id=project_id,
    organization_id=organization_id,
)

# Agentic Plus Mode
llama_parser = LlamaParse(
    # See how to get your API key at https://docs.cloud.llamaindex.ai/api_key
    parse_mode="parse_page_with_agent",
    model="anthropic-sonnet-4.0",
    high_res_ocr=True,
    adaptive_long_table=True,
    outlined_table_extraction=True,
    output_tables_as_HTML=True,
    result_type="markdown",
    project_id=project_id,
    organization_id=organization_id,
)
```

<!-- sep---sep -->

### Using with file object / bytes

You can parse a file object directly:

```python
from llama_cloud_services import LlamaParse

parser = LlamaParse(
    parse_mode="parse_page_with_agent",
    model="openai-gpt-4-1-mini",
    high_res_ocr=True,
    adaptive_long_table=True,
    outlined_table_extraction=True,
    output_tables_as_HTML=True,
    result_type="markdown",
    project_id=project_id,
    organization_id=organization_id,
)

file_name = "my_file1.pdf"
extra_info = {"file_name": file_name}

with open(f"./{file_name}", "rb") as f:
    # must provide extra_info with file_name key with passing file object
    result = parser.parse(f, extra_info=extra_info)

# you can also pass file bytes directly
with open(f"./{file_name}", "rb") as f:
    file_bytes = f.read()
    # must provide extra_info with file_name key with passing file bytes
    result = parser.parse(file_bytes, extra_info=extra_info)
```

### Using with `SimpleDirectoryReader`

You can also integrate the parser as the default PDF loader in `SimpleDirectoryReader`:

```python
from llama_cloud_services import LlamaParse
from llama_index.core import SimpleDirectoryReader

parser = LlamaParse(
    parse_mode="parse_page_with_agent",
    model="openai-gpt-4-1-mini",
    high_res_ocr=True,
    adaptive_long_table=True,
    outlined_table_extraction=True,
    output_tables_as_HTML=True,
    result_type="markdown",
    project_id=project_id,
    organization_id=organization_id,
)

file_extractor = {".pdf": parser}
documents = SimpleDirectoryReader(
    "./data", file_extractor=file_extractor
).load_data()
```

<!-- sep---sep -->

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
    chunk_mode=ChunkMode.PAGE,  # PAGE, SECTION
    high_resolution_mode=True,  # Enable for better OCR
    nvalidate_cache=False,  # Set to True to bypass cache
    # Extensions
    cite_sources=True,  # Enable citations
    use_reasoning=True,  # Enable reasoning (not available in FAST mode)
    confidence_scores=True,  # Enable confidence scores (MULTIMODAL/PREMIUM only)
)

# Extract data directly from document - no agent needed!
result = extractor.extract(Resume, config, "resume.pdf")
print(result.data)
```

<!-- sep---sep -->

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

<!-- sep---sep -->

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

<!-- sep---sep -->

### Extraction Configuration

Configure how extraction is performed using `ExtractConfig`. The schema is the most important part, but several configuration options can significantly impact the extraction process.

```python
from llama_cloud import ExtractConfig, ExtractMode, ChunkMode, ExtractTarget

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
    chunk_mode=ChunkMode.PAGE,  # PAGE, SECTION
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
- `chunk_mode`: Document splitting strategy (`PAGE` or `SECTION`)
- `high_resolution_mode`: Better OCR for small text (slower processing)

**Extensions** (return additional metadata):

- `cite_sources`: Source tracing for extracted fields
- `use_reasoning`: Explanations for extraction decisions
- `confidence_scores`: Quantitative confidence measures (MULTIMODAL/PREMIUM only)

For complete configuration options, advanced settings, and detailed examples, see the [LlamaExtract Configuration Documentation](https://docs.cloud.llamaindex.ai/llamaextract/features/options).

<!-- sep---sep -->

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
print(result.data)
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

<!-- sep---sep -->

### Index

### Usage

You can create an index on LlamaCloud using the following code. By default, new indexes use managed embeddings (OpenAI text-embedding-3-small, 1536 dimensions, 1 credit/page):

```python
import os

from llama_index.core import SimpleDirectoryReader
from llama_cloud_services import LlamaCloudIndex

# create a new index (uses managed embeddings by default)
index = LlamaCloudIndex.from_documents(
    documents,
    "my_first_index",
    project_name="default",
    api_key="llx-...",
    verbose=True,
)

# connect to an existing index
index = LlamaCloudIndex("my_first_index", project_name="default")
```

You can also configure a retriever for managed retrieval:

```python
# from the existing index
index.as_retriever()

# from scratch
from llama_cloud_services import LlamaCloudRetriever

retriever = LlamaCloudRetriever("my_first_index", project_name="default")
```

And of course, you can use other index shortcuts to get use out of your new managed index:

```python
query_engine = index.as_query_engine(llm=llm)

chat_engine = index.as_chat_engine(llm=llm)
```

## Retriever Settings

A full list of retriever settings/kwargs is below:

- `dense_similarity_top_k`: Optional[int] -- If greater than 0, retrieve `k` nodes using dense retrieval
- `sparse_similarity_top_k`: Optional[int] -- If greater than 0, retrieve `k` nodes using sparse retrieval
- `enable_reranking`: Optional[bool] -- Whether to enable reranking or not. Sacrifices some speed for accuracy
- `rerank_top_n`: Optional[int] -- The number of nodes to return after reranking initial retrieval results
- `alpha` Optional[float] -- The weighting between dense and sparse retrieval. 1 = Full dense retrieval, 0 = Full sparse retrieval.

<!-- sep---sep -->

# Building with LlamaCloud in TypeScript

## A compendium of examples and explanations

### Introduction

[LlamaCloud](https://cloud.llamaindex.ai/) is a cloud platform provided by LlamaIndex for intelligent document processing.

It is composed of three main services:

- [LlamaParse](https://www.llamaindex.ai/llamaparse), for parsing and extracting text, charts, tables and images from unstructured files
- [LlamaExtract](https://www.llamaindex.ai/llamaextract), for extracting structured data from files following specific patterns
- LlamaCloud Index, for storing, indexing and retrieving documents, especially oriented towards retrieval-augmented generation.

You can interact with LlamaCloud services through a TypeScript SDK, that you can easily obtain by installing it from NPM:

```bash
npm install llama-cloud-services
```

Let's see some examples of how to interact with the various services.

<!-- sep---sep -->

### Parse

You can interact with Parse as in the following code:

```tsx
import { LlamaParseReader } from "llama-cloud-services";

const reader = new LlamaParseReader({ resultType: "markdown" });
// this would return an array of Document containing text under the text attribute
const documents = await reader.loadData("my-file.pdf");
// this would return an array of the JSON representation of all elements of the parsing job contained under the pages attribute
const result = await reader.parse("my-file.pdf"); // you can also use file bytes a Uint8Array here
```

You can then extract images or tables:

```tsx
const images = await reader.getImages(result, "static/images"); // specify a download path
const tables = await reader.getTables(result, "data/tables"); // this will return an array of strings pointing to the paths of the CSV files where the tables are saved
```

> Remember to export your LLAMA_CLOUD_API_KEY as an environment variable!

<!-- sep---sep -->

### Extract

You can interact with Extract as in the following code:

```tsx
import { LlamaExtract } from "llama-cloud-services";

const extractClient = new LlamaExtract(
  process.env.LLAMA_CLOUD_API_KEY!,
  "<https://api.cloud.llamaindex.ai>", // specify the base URL
);
```

You need to define a data schema (in JSON format) to perform extraction:

```tsx
const dataSchema = {
  type: "object",
  properties: {
    text: {
      type: "string",
      description: "Text from the file",
    },
  },
  required: ["text"],
};
```

You can then use the data schema to perform extraction directly, or to create an extraction agent and extract data with it:

```tsx
// Create an agent
const agent = await extractClient.createAgent("TextAgent", dataSchema);

// if you already created an agent, you can fetch it with its name
const namedAgent = await extractClient.getAgent("TextAgent");

// Extract with the agent
const result = await agent.extract("test-extract-agent.md");

// Or you can extract directly from a file buffer
const buffer = await fs.readFile("test-extract-agent.md");
const resultBuffer = await agent!.extract(
  undefined, // leave the path undefined
  buffer,
  "test-extract-agent.md", // specify the filename - highly recommended!
);
```

As said, you can perform all these same operation directly with a LlamaExtract instance, using the `extract` method and specifying the extraction schema and the extraction configuration:

```tsx
import { ExtractConfig } from "llama-cloud-services";

const result = await extractClient.extract(
  dataSchema,
  {} as ExtractConfig,
  "test-extract.md",
);
```

The results will be `ExtractResult` objects, with the `data` attribute (the JSON representation of the extracted data) and the `extractionMetadata` attribute (metadata about the extraction).

<!-- sep---sep -->

### Index

You can interact with Index as in the following code:

```tsx
import { LlamaCloudIndex } from "llama-cloud-services";

const index = new LlamaCloudIndex({
  name: process.env.PIPELINE_NAME as string,
  projectName: "Default",
  apiKey: process.env.LLAMA_CLOUD_API_KEY, // can provide API-key in the constructor or in the env
});

// use Index as retriever
const retriever = index.asRetriever({
  similarityTopK: 5,
});
```

Retrieve nodes and use them for RAG purposes:

```tsx
const nodes = await retriever.retrieve(
  "How many cells are in the human brain?",
); // the query here is a string
```

Here is a simple example of how to insert the retrieved nodes inside a RAG framework:

```tsx
import { generateText } from "ai";
import { openai } from "@ai-sdk/openai";
import { NodeWithScore, MetadataMode } from "llamaindex";

export async function retrievalAugmentedGeneration(
  nodes: NodeWithScore[],
  prompt: string,
): Promise<string> {
  let mainText: string = "";

  for (const node of nodes) {
    mainText += `\\t{information: '${node.node.getContent(
      MetadataMode.ALL,
    )}', relevanceScore: '${node.score ?? "no score"}'}\\n`;
  }

  const { text } = await generateText({
    model: openai("gpt-4.1"),
    prompt: `[\\n${mainText}\\n]\\n\\nBased on the information you are given and on the relevance score of that (where -1 means no score available), answer to this user prompt: '${prompt}'`,
  });

  return text;
}
```

<!-- sep---sep -->
