import os
import numpy as np
import httpx
import asyncio

from pathlib import Path
from typing import Optional, Iterable, List
from fastembed import SparseTextEmbedding, SparseEmbedding
from .text_chunks import get_text_chunks


def write_file(file_path: str, content: str, service_url: str) -> None:
    directory = os.path.dirname(file_path)
    if not Path(directory).is_dir():
        os.makedirs(directory, exist_ok=True)
    if Path(file_path).is_file():
        with open(file_path) as f:
            file_content = f.read()
        content = file_content + "\n" + content
    if file_path.startswith(".cursor"):
        frontmatter = f"""---
description: Instructions from {service_url} for Cursor coding agent
alwaysApply: false
---

"""
        content = frontmatter + "\n" + content
    with open(file_path, "w") as w:
        w.write(content)
    return None


async def get_instructions(
    instructions_url: str, max_retries: int = 10, retry_interval: float = 0.5
) -> Optional[str]:
    async with httpx.AsyncClient() as client:
        retries = 0
        while True:
            if retries < max_retries:
                response = await client.get(instructions_url)
                if response.status_code == 200:
                    return response.text
                else:
                    retries += 1
                    await asyncio.sleep(retry_interval)
            else:
                return None


class Retriever:
    def __init__(
        self,
        model_name: str = "Qdrant/bm25",
        cache_dir: str = ".vibe-llama/model_cache",
    ) -> None:
        self.model = SparseTextEmbedding(model_name, cache_dir)
        self.document_vectors: Iterable[SparseEmbedding] = []
        self.text_chunks: List[str] = []
        self.loaded = False
        self.loading_failed = False

    async def _prepare_document_vectors(self):
        text_chunks = await get_text_chunks()
        if text_chunks:
            self.text_chunks = text_chunks
            self.document_vectors = list(self.model.embed(text_chunks))
        else:
            self.loading_failed = True
        self.loaded = True

    def _query_embed(self, query: str) -> List[SparseEmbedding]:
        return list(self.model.embed(query))

    def _get_docs_values(self) -> list:
        return [emb.values for emb in self.document_vectors]

    async def retrieve(self, query: str, top_k: int = 5) -> Optional[List[str]]:
        if not self.loaded or self.loading_failed:
            await self._prepare_document_vectors()
        embedding = self._query_embed(query)
        query_values = embedding[0].values
        docs_values = self._get_docs_values()
        scores = np.dot(docs_values, query_values)
        # sort the scores in descending order
        sorted_scores = np.argsort(scores)[::-1]
        docs_to_return = []
        for i in range(top_k):
            docs_to_return.append(self.text_chunks[sorted_scores[i]])
        return docs_to_return
