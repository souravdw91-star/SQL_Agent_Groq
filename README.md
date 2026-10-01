# Local MySQL RAG Agent with Groq Cloud & Redis

A local, practical SQL copilot built to let a user ask natural-language questions about a MySQL database and get relevant answers through a Streamlit chat interface. The system uses Groq Cloud LLMs through LangChain, Redis caching, FAISS-based example retrieval, and schema introspection to generate and answer database queries without requiring the user to write SQL manually.

This project is useful for prototyping business intelligence, data exploration, and lightweight database assistants in a local environment.

## Why this project exists

Many teams need a quick way to query structured data without relying on a full BI stack or writing SQL by hand. This project demonstrates a simple architecture for:

- asking questions in plain English
- translating them into MySQL queries
- inspecting the schema before generating a query
- serving cached answers quickly for repeated questions
- monitoring the agent with LangSmith tracing

It is intentionally designed for local development and experimentation.

## Core features

- Natural-language to SQL conversion for MySQL
- Automatic schema inspection before query generation
- Redis-based caching for both schema metadata and final answers
- FAISS-based retrieval of few-shot SQL examples
- Groq Cloud LLM access via any supported model
- Streamlit-based UI for direct user interaction
- Sidebar diagnostics for Redis and database status
- Cache reset option from the UI
- Guardrails to prevent destructive SQL actions

## Architecture overview

The application is split into three main layers:

1. Frontend interface: `streamlit_app.py`
2. Backend logic: `backend/app.py`
3. Model validation helper: `backend/check_models.py`

The runtime flow is:

1. Streamlit starts the backend.
2. The backend connects to MySQL and Redis.
3. The database schema is fetched once and cached in Redis.
4. The user enters a natural-language question in the chat UI.
5. The agent checks Redis for a cached answer.
6. If no cached result exists, it builds a LangChain SQL agent and calls Groq with the schema context.
7. The model returns a SQL query and/or a final natural-language answer.
8. The result is cached and shown in the UI.

A simplified flow looks like this:

```text
User question
    ↓
Streamlit UI
    ↓
SQLAgentBackend.query()
    ├─ Check Redis cache
    ├─ If miss: invoke LangChain SQL agent
    │      ├─ Load MySQL schema
    │      ├─ Retrieve few-shot examples from FAISS
    │      └─ Query Groq Cloud model
    └─ Cache final answer in Redis
    ↓
Response shown in chat
```

## Tech stack

- Python 3.10+
- Streamlit
- LangChain
- LangChain Community
- LangChain Groq
- LangChain HuggingFace embeddings
- FAISS
- Redis
- MySQL + PyMySQL
- Sentence Transformers
- Groq Cloud API
- LangSmith (optional tracing)

## Project structure

```text
SQL_Agent_Groq/
├── README.md
├── requirements.txt
├── streamlit_app.py
├── backend/
│   ├── app.py
│   └── check_models.py
├── .env                # local environment variables (not committed)
├── .venv/              # local virtual environment (optional)
└── .gitignore          # project ignore rules
```

## Prerequisites

Before running the project, make sure your environment includes:

- Python 3.10 or newer
- A MySQL server running locally
- Redis installed and running locally
- A valid Groq API key
- Optional: a LangSmith API key for tracing
- A MySQL database with tables and data relevant to your use case

## Installation

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd SQL_Agent_Groq
```

### 2. Create a virtual environment

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

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

This installs the main app requirements, including the LangChain stack, Groq connector, Redis library, MySQL connector, FAISS, and embeddings tooling.

### 4. Configure environment variables

Create a `.env` file in the project root with values similar to the following:

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
GROQ_MODEL=llama-3.1-8b-instant

# Optional LangSmith tracing
LANGSMITH_API_KEY=your_langsmith_api_key
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=sql-agent-groq
```

### 5. Validate database and Redis availability

Confirm the following are true before launching the app:

- MySQL is running on `localhost:3306`
- Redis is running on `localhost:6379`
- You can connect to your database with the configured username/password
- Your database contains tables the model can inspect

## Starting required services

### MySQL

If MySQL is installed locally, make sure it is running. Common examples:

Windows:

```powershell
net start MySQL80
```

If your setup uses a different service name or a local MySQL installation directory, start it using the appropriate method for your machine.

### Redis

Start Redis on the default port:

```bash
redis-server
```

If you are on Windows and Redis was installed as a Windows service or via a zip, use the startup command or service manager appropriate for that installation.

## Verifying Groq access

Before launching the app, confirm that your Groq API key is valid and the model is accessible:

```bash
python backend/check_models.py
```

This script calls the Groq models endpoint and lists available model IDs on your API key. If you see errors, check your API key and network access.

## Running the application

Start the Streamlit app:

```bash
streamlit run streamlit_app.py
```

Then open the browser URL shown in the terminal, typically:

```text
http://localhost:8501
```

## Example queries

The app works best with clear natural-language prompts that match the actual schema of the database. Good examples include:

- Show total sales by customer
- Which products generated the most revenue last month?
- Find users with no orders
- List active customers created this year
- What is the average order value by region?
- Show the top 10 products by quantity sold

The SQL agent is designed to inspect the schema first, so the quality of the schema matters a lot. Clear table names and sensible column names make a big difference.

## How the backend works

The main logic is in `backend/app.py`.

### 1. MySQL connection

The app creates a database connection using SQLAlchemy and LangChain's `SQLDatabase` wrapper:

```python
self.db = SQLDatabase.from_uri(uri)
```

This gives the model access to the database schema and query execution capabilities.

### 2. Schema caching in Redis

The project stores schema metadata in Redis to avoid repeatedly introspecting the database:

```python
self.schema_cache_key = f"db_schema:{db_name}"
```

The caching function tries to load the schema from Redis and creates it if missing.

This is useful because schema introspection can be repetitive and expensive in data-heavy systems.

### 3. Groq model initialization

The app initializes the LLM with Groq using the configured model:

```python
self.llm = ChatGroq(
    model=model_name,
    temperature=0,
    groq_api_key=os.getenv("GROQ_API_KEY")
)
```

The default is intentionally configurable and can be set to any Groq-supported model, for example:

```text
llama-3.1-8b-instant
```

### 4. Few-shot example retrieval with FAISS

The backend builds a small vector-based example selector using HuggingFace embeddings and FAISS:

- natural-language prompts are stored as examples
- matching examples are retrieved based on semantic similarity
- those examples help the model generate more consistent SQL queries

This is a lightweight RAG pattern for few-shot prompting.

### 5. SQL agent creation

The project uses LangChain's SQL agent toolkit:

```python
self.agent = create_sql_agent(
    llm=self.llm,
    db=self.db,
    agent_type="openai-tools",
    verbose=True,
    system_message=system_prefix
)
```

The system prompt explicitly instructs the agent to:

- inspect the schema first
- avoid destructive commands
- explain limitations when the database information is insufficient

### 6. Query result caching

The app also caches final responses by normalized question text:

```python
cache_key = f"query_cache:{user_question.strip().lower()}"
```

If an identical question is asked again, the system can return the cached result without calling the LLM again.

## What the UI does

The Streamlit frontend presents a chat experience and includes several features:

- user message input box
- chat history display
- Redis status checks in the sidebar
- database target info in the sidebar
- a button to clear Redis query cache
- metadata indicating whether output came from Redis or a fresh Groq-generated response

Example UI labels:

- `⚡ Served from Redis Cache`
- `🤖 Generated via Groq Cloud Agent`

## Data flow and behavior

The app is intentionally simple and fast for local use:

- If a query is repeated, Redis may answer immediately.
- If a query is new, the LLM agent runs.
- The model receives schema information and example prompts to guide SQL generation.
- The generated response is returned to the user in natural language.

This makes it easier to prototype data exploration without needing a full production warehouse assistant setup.

## Safety and guardrails

The system includes safeguards to reduce the risk of destructive queries:

- the system message tells the model not to run destructive operations
- blocked SQL actions include:
  - `DROP`
  - `DELETE`
  - `TRUNCATE`
  - `ALTER`

This is not a substitute for database security controls, but it helps reduce accidental misuse during local experimentation.

## Security considerations

Because this project interacts with a live MySQL database, follow these rules:

- use a dedicated database user with limited permissions when possible
- do not commit `.env` files to version control
- keep the API keys and database credentials secure
- prefer read-only access for non-production experiments
- avoid exposing the app publicly without authentication

## Troubleshooting

### Backend fails to initialize

Common reasons include:

- MySQL is down
- Redis is down
- environment variables are missing or invalid
- the Groq API key is invalid
- the database name or port is incorrect

Check the Streamlit error output or run:

```bash
python backend/check_models.py
```

### Redis connection issues

Redis is used for both schema cache and result cache.

If Redis is unavailable:

- the app may still start, but cache behavior will degrade
- repeated questions may require fresh model calls
- no response cache will be stored

### MySQL connection issues

Verify the following:

- host matches the local instance
- port is correct
- user has access to the database
- password is valid
- the target database exists

### Groq access issues

If the model listing script fails, confirm:

- the API key is valid
- the key has access to Groq model endpoints
- outbound internet access is available
- the model ID is correct

### Weak or incorrect responses

If the assistant returns poor SQL or bad answers, review these points:

- the database schema is clear and consistent
- the table and column names are meaningful
- the prompts are specific and concrete
- more example prompts can be added to the few-shot selector in `backend/app.py`
- the user question should map closely to real fields in the database

## Suggested improvements

This project is a strong starting point, and there are many practical enhancements you could add next:

- support for PostgreSQL or SQLite in addition to MySQL
- better schema summarization for large databases
- user authentication for the Streamlit app
- query result downloads as CSV or JSON
- more advanced multi-turn chat memory
- audit logging for generated SQL queries
- improved prompt templates and better database-specific instructions
- support for data visualization of query outputs

## Best practices for using this project

To get the most reliable outputs:

- keep your database schema clean and descriptive
- ask questions that map directly to actual table names and columns
- use a read-only database account for testing
- keep the model configuration stable and documented
- test the system with a small database before scaling up

## Limitations

This project is meant for local experimentation and prototype data access, not for full production-grade enterprise deployment. Current limitations include:

- dependence on local services and credentials
- relatively simple prompt engineering
- no robust authentication layer
- no advanced permissions model
- no full enterprise monitoring or query governance

## License

This project is intended for personal, educational, or internal experimental use unless additional licensing is specified by the repository owner.

## Summary

This project demonstrates a practical local SQL assistant using Groq Cloud models, LangChain, MySQL, Redis, and FAISS. It is a useful example of combining LLM-powered agents with database introspection, caching, and a simple chat interface to enable natural-language querying of structured data.

It is especially well-suited for learning, internal tooling, and lightweight data exploration workflows.
