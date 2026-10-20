from typing import Any, Dict, List, Optional, Tuple
import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer

from agentgate.config import settings
from agentgate.connectors.base import Chunk


class DenseRetriever:
    """Dense vector retriever using SentenceTransformers and ChromaDB."""

    def __init__(
        self,
        collection_name: str = "agentgate_knowledge",
        persist_dir: Optional[str] = None,
        model_name: Optional[str] = None,
    ):
        self.persist_dir = persist_dir or settings.chroma_persist_dir
        self.model_name = model_name or settings.embedding_model
        settings.ensure_directories()

        self.client = chromadb.PersistentClient(
            path=self.persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "AgentGate dense knowledge vectors"},
        )
        self._model: Optional[SentenceTransformer] = None

    @property
    def model(self) -> SentenceTransformer:
        if self._model is None:
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def add_chunks(self, chunks: List[Chunk]) -> int:
        if not chunks:
            return 0

        ids = [c.id for c in chunks]
        texts = [c.content for c in chunks]
        metadatas = [
            {
                "document_id": c.document_id,
                "chunk_index": c.chunk_index,
                "source_title": c.source_title,
                "source_url": c.source_url or "",
                **{f"meta_{k}": str(v) for k, v in c.metadata.items()},
            }
            for c in chunks
        ]

        embeddings = self.model.encode(texts, show_progress_bar=False).tolist()

        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )
        return len(chunks)

    def search(self, query: str, top_k: int = 5) -> List[Tuple[Chunk, float]]:
        if not query.strip():
            return []

        query_embedding = self.model.encode([query], show_progress_bar=False).tolist()[0]
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, max(1, self.collection.count())),
            include=["documents", "metadatas", "distances"],
        )

        output: List[Tuple[Chunk, float]] = []
        if not results or not results["ids"] or not results["ids"][0]:
            return output

        ids = results["ids"][0]
        docs = results["documents"][0] if results.get("documents") else []
        metas = results["metadatas"][0] if results.get("metadatas") else []
        distances = results["distances"][0] if results.get("distances") else []

        for idx, chunk_id in enumerate(ids):
            content = docs[idx] if idx < len(docs) else ""
            meta = metas[idx] if idx < len(metas) else {}
            dist = distances[idx] if idx < len(distances) else 1.0
            # Convert cosine distance to similarity score in [0, 1]
            score = max(0.0, min(1.0, 1.0 - (dist / 2.0)))

            chunk = Chunk(
                id=chunk_id,
                document_id=meta.get("document_id", ""),
                content=content,
                chunk_index=int(meta.get("chunk_index", 0)),
                source_title=meta.get("source_title", "Document"),
                source_url=meta.get("source_url") or None,
                metadata=meta,
            )
            output.append((chunk, round(score, 4)))

        return output

    def get_all_chunks(self) -> List[Chunk]:
        """Fetches all stored chunks (used to seed sparse retriever)."""
        count = self.collection.count()
        if count == 0:
            return []

        data = self.collection.get(include=["documents", "metadatas"])
        chunks: List[Chunk] = []
        for idx, cid in enumerate(data.get("ids", [])):
            content = data["documents"][idx] if data.get("documents") else ""
            meta = data["metadatas"][idx] if data.get("metadatas") else {}
            chunks.append(
                Chunk(
                    id=cid,
                    document_id=meta.get("document_id", ""),
                    content=content,
                    chunk_index=int(meta.get("chunk_index", 0)),
                    source_title=meta.get("source_title", "Document"),
                    source_url=meta.get("source_url") or None,
                    metadata=meta,
                )
            )
        return chunks

    def delete_by_source(self, source_id: str) -> None:
        """Deletes chunks matching a document/source prefix."""
        # Chroma where filter
        try:
            self.collection.delete(where={"meta_source_id": source_id})
        except Exception:
            pass

    def count(self) -> int:
        return self.collection.count()


_dense_retriever_instance: Optional[DenseRetriever] = None


def get_dense_retriever() -> DenseRetriever:
    global _dense_retriever_instance
    if _dense_retriever_instance is None:
        _dense_retriever_instance = DenseRetriever()
    return _dense_retriever_instance
