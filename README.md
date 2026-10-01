# Local MySQL RAG Agent with Groq (Qwen) & Redis

An intelligent SQL Agent using LangChain, Groq's high-speed inference, Redis caching, FAISS RAG for few-shot prompt injection, and LangSmith for real-time observability.

## Prerequisites
- Local MySQL instance running on port 3306.
- Local Redis instance running on port 6379 (`redis-server`).
- Groq Cloud API Key.
- LangSmith API Key.

## Setup Instructions

1. **Create and activate the virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate