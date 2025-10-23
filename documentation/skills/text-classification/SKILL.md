---
name: Classify files according to specific rules
description: Invoke this skill BEFORE implementing any text/document classification task to learn the correct llama_cloud_services API usage. Required reading before writing classification code." Requires the llama_cloud_services package and LLAMA_CLOUD_API_KEY as an environment variable.
---

# Texts and Files Classification

## Quick start

- Define classification rules:

```python
from llama_cloud.types import ClassifierRule

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
```

- Create the classification client and run the job:

```python
from llama_cloud_services.beta.classifier.client import ClassifyClient

# Initialize client
# Note: the beta client differs in usage slightly compared to other clients in llama-cloud-services
classifier = ClassifyClient.from_api_key(api_key)

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

For more detailed code implementations, see [REFERENCE.md](REFERENCE.md).

## Requirements

The `llama_cloud_services` package must be installed in your environment:

```bash
pip install llama_cloud_services
```

And the `LLAMA_CLOUD_API_KEY` must be available as an environment variable:

```bash
export LLAMA_CLOUD_API_KEY="..."
```
