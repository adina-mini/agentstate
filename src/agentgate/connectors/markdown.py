import hashlib
from pathlib import Path
from typing import List, Optional, Union
from agentgate.connectors.base import BaseConnector, Document


class MarkdownConnector(BaseConnector):
    """Ingests local markdown and text files or parsed directory trees."""

    def __init__(
        self,
        file_path_or_dir: Union[str, Path],
        source_id: Optional[str] = None,
        name: Optional[str] = None,
    ):
        self.target_path = Path(file_path_or_dir)
        sid = source_id or f"local_{self.target_path.stem}"
        sname = name or f"Local Docs: {self.target_path.name}"
        super().__init__(source_id=sid, name=sname)

    async def fetch_documents(self) -> List[Document]:
        documents: List[Document] = []
        if not self.target_path.exists():
            return documents

        if self.target_path.is_file():
            doc = self._read_file(self.target_path)
            if doc:
                documents.append(doc)
        elif self.target_path.is_dir():
            for p in self.target_path.rglob("*"):
                if p.is_file() and p.suffix.lower() in [".md", ".txt", ".markdown"]:
                    doc = self._read_file(p)
                    if doc:
                        documents.append(doc)

        return documents

    def _read_file(self, file_path: Path) -> Optional[Document]:
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore").strip()
            if not content:
                return None

            doc_id = hashlib.md5(f"{file_path.resolve()}".encode()).hexdigest()
            return Document(
                id=doc_id,
                title=file_path.stem.replace("_", " ").title(),
                content=content,
                source_id=self.source_id,
                source_type="markdown",
                url=str(file_path.resolve()),
                metadata={"filename": file_path.name, "path": str(file_path)},
            )
        except Exception as e:
            print(f"[MarkdownConnector] Error reading {file_path}: {e}")
            return None
