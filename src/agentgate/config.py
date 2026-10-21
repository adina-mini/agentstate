from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # LLM Settings
    groq_api_key: str = ""
    gemini_api_key: str = ""
    google_api_key: str = ""
    llm_provider: str = "gemini"  # "gemini" or "groq"
    llm_model: str = "gemini-1.5-flash"  # default model
    groq_model: str = "llama-3.1-70b-versatile"
    gemini_model: str = "gemini-1.5-flash"
    llm_temperature: float = 0.1

    # External APIs
    github_token: Optional[str] = None

    # Embeddings & Vector Store
    embedding_model: str = "all-MiniLM-L6-v2"
    chroma_persist_dir: str = "./data/chroma"

    # SQLite Database
    sqlite_db_path: str = "./data/agentgate.db"

    # Server Settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    mcp_transport: str = "stdio"

    # Chunking Configuration
    chunk_size: int = 500
    chunk_overlap: int = 50

    def ensure_directories(self) -> None:
        """Ensure necessary data directories exist."""
        Path(self.chroma_persist_dir).mkdir(parents=True, exist_ok=True)
        Path(self.sqlite_db_path).parent.mkdir(parents=True, exist_ok=True)


settings = Settings()
