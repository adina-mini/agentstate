"""Data connectors package for ingesting content from external sources."""

from agentgate.connectors.base import BaseConnector, Chunk, Document, chunk_document
from agentgate.connectors.github import GitHubConnector
from agentgate.connectors.markdown import MarkdownConnector

__all__ = [
    "BaseConnector",
    "Chunk",
    "Document",
    "chunk_document",
    "GitHubConnector",
    "MarkdownConnector",
]
