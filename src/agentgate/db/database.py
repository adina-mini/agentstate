import json
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional
from agentgate.config import settings


class Database:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or settings.sqlite_db_path
        settings.ensure_directories()
        self._init_schema()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Sources table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS sources (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    config TEXT NOT NULL,
                    doc_count INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'synced',
                    last_synced DATETIME DEFAULT CURRENT_TIMESTAMP,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
            # Eval logs table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS eval_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    query TEXT NOT NULL,
                    strategy TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    faithfulness REAL,
                    relevance REAL,
                    latency_ms REAL,
                    tokens_used INTEGER,
                    cost_usd REAL,
                    sources TEXT
                );
                """
            )
            conn.commit()

    # --- Source Operations ---
    def upsert_source(
        self,
        source_id: str,
        name: str,
        source_type: str,
        config: Dict[str, Any],
        doc_count: int = 0,
        status: str = "synced",
    ) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO sources (id, name, type, config, doc_count, status, last_synced)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(id) DO UPDATE SET
                    name = excluded.name,
                    type = excluded.type,
                    config = excluded.config,
                    doc_count = excluded.doc_count,
                    status = excluded.status,
                    last_synced = CURRENT_TIMESTAMP;
                """,
                (source_id, name, source_type, json.dumps(config), doc_count, status),
            )
            conn.commit()

    def get_source(self, source_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sources WHERE id = ?", (source_id,))
            row = cursor.fetchone()
            if not row:
                return None
            data = dict(row)
            data["config"] = json.loads(data["config"])
            return data

    def list_sources(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sources ORDER BY created_at DESC")
            rows = cursor.fetchall()
            results = []
            for row in rows:
                item = dict(row)
                try:
                    item["config"] = json.loads(item["config"])
                except Exception:
                    item["config"] = {}
                results.append(item)
            return results

    def delete_source(self, source_id: str) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sources WHERE id = ?", (source_id,))
            conn.commit()
            return cursor.rowcount > 0

    # --- Eval Log Operations ---
    def log_eval(
        self,
        query: str,
        strategy: str,
        answer: str,
        faithfulness: Optional[float] = None,
        relevance: Optional[float] = None,
        latency_ms: float = 0.0,
        tokens_used: int = 0,
        cost_usd: float = 0.0,
        sources: Optional[List[Dict[str, Any]]] = None,
    ) -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO eval_logs (
                    query, strategy, answer, faithfulness, relevance,
                    latency_ms, tokens_used, cost_usd, sources
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    query,
                    strategy,
                    answer,
                    faithfulness,
                    relevance,
                    latency_ms,
                    tokens_used,
                    cost_usd,
                    json.dumps(sources or []),
                ),
            )
            conn.commit()
            return cursor.lastrowid

    def get_recent_evals(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM eval_logs ORDER BY id DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            logs = []
            for row in rows:
                item = dict(row)
                try:
                    item["sources"] = json.loads(item["sources"])
                except Exception:
                    item["sources"] = []
                logs.append(item)
            return logs

    def get_eval_summary(self) -> Dict[str, Any]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT
                    COUNT(*) as total_queries,
                    AVG(faithfulness) as avg_faithfulness,
                    AVG(relevance) as avg_relevance,
                    AVG(latency_ms) as avg_latency_ms,
                    SUM(tokens_used) as total_tokens,
                    SUM(cost_usd) as total_cost_usd
                FROM eval_logs
                """
            )
            row = cursor.fetchone()
            if not row:
                return {
                    "total_queries": 0,
                    "avg_faithfulness": 0.0,
                    "avg_relevance": 0.0,
                    "avg_latency_ms": 0.0,
                    "total_tokens": 0,
                    "total_cost_usd": 0.0,
                }
            return {
                "total_queries": row["total_queries"] or 0,
                "avg_faithfulness": round(row["avg_faithfulness"] or 0.0, 3),
                "avg_relevance": round(row["avg_relevance"] or 0.0, 3),
                "avg_latency_ms": round(row["avg_latency_ms"] or 0.0, 1),
                "total_tokens": row["total_tokens"] or 0,
                "total_cost_usd": round(row["total_cost_usd"] or 0.0, 6),
            }


_db_instance: Optional[Database] = None


def get_db() -> Database:
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance
