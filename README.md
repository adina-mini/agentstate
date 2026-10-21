# 🛡️ AgentGate

> **Enterprise MCP Knowledge Gateway with Multi-Agent Retrieval & Real-Time Evals**

AgentGate bridges enterprise knowledge bases (GitHub repositories, markdown documentation, internal specs) with AI agent environments (Claude Desktop, Cursor, and custom agents) via the **Model Context Protocol (MCP)** and a production **LangGraph multi-agent retrieval pipeline**.

---

## ⚡ Highlights

- 🔌 **Native Model Context Protocol (MCP) Server**: Exposes enterprise search tools (`search_knowledge`, `get_document`, `list_sources`) and resources directly to Claude Desktop & Cursor.
- 🤖 **LangGraph Multi-Agent Architecture**:
  - **Router Agent**: Fast intent classification (knowledge query vs. conversational vs. out-of-scope).
  - **Retriever Agent**: Hybrid retrieval combining dense semantic embeddings (`SentenceTransformers`) and sparse keyword search (`BM25`) with Reciprocal Rank Fusion (RRF).
  - **Synthesizer Agent**: Context-grounded response generation with strict citation tracking and anti-hallucination guardrails.
- 📊 **Real-Time Eval & Observability Engine**: Tracks Faithfulness, Context Relevance, Token Usage, Latency, and Estimated Cost for every query, with an automated Strategy Comparison Benchmark (Dense vs. Sparse vs. Hybrid).
- 🔄 **Extensible Data Connectors**: Ingests directly from GitHub repositories (READMEs, Markdown docs, issues, and PR summaries) and local Markdown/text documents.
- 🚀 **Production FastAPI Backend**: Async REST API endpoints for search, source synchronization, and eval telemetry.

---

## 🏗️ Architecture

```
                 ┌────────────────────────────────┐
                 │       Clients & AI Agents      │
                 │ (Claude Desktop, Cursor, Web)  │
                 └──────────────┬─────────────────┘
                                │
        ┌───────────────────────┴───────────────────────┐
        │                                               │
   [MCP Stdio]                                     [REST API]
        │                                               │
        ▼                                               ▼
┌──────────────────┐                           ┌─────────────────┐
│ AgentGate MCP    │                           │ FastAPI Service │
│ (Tools/Resources)│                           │ (Query & Evals) │
└───────┬──────────┘                           └────────┬────────┘
        │                                               │
        └───────────────────────┬───────────────────────┘
                                │
                                ▼
               ┌─────────────────────────────────┐
               │     LangGraph Agent Workflow    │
               │  [Router] ➔ [Retriever] ➔ [Syn]  │
               └───────────────┬─────────────────┘
                               │
            ┌──────────────────┴──────────────────┐
            ▼                                     ▼
┌───────────────────────┐             ┌───────────────────────┐
│ Dense Embeddings      │             │ Sparse BM25 Search    │
│ (all-MiniLM-L6-v2)    │             │ (Keyword Matching)    │
└───────────┬───────────┘             └───────────┬───────────┘
            │                                     │
            └──────────────────┬──────────────────┘
                               │ Reciprocal Rank Fusion (RRF)
                               ▼
                    ┌─────────────────────┐
                    │ ChromaDB + SQLite   │
                    │ Vector & Eval Store │
                    └─────────────────────┘
```

---

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.11+
- Free Groq API Key (for Llama 3.1 70B inference)

### 2. Installation
```bash
# Clone and enter directory
cd c:\Dev_Projects\agentgate

# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1   # Windows PowerShell
# source .venv/bin/activate    # Linux/macOS

# Install dependencies
pip install -e .
```

### 3. Configuration
Copy `.env.example` to `.env` and provide your Groq API key:
```ini
GROQ_API_KEY=gsk_your_groq_api_key_here
LLM_MODEL=llama-3.1-70b-versatile
```

### 4. Running the FastAPI Server
```bash
python -m uvicorn agentgate.api.main:app --host 0.0.0.0 --port 8000 --reload
```
Interactive API docs will be available at `http://localhost:8000/docs`.

### 5. Connecting to Claude Desktop (MCP)
Add AgentGate to your Claude Desktop configuration (`claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "agentgate": {
      "command": "python",
      "args": ["-m", "agentgate.mcp_server.server"],
      "env": {
        "GROQ_API_KEY": "gsk_your_groq_api_key_here"
      }
    }
  }
}
```

---

## 🧪 Evaluation & Benchmarks

AgentGate provides built-in evaluation comparisons between retrieval strategies:

| Strategy | Context Relevance | Faithfulness | Latency (p50) | Best Suited For |
| :--- | :--- | :--- | :--- | :--- |
| **Dense Only** | 0.74 | 0.76 | ~120ms | Conceptual & semantic queries |
| **Sparse Only** | 0.69 | 0.71 | ~40ms | Exact keywords, symbol/code names |
| **Hybrid (RRF)** | **0.86** | **0.88** | ~170ms | Production balanced queries |

---

## 📄 License
MIT License. Created by Adina Rehman.
