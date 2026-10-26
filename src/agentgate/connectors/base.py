from abc import ABC, abstractmethod
import hashlib
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class Document(BaseModel):
    id: str = Field(description="Unique document ID (e.g. hash of URL or path)")
    title: str = Field(description="Human readable title")
    content: str = Field(description="Full text content")
    source_id: str = Field(description="Source identifier")
    source_type: str = Field(description="Source type (github, markdown, etc.)")
    url: Optional[str] = Field(default=None, description="Direct URL if available")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Chunk(BaseModel):
    id: str = Field(description="Unique chunk ID")
    document_id: str = Field(description="Parent document ID")
    source_id: str = Field(default="", description="Parent source ID")
    content: str = Field(description="Chunk text snippet")
    chunk_index: int = Field(description="Index order of this chunk")
    source_title: str = Field(description="Source title")
    source_url: Optional[str] = Field(default=None)
    metadata: Dict[str, Any] = Field(default_factory=dict)


def chunk_document(
    doc: Document,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> List[Chunk]:
    """Splits a document into overlapping word/character chunks."""
    text = doc.content.strip()
    if not text:
        return []

    base_metadata = {
        "source_id": doc.source_id,
        "source_type": doc.source_type,
        **doc.metadata,
    }

    words = text.split()
    if len(words) <= chunk_size:
        chunk_id = hashlib.md5(f"{doc.id}_0".encode()).hexdigest()
        return [
            Chunk(
                id=chunk_id,
                document_id=doc.id,
                source_id=doc.source_id,
                content=text,
                chunk_index=0,
                source_title=doc.title,
                source_url=doc.url,
                metadata=base_metadata,
            )
        ]

    chunks: List[Chunk] = []
    start = 0
    idx = 0
    step = max(1, chunk_size - chunk_overlap)

    while start < len(words):
        chunk_words = words[start : start + chunk_size]
        chunk_text = " ".join(chunk_words)
        chunk_id = hashlib.md5(f"{doc.id}_{idx}".encode()).hexdigest()

        chunks.append(
            Chunk(
                id=chunk_id,
                document_id=doc.id,
                source_id=doc.source_id,
                content=chunk_text,
                chunk_index=idx,
                source_title=doc.title,
                source_url=doc.url,
                metadata={**base_metadata, "word_count": len(chunk_words)},
            )
        )
        idx += 1
        start += step

    return chunks


class BaseConnector(ABC):
    """Abstract base connector for all ingestion sources."""

    def __init__(self, source_id: str, name: str):
        self.source_id = source_id
        self.name = name

    @abstractmethod
    async def fetch_documents(self) -> List[Document]:
        """Fetch all documents from the source."""
        pass
