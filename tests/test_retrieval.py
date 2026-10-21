import pytest
from agentgate.connectors.base import Document, chunk_document
from agentgate.retrieval.sparse import SparseRetriever


def test_chunk_document():
    doc = Document(
        id="test_doc_1",
        title="Test Document",
        content="This is word one. " * 100,
        source_id="src_1",
        source_type="markdown",
    )
    chunks = chunk_document(doc, chunk_size=50, chunk_overlap=10)
    assert len(chunks) > 1
    assert chunks[0].document_id == "test_doc_1"
    assert chunks[0].chunk_index == 0


def test_sparse_retriever():
    doc = Document(
        id="test_doc_2",
        title="Auth Guide",
        content="OAuth2 authentication requires client ID and client secret with redirect callback URL.",
        source_id="src_2",
        source_type="markdown",
    )
    chunks = chunk_document(doc)
    retriever = SparseRetriever(chunks=chunks)
    results = retriever.search("OAuth2 redirect callback", top_k=2)
    assert len(results) > 0
    top_chunk, score = results[0]
    assert score > 0.0
    assert "OAuth2" in top_chunk.content
