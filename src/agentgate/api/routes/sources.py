import hashlib
from typing import List
from fastapi import APIRouter, File, HTTPException, UploadFile
from agentgate.api.models import GitHubSourceRequest, SourceResponse
from agentgate.connectors.base import Chunk, Document, chunk_document
from agentgate.connectors.github import GitHubConnector
from agentgate.db.database import get_db
from agentgate.retrieval.dense import get_dense_retriever
from agentgate.retrieval.hybrid import get_hybrid_retriever

router = APIRouter(prefix="/sources", tags=["Sources"])


@router.get("", response_model=List[SourceResponse])
def list_sources():
    db = get_db()
    return db.list_sources()


@router.post("/github", response_model=SourceResponse)
async def connect_github_source(request: GitHubSourceRequest):
    """Connects and indexes a GitHub repository."""
    try:
        connector = GitHubConnector(repo=request.repo, token=request.token)
        db = get_db()
        dense = get_dense_retriever()

        # Mark source as syncing
        db.upsert_source(
            source_id=connector.source_id,
            name=connector.name,
            source_type="github",
            config={"repo": connector.full_repo},
            status="syncing",
        )

        docs = await connector.fetch_documents()
        all_chunks: List[Chunk] = []
        for doc in docs:
            all_chunks.extend(chunk_document(doc))

        # Index into ChromaDB
        if all_chunks:
            dense.add_chunks(all_chunks)
            # Invalidate/refresh hybrid sparse index
            get_hybrid_retriever().sync_sparse_index()

        db.upsert_source(
            source_id=connector.source_id,
            name=connector.name,
            source_type="github",
            config={"repo": connector.full_repo},
            doc_count=len(docs),
            status="synced",
        )

        source_data = db.get_source(connector.source_id)
        if not source_data:
            raise HTTPException(status_code=500, detail="Failed to retrieve saved source")
        return SourceResponse(**source_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GitHub connection failed: {str(e)}")


@router.post("/upload", response_model=SourceResponse)
async def upload_document_source(file: UploadFile = File(...)):
    """Uploads and indexes a Markdown or text file."""
    try:
        content_bytes = await file.read()
        text_content = content_bytes.decode("utf-8", errors="ignore")
        filename = file.filename or "uploaded_doc.md"

        source_id = f"upload_{hashlib.md5(filename.encode()).hexdigest()[:8]}"
        doc_id = hashlib.md5(f"{source_id}_{filename}".encode()).hexdigest()

        doc = Document(
            id=doc_id,
            title=filename.replace(".md", "").replace("_", " ").title(),
            content=text_content,
            source_id=source_id,
            source_type="upload",
            url=filename,
            metadata={"filename": filename},
        )

        chunks = chunk_document(doc)
        dense = get_dense_retriever()
        dense.add_chunks(chunks)
        get_hybrid_retriever().sync_sparse_index()

        db = get_db()
        db.upsert_source(
            source_id=source_id,
            name=f"File: {filename}",
            source_type="upload",
            config={"filename": filename},
            doc_count=1,
            status="synced",
        )

        source_data = db.get_source(source_id)
        return SourceResponse(**source_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")


@router.delete("/{source_id}")
def delete_source(source_id: str):
    """Disconnects a source and removes its indexed vectors."""
    db = get_db()
    dense = get_dense_retriever()

    dense.delete_by_source(source_id)
    success = db.delete_source(source_id)
    if not success:
        raise HTTPException(status_code=404, detail="Source not found")

    get_hybrid_retriever().sync_sparse_index()
    return {"message": f"Source '{source_id}' removed successfully"}
