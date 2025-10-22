### Classify

LlamaClassify enables automatic categorization of documents into types you define using natural-language rules. It's especially useful as a pre-processing step before extraction to route different document types to different extraction schemas.

**Common Use Cases:**

- **Pre-processing before extraction**: Classify first, then run schema-specific extraction with different schemas for each document type (e.g., invoice schema vs contract schema)
- **Intake routing**: Auto-separate invoices, receipts, contracts, and other business documents to appropriate workflows
- **Dataset curation**: Auto-tag archives into labeled categories for training or analysis

**Key Feature**: Classify can work directly on PDFs (parsing happens implicitly) OR on pre-parsed markdown content.

### Basic Usage - Direct File Classification

Classify can work directly on PDF files - parsing happens automatically under the hood:

```python
from llama_cloud_services.beta.classifier.client import ClassifyClient
from llama_cloud.types import ClassifierRule

# Initialize client
classifier = ClassifyClient.from_api_key(api_key)

# Define classification rules (natural language descriptions)
rules = [
    ClassifierRule(
        type="invoice",
        description="Documents that are invoices for goods or services, containing line items, prices, and payment terms",
    ),
    ClassifierRule(
        type="contract",
        description="Legal agreements between parties, containing terms, conditions, and signatures",
    ),
    ClassifierRule(
        type="receipt",
        description="Proof of payment documents, typically shorter than invoices, showing items purchased and amount paid",
    ),
]

# Classify a PDF directly (parsing happens implicitly)
result = await classifier.aclassify_file_path(
    rules=rules,
    file_input_path="document.pdf",
)

# Access classification results
classification = result.items[0].result
print(f"Predicted Type: {classification.type}")
print(f"Confidence: {classification.confidence:.2%}")
print(f"Reasoning: {classification.reasoning}")
```

### Parse → Classify → Extract Workflow

For more control, you can explicitly parse first, then classify the markdown, then extract structured data based on the classification:

```python
from llama_cloud_services import LlamaParse, LlamaExtract
from llama_cloud_services.beta.classifier.client import ClassifyClient
from llama_cloud_services.extract.extract import SourceText
from llama_cloud.types import ClassifierRule, ExtractConfig
import tempfile
from pathlib import Path

# Step 1: Parse document to markdown
parser = LlamaParse(result_type="markdown")
parse_result = await parser.aparse("document.pdf")
markdown_content = await parse_result.aget_markdown()

# Step 2: Classify based on markdown content
# Write markdown to temp file for classification
with tempfile.NamedTemporaryFile(
    mode="w", suffix=".md", delete=False, encoding="utf-8"
) as tmp:
    tmp.write(markdown_content)
    temp_path = Path(tmp.name)

classifier = ClassifyClient.from_api_key(api_key)
classification = await classifier.aclassify_file_path(
    rules=rules, file_input_path=str(temp_path)
)

doc_type = classification.items[0].result.type
print(f"Document classified as: {doc_type}")

# Step 3: Extract structured data using appropriate schema based on classification
extractor = LlamaExtract(api_key=api_key)

# Select schema based on classification
if doc_type == "invoice":
    schema = InvoiceSchema
elif doc_type == "contract":
    schema = ContractSchema
else:
    schema = GeneralSchema

# Extract using SourceText (markdown as input)
source_text = SourceText(text_content=markdown_content, filename="document.md")
extraction_result = extractor.extract(
    data_schema=schema,
    config=ExtractConfig(extraction_mode="BALANCED"),
    files=source_text,
)

print(f"Extracted data: {extraction_result.data}")
```

### Multi-Document Classification and Extraction

Route different document types to different extraction schemas in a single workflow:

```python
# Process multiple documents with different schemas
pdf_files = ["invoice.pdf", "contract.pdf", "receipt.pdf"]

for file_path in pdf_files:
    # Classify document
    result = await classifier.aclassify_file_path(
        rules=rules, file_input_path=file_path
    )
    classification = result.items[0].result

    print(f"\nProcessing: {file_path}")
    print(f"Type: {classification.type}")

    # Route to appropriate extraction schema
    if classification.type == "invoice":
        # Extract with invoice-specific schema
        extractor = LlamaExtract(api_key=api_key)
        data = await extractor.aextract(InvoiceSchema, config, file_path)
        print(f"Invoice data: {data.data}")

    elif classification.type == "contract":
        # Extract with contract-specific schema
        extractor = LlamaExtract(api_key=api_key)
        data = await extractor.aextract(ContractSchema, config, file_path)
        print(f"Contract data: {data.data}")
```
