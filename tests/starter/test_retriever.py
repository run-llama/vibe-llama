import pytest
import Stemmer

from vibe_llama.starter.utils import get_text_chunks, Retriever, get_instructions
from vibe_llama.starter import services
from vibe_llama.starter.constants import CHUNKS_SEPARATOR


@pytest.mark.asyncio
async def test_get_text_chunks() -> None:
    res = await get_text_chunks()
    assert len(res) > 0
    llamacloud = await get_instructions(services["LlamaCloud Services"])
    wfs = await get_instructions(services["llama-index-workflows"])
    llindex = await get_instructions(services["LlamaIndex"])
    if llamacloud and wfs and llindex:
        assert len(llamacloud.split(CHUNKS_SEPARATOR)) + len(
            wfs.split(CHUNKS_SEPARATOR)
        ) + len(llindex.split(CHUNKS_SEPARATOR)) == len(res)


@pytest.mark.asyncio
async def test_retriever() -> None:
    retr = Retriever()
    assert not retr.loaded
    assert not retr.loading_failed
    assert retr.document_index == []
    assert retr.text_chunks == []
    assert isinstance(retr.stemmer, Stemmer.Stemmer)
    await retr._prepare_document_index()
    assert retr.loaded
    assert not retr.loading_failed
    assert len(retr.text_chunks) > 0
    assert len(retr.document_index) > 0
    res = await retr.retrieve("Human in the loop", top_k=3)
    assert isinstance(res, list)
    assert 0 < len(res) <= 3
