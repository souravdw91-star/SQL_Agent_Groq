# Local MySQL RAG Agent with Groq (Qwen) & Redis

A lightweight, local-first SQL assistant that lets you ask natural-language questions about a MySQL database and receive SQL-backed answers through a Streamlit chat UI. The project combines:

- Groq-hosted LLM inference with Qwen
- LangChain SQL agent tooling
- Redis schema/query caching
- FAISS-based few-shot example retrieval for query patterns
- MySQL schema introspection
- LangSmith tracing support for observability

This is a practical starter for building query copilots that answer business questions from a local database without writing SQL manually.

## Features

- Natural-language querying of a local MySQL database
- Automatic schema inspection before SQL generation
- Query result caching in Redis to reduce repeated latency
- Schema caching to avoid re-reading database metadata repeatedly
- Few-shot RAG examples for more consistent query generation
- Streamlit-based chat experience
- Built-in status checks and cache reset controls in the UI
- Guardrails to avoid destructive SQL operations

## Architecture Overview

The application is split into two main pieces:

- `streamlit_app.py` — the user-facing chat interface
- `backend/app.py` — the SQL agent backend, database connection, schema caching, and Groq integration

The flow is:

1. The Streamlit app starts the backend.
2. The backend connects to MySQL and Redis.
3. It caches the database schema in Redis.
4. A Qwen model through Groq is used to generate SQL from a natural-language prompt.
5. The generated SQL is executed against MySQL.
6. The final answer is returned to the UI and cached in Redis for repeat queries.

## Tech Stack

- Python 3.10+
- Streamlit
- LangChain
- LangChain Community
- LangChain Groq
- LangChain HuggingFace embeddings
- Redis
- MySQL / PyMySQL
- FAISS
- Sentence Transformers
- Groq API

## Project Structure

```text
SQL_Agent_Groq/
├── README.md
├── requirements.txt
├── streamlit_app.py
├── backend/
│   ├── app.py
│   └── check_models.py
├── .env.example (optional, user-created)
└── .venv/ (local virtual environment, if created)
```

## Prerequisites

Before starting, ensure you have:

- Python 3.10 or newer installed
- A local MySQL server running on port 3306
- A local Redis server running on port 6379
- A Groq API key
- Optional: a LangSmith API key for tracing and monitoring
- A MySQL database with tables you want to query

## Installation

1. Clone the repository:

   ```bash
   git clone <your-repo-url>
   cd SQL_Agent_Groq
   ```

2. Create and activate a virtual environment:

   On macOS/Linux:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

   On Windows PowerShell:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root with the required environment variables:

   ```env
   MYSQL_HOST=localhost
   MYSQL_PORT=3306
   MYSQL_USER=root
   MYSQL_PASSWORD=your_mysql_password
   MYSQL_DB=your_database_name

   REDIS_HOST=localhost
   REDIS_PORT=6379
   REDIS_DB=0
   REDIS_TTL_SECONDS=3600

   GROQ_API_KEY=your_groq_api_key
   GROQ_MODEL=qwen/qwen3.8-27b

   # Optional LangSmith tracing configuration
   LANGSMITH_API_KEY=your_langsmith_api_key
   LANGCHAIN_TRACING_V2=true
   LANGCHAIN_PROJECT=sql-agent-groq
   ```

5. Make sure your local MySQL database is reachable and contains the tables you want to query.

## Starting Required Services

### MySQL

Ensure MySQL is installed and running locally. If you need to start it manually, the exact command depends on your setup, but common examples are:

- Windows services:

  ```powershell
  net start MySQL80
  ```

- Or start the MySQL server from your installation directory using your preferred method.

### Redis

Redis should be running on `localhost:6379`.

Common command:

```bash
redis-server
```

On Windows, if Redis is installed as a service or via a local binary, use the corresponding startup command for your setup.

## Verifying the Groq Model Access

The project includes a helper script to check whether your Groq key can access the Groq model API:

```bash
python backend/check_models.py
```

This script lists the available Groq models on your key and is useful for confirming API access before running the app.

## Running the App

Start the Streamlit app:

```bash
streamlit run streamlit_app.py
```

Then open the local URL shown in the terminal, typically:

```text
http://localhost:8501
```

## Example Questions

Try prompts like:

- Show me the total number of orders placed this month.
- Which customers have spent the most money?
- List the top 10 products by revenue.
- Find users with no orders yet.
- Show sales by region for the last 30 days.

The agent inspects the schema first and then generates MySQL queries accordingly.

## How the Backend Works

The main backend logic lives in `backend/app.py` and performs the following:

### 1. Database connection

A MySQL connection is created using SQLAlchemy via:

```python
SQLDatabase.from_uri(uri)
```

### 2. Schema caching

The DB schema is stored in Redis under a key like:

```text
db_schema:<database_name>
```

This avoids repeatedly fetching metadata from MySQL and reduces latency.

### 3. LLM setup

The app uses:

```python
ChatGroq(model=os.getenv("GROQ_MODEL", "qwen/qwen3.6-27b"))
```

This gives the SQL agent access to a Groq-hosted model for SQL generation.

### 4. Few-shot prompt augmentation

The app builds a local FAISS vector store with example natural-language prompts and SQL outputs. Those examples are used as retrieval-based few-shot prompts to improve query quality.

### 5. Agent execution

The SQL agent is assembled with LangChain and runs against the connected database using a read-safe system prompt.

### 6. Result caching

After a user asks a question, the final answer is cached in Redis using a prompt-based key:

```text
query_cache:<normalized_question>
```

This means repeated asks for the same question can be served faster from Redis instead of calling the model again.

## UI Behavior

The Streamlit UI includes:

- A conversational chat interface
- Red/green status indicators for Redis connectivity
- Database metadata display in the sidebar
- A button to clear the query cache
- Labels showing whether a response came from Redis or the Groq-generated path

## Security Notes

This project is designed for local experimentation and internal use. To keep it safe:

- Use a dedicated MySQL user with read-only access when possible
- Avoid storing sensitive database credentials in source control
- Keep the `.env` file local and out of version control
- The agent explicitly protects against destructive SQL commands such as `DROP`, `DELETE`, `TRUNCATE`, and `ALTER`

## Troubleshooting

### Backend fails to initialize

Common causes:

- MySQL is not running
- Redis is not running
- `.env` values are missing or incorrect
- Groq API key is invalid or missing

Check the app error message and verify each connection in the `.env` file.

### Redis errors

If Redis is down, the app can still start in a degraded mode, but caching won't work reliably. Start Redis and verify connectivity before querying heavily.

### MySQL connection issues

Verify:

- host, port, user, password, and database name are correct
- the database exists
- the MySQL user has access to it

### Groq API access problems

Run:

```bash
python backend/check_models.py
```

If the script fails, confirm the `GROQ_API_KEY` is valid and the model ID is accessible on your account.

### Prompt results look weak or invalid

Improve the database schema quality, ensure your tables and column names are clear, and consider adding more example prompts to the few-shot vector store in `backend/app.py`.

## Recommended Next Improvements

- Add database-specific schema metadata for better SQL generation
- Support more SQL dialects or database backends
- Add user authentication for the Streamlit app
- Add query logging and audit trails
- Add support for multi-turn conversational context
- Add downloadable CSV exports for query results

## License

This project is intended for personal or internal educational use unless another license is specified by the repository owner.

## Summary

This project is a solid local SQL agent starter that demonstrates how to combine LLMs, database introspection, retrieval-augmented prompting, and caching into a useful natural-language query interface. It is especially useful for exploring structured data with low friction and fast iteration.
