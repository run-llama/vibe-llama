---
name: Retrieve relevant information through RAG
description: Leverage Retrieval Augmented Generation to retrieve relevant information from a a LlamaCloud Index. Requires the llama_cloud_services package and LLAMA_CLOUD_API_KEY as an environment variable.
---

# Information Retrieval

## Quick start

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

# perform retrieval
result = retriever.retrieve("What is the capital of France?")
```

And of course, you can use other index shortcuts to get use out of your new managed index:

```python
query_engine = index.as_query_engine(llm=llm)

# perform retrieval and generation
result = query_engine.query("What is the capital of France?")
```

## Retriever Settings

A full list of retriever settings/kwargs is below:

- `dense_similarity_top_k`: Optional[int] -- If greater than 0, retrieve `k` nodes using dense retrieval
- `sparse_similarity_top_k`: Optional[int] -- If greater than 0, retrieve `k` nodes using sparse retrieval
- `enable_reranking`: Optional[bool] -- Whether to enable reranking or not. Sacrifices some speed for accuracy
- `rerank_top_n`: Optional[int] -- The number of nodes to return after reranking initial retrieval results
- `alpha` Optional[float] -- The weighting between dense and sparse retrieval. 1 = Full dense retrieval, 0 = Full sparse retrieval.

## Requirements

The `llama_cloud_services` and `llama-index-core` packages must be installed in your environment:

```bash
pip install llama-index-core llama_cloud_services
```

And the `LLAMA_CLOUD_API_KEY` must be available as an environment variable:

```bash
export LLAMA_CLOUD_API_KEY="..."
```
