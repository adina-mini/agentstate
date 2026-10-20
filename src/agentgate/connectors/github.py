import base64
import hashlib
from typing import Any, Dict, List, Optional
import httpx
from agentgate.config import settings
from agentgate.connectors.base import BaseConnector, Document


class GitHubConnector(BaseConnector):
    """Ingests documentation, READMEs, and open issues from a GitHub repository."""

    def __init__(
        self,
        repo: str,
        token: Optional[str] = None,
        source_id: Optional[str] = None,
    ):
        """
        repo: 'owner/repo' or full URL like 'https://github.com/owner/repo'
        """
        clean_repo = repo.replace("https://github.com/", "").strip("/ ")
        self.owner, self.repo_name = clean_repo.split("/")[:2]
        self.full_repo = f"{self.owner}/{self.repo_name}"
        sid = source_id or f"github_{self.owner}_{self.repo_name}"
        super().__init__(source_id=sid, name=f"GitHub: {self.full_repo}")
        self.token = token or settings.github_token
        self.base_url = "https://api.github.com"

    def _headers(self) -> Dict[str, str]:
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AgentGate-KnowledgeGateway",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    async def fetch_documents(self) -> List[Document]:
        documents: List[Document] = []
        async with httpx.AsyncClient(headers=self._headers(), timeout=15.0) as client:
            # 1. Fetch README
            try:
                readme_doc = await self._fetch_readme(client)
                if readme_doc:
                    documents.append(readme_doc)
            except Exception as e:
                print(f"[GitHubConnector] Error fetching README: {e}")

            # 2. Fetch docs/ directory if it exists
            try:
                docs = await self._fetch_directory_files(client, path="docs")
                documents.extend(docs)
            except Exception as e:
                print(f"[GitHubConnector] Error fetching docs directory: {e}")

            # 3. Fetch recent open issues
            try:
                issue_docs = await self._fetch_issues(client)
                documents.extend(issue_docs)
            except Exception as e:
                print(f"[GitHubConnector] Error fetching issues: {e}")

        return documents

    async def _fetch_readme(self, client: httpx.AsyncClient) -> Optional[Document]:
        url = f"{self.base_url}/repos/{self.full_repo}/readme"
        res = await client.get(url)
        if res.status_code == 200:
            data = res.json()
            raw_content = base64.b64decode(data.get("content", "")).decode("utf-8", errors="ignore")
            doc_id = hashlib.md5(f"{self.full_repo}_readme".encode()).hexdigest()
            return Document(
                id=doc_id,
                title=f"{self.full_repo} - README",
                content=raw_content,
                source_id=self.source_id,
                source_type="github",
                url=data.get("html_url"),
                metadata={"path": data.get("path"), "type": "readme"},
            )
        return None

    async def _fetch_directory_files(
        self, client: httpx.AsyncClient, path: str = "docs"
    ) -> List[Document]:
        url = f"{self.base_url}/repos/{self.full_repo}/contents/{path}"
        res = await client.get(url)
        if res.status_code != 200:
            return []

        items = res.json()
        if not isinstance(items, list):
            return []

        docs: List[Document] = []
        for item in items:
            if item.get("type") == "file" and item.get("name", "").endswith((".md", ".txt")):
                file_url = item.get("url")
                if file_url:
                    f_res = await client.get(file_url)
                    if f_res.status_code == 200:
                        f_data = f_res.json()
                        raw_content = base64.b64decode(f_data.get("content", "")).decode(
                            "utf-8", errors="ignore"
                        )
                        doc_id = hashlib.md5(
                            f"{self.full_repo}_{item.get('path')}".encode()
                        ).hexdigest()
                        docs.append(
                            Document(
                                id=doc_id,
                                title=f"{self.full_repo} - {item.get('name')}",
                                content=raw_content,
                                source_id=self.source_id,
                                source_type="github",
                                url=item.get("html_url"),
                                metadata={"path": item.get("path"), "type": "doc"},
                            )
                        )
        return docs

    async def _fetch_issues(self, client: httpx.AsyncClient, limit: int = 15) -> List[Document]:
        url = f"{self.base_url}/repos/{self.full_repo}/issues?state=open&per_page={limit}"
        res = await client.get(url)
        if res.status_code != 200:
            return []

        issues = res.json()
        if not isinstance(issues, list):
            return []

        docs: List[Document] = []
        for issue in issues:
            # Skip PRs (which appear in the issues API with a pull_request key)
            if "pull_request" in issue:
                continue

            title = issue.get("title", "")
            body = issue.get("body") or ""
            issue_number = issue.get("number")
            combined_text = f"Issue #{issue_number}: {title}\n\nDescription:\n{body}"
            doc_id = hashlib.md5(f"{self.full_repo}_issue_{issue_number}".encode()).hexdigest()

            docs.append(
                Document(
                    id=doc_id,
                    title=f"{self.full_repo} - Issue #{issue_number}: {title}",
                    content=combined_text,
                    source_id=self.source_id,
                    source_type="github",
                    url=issue.get("html_url"),
                    metadata={"issue_number": issue_number, "type": "issue"},
                )
            )

        return docs
