import bm25s
import Stemmer

from bm25s.tokenization import Tokenized
from typing import List, Union
from vibe_llama_core.docs.data import services
from vibe_llama_core.constants import CHUNKS_SEPARATOR
from vibe_llama_core.docs.utils import get_instructions


async def get_text_chunks() -> List[str]:
    llamacloud = await get_instructions(services["LlamaCloud Services"])
    wfs = await get_instructions(services["llama-index-workflows"])
    llindex = await get_instructions(services["LlamaIndex"])
    wfs_chunks: List[str] = []
    llamacloud_chunks: List[str] = []
    llindex_chunks: List[str] = []
    if wfs:
        wfs_chunks = wfs.split(CHUNKS_SEPARATOR)
    if llamacloud:
        llamacloud_chunks = llamacloud.split(CHUNKS_SEPARATOR)
    if llindex:
        llindex_chunks = llindex.split(CHUNKS_SEPARATOR)
    # filter out empty chunks
    return (
        [chunk for chunk in wfs_chunks if chunk]
        + [chunk for chunk in llamacloud_chunks if chunk]
        + [chunk for chunk in llindex_chunks if chunk]
    )


class Retriever:
    """
    Retriever for vibe-llama documentation, leverages BM25 (enhanced with stemming) for lightweight, on-disk indexing and retrieval.

    Attributes:
        stemmer (Stemmer.Stemmer): Implements stemming for the English language.
        document_index (Union[List[List[str]], Tokenized]): Tokenized documents that serve as corpus for the BM25 index.
        retriever (bm25s.BM25): Document retriever
        text_chunks (List[str]): List of text chunks deriving from manual chunking of vibe-llama documentation.
        loaded (bool): Indicates whether or not the document index has been loaded on disk.
        loading_failed (bool): Indicates whether or not the loading of the document index failed.
    """

    def __init__(
        self,
    ) -> None:
        self.stemmer = Stemmer.Stemmer("english")
        self.document_index: Union[List[List[str]], Tokenized] = []
        self.retriever = bm25s.BM25()
        self.text_chunks: List[str] = []
        self.loaded = False
        self.loading_failed = False

    async def _prepare_document_index(self):
        """
        Prepares document index and loads it on disk.
        """
        text_chunks = await get_text_chunks()
        if text_chunks:
            self.text_chunks = text_chunks
            self.document_index = bm25s.tokenize(
                text_chunks, stopwords="en", stemmer=self.stemmer
            )
            self.retriever.index(self.document_index)
        else:
            self.loading_failed = True
        self.loaded = True

    def _query_embed(self, query: str) -> Union[List[List[str]], Tokenized]:
        """
        Embeds a query using BM25.

        Args:
            query (str): Query to embed.
        """
        return bm25s.tokenize(query, stemmer=self.stemmer, stopwords="en")

    async def retrieve(self, query: str, top_k: int = 5) -> List[str]:
        """
        Retrieves the top_k documents relevant to the specified query.

        Args:
            query (str): Query for document retrieval
            top_k (int): Maximum number of retrieved relevant documents
        """
        if not self.loaded or self.loading_failed:
            await self._prepare_document_index()
        embedding = self._query_embed(query)
        results, _ = self.retriever.retrieve(embedding, k=top_k)

        retrieved_docs: List[str] = []

        for i in range(results.shape[1]):
            doc = results[0, i]
            retrieved_docs.append(self.text_chunks[doc])

        return retrieved_docs
