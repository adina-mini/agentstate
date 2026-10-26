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


import io
from pathlib import Path
import pypdf


@router.get("/{source_id}")
def get_source_details(source_id: str):
    """Retrieves metadata and sample indexed chunks for a source."""
    db = get_db()
    source_data = db.get_source(source_id)
    if not source_data:
        raise HTTPException(status_code=404, detail="Source not found")

    dense = get_dense_retriever()
    chunks = dense.get_chunks_by_source(source_id, limit=10)

    return {
        **source_data,
        "preview_chunks": [
            {
                "id": c.id,
                "chunk_index": c.chunk_index,
                "content": c.content[:350] + ("..." if len(c.content) > 350 else ""),
                "source_title": c.source_title,
            }
            for c in chunks
        ],
    }


@router.post("/upload", response_model=SourceResponse)
async def upload_document_source(file: UploadFile = File(...)):
    """Uploads and indexes a PDF, Markdown, or text file."""
    try:
        content_bytes = await file.read()
        filename = file.filename or "uploaded_doc.txt"
        file_ext = Path(filename).suffix.lower()

        if file_ext == ".pdf":
            try:
                reader = pypdf.PdfReader(io.BytesIO(content_bytes))
                if len(reader.pages) == 0:
                    raise ValueError("The uploaded PDF contains no pages.")
                pages_text = []
                for page_idx, page in enumerate(reader.pages):
                    txt = page.extract_text() or ""
                    if txt.strip():
                        pages_text.append(f"--- Page {page_idx + 1} ---\n{txt.strip()}")
                text_content = "\n\n".join(pages_text)
                if not text_content.strip():
                    raise ValueError(
                        "No extractable text found in this PDF (it might be an image-only scan)."
                    )
            except Exception as pdf_err:
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to extract text from PDF: {str(pdf_err)}",
                )
        else:
            text_content = content_bytes.decode("utf-8", errors="ignore")
            if not text_content.strip():
                raise HTTPException(
                    status_code=400,
                    detail="The uploaded text document is empty.",
                )

        source_id = f"upload_{hashlib.md5(filename.encode()).hexdigest()[:8]}"
        clean_title = Path(filename).stem.replace("_", " ").replace("-", " ").title()
        chunks = []

        if file_ext == ".pdf":
            try:
                reader = pypdf.PdfReader(io.BytesIO(content_bytes))
                if len(reader.pages) == 0:
                    raise ValueError("The uploaded PDF contains no pages.")
                
                for page_idx, page in enumerate(reader.pages):
                    txt = (page.extract_text() or "").strip()
                    if not txt:
                        continue
                    page_num = page_idx + 1
                    page_doc_id = hashlib.md5(f"{source_id}_{filename}_p{page_num}".encode()).hexdigest()
                    page_doc = Document(
                        id=page_doc_id,
                        title=f"{clean_title} (Page {page_num})",
                        content=txt,
                        source_id=source_id,
                        source_type="upload",
                        url=filename,
                        metadata={
                            "filename": filename,
                            "file_type": "pdf",
                            "page_number": page_num,
                            "total_pages": len(reader.pages),
                            "source_id": source_id,
                        },
                    )
                    chunks.extend(chunk_document(page_doc))

                if not chunks:
                    raise ValueError(
                        "No extractable text found in this PDF (it might be an image-only scan)."
                    )
            except Exception as pdf_err:
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to extract text from PDF: {str(pdf_err)}",
                )
        else:
            text_content = content_bytes.decode("utf-8", errors="ignore")
            if not text_content.strip():
                raise HTTPException(
                    status_code=400,
                    detail="The uploaded text document is empty.",
                )

            doc_id = hashlib.md5(f"{source_id}_{filename}".encode()).hexdigest()
            doc = Document(
                id=doc_id,
                title=clean_title,
                content=text_content,
                source_id=source_id,
                source_type="upload",
                url=filename,
                metadata={
                    "filename": filename,
                    "file_type": file_ext.replace(".", ""),
                    "source_id": source_id,
                },
            )
            chunks = chunk_document(doc)

        dense = get_dense_retriever()
        
        # Clean previous chunks if re-uploading the same file
        dense.delete_by_source(source_id)
        dense.add_chunks(chunks)
        get_hybrid_retriever().sync_sparse_index()

        db = get_db()
        db.upsert_source(
            source_id=source_id,
            name=f"File: {filename}",
            source_type="upload",
            config={
                "filename": filename,
                "file_type": file_ext.replace(".", ""),
                "chunks_indexed": len(chunks),
            },
            doc_count=len(chunks),
            status="synced",
        )

        source_data = db.get_source(source_id)
        return SourceResponse(**source_data)
    except HTTPException:
        raise
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
