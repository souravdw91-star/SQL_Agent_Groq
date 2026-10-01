# SQLAgent

A MySQL natural-language SQL assistant built with LangChain, Google Gemini, and LangSmith. The application converts plain-English database questions into safe read-only SQL queries, executes them against a MySQL database, and returns the result in a user-friendly format.

This project is designed for query exploration and reporting use cases where users want to ask business questions without writing SQL themselves.

## Overview

The agent works in the following flow:

1. A user enters a natural-language question in the CLI or Streamlit app.
2. The LangChain SQL toolkit inspects the connected MySQL schema.
3. A Gemini model generates a MySQL query based on the schema and the prompt instructions.
4. The query is executed against the database through LangChain tools.
5. The result is summarized and returned to the user.

The application is intentionally restricted to read-only queries. It avoids destructive operations like `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, and `TRUNCATE` by using the agent prompt and SQL tool behavior.

---

## Features

- Natural-language-to-SQL conversion using Gemini
- MySQL database connectivity through LangChain SQL tooling
- Safe read-only execution guardrails
- CLI experience via `app.py`
- Web interface via `streamlit_app.py`
- LangSmith tracing for agent reasoning and query execution
- Environment-based configuration using `.env`

---

## Project Structure

```text
SQLAgent/
├── app.py                     # Terminal-based chat interface
├── streamlit_app.py           # Streamlit web interface
├── README.md                 # Project documentation
├── requirements.txt          # Python dependencies
├── .env.example              # Optional example environment file
├── config/
│   ├── __init__.py
│   └── settings.py           # App configuration and database settings
├── src/
│   ├── __init__.py
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── builder.py        # Builds the SQL agent executor
│   │   └── toolkit.py       # Creates LangChain SQL toolkit
│   ├── db/
│   │   ├── __init__.py
│   │   └── connection.py    # MySQL connection setup
│   ├── prompts/
│   │   ├── __init__.py
│   │   └── system_prompts.py # Agent instructions and SQL constraints
│   └── utils/
│       ├── __init__.py
│       └── parser.py        # Output cleanup/formatting helper
└── .env                      # Local environment variables (not committed)
```

---

## Tech Stack

- Python 3.10+
- LangChain
- LangChain Community SQL toolkit
- Google Gemini via `langchain-google-genai`
- MySQL via `pymysql`
- Streamlit for the web UI
- LangSmith for tracing and observability
- Python-dotenv for environment loading

---

## Environment Setup

### 1. Clone the repository

```bash
git clone <repository-url>
cd SQLAgent
```

### 2. Create and activate a virtual environment

On macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

On Windows:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root with the required values:

```env
GOOGLE_API_KEY=your_google_api_key
GEMINI_MODEL=gemini-2.5-flash

LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_api_key
LANGCHAIN_PROJECT=mysql-gemini-agent

DB_USER=root
DB_PASSWORD=your_mysql_password
DB_HOST=localhost
DB_PORT=3306
DB_NAME=your_database_name
```

The app reads these values automatically through the settings layer in `config/settings.py`.

> If `LANGCHAIN_API_KEY` is not set, LangSmith tracing will remain disabled and the app will still run without it.

---

## Database Requirements

This project expects an accessible MySQL instance with a schema that matches the questions you want to ask. The agent reads database metadata and generates SQL based on the available tables and columns.

For best results:

- Use descriptive table and column names
- Avoid overly large schemas without narrowing relevant tables
- Keep the database read-only for experimentation
- Prefer adding indexes for large reporting tables

---

## Running the Application

### CLI mode

Run the terminal interface:

```bash
python app.py
```

This starts a prompt loop where you can ask questions such as:

```text
Which 5 customers placed the most orders last month?
Show total sales by product category.
List the top 10 employees by revenue.
```

### Streamlit app

Run the web interface:

```bash
streamlit run streamlit_app.py
```

Then open the local Streamlit URL in your browser and start asking database questions.

---

## Architecture

### Configuration layer

The project centralizes environment configuration in `config/settings.py`.

Key responsibilities:

- reading `.env` values
- exposing the MySQL connection URI
- validating required secrets
- controlling LangSmith tracing settings

### Database layer

The connection logic in `src/db/connection.py` creates a LangChain `SQLDatabase` object using the configured connection string.

This layer handles:

- database URI creation
- table inclusion/exclusion settings
- sample row metadata for schema introspection

### Agent layer

The agent is built in `src/agent/builder.py`.

It performs the following steps:

- validates configuration
- initializes the Gemini LLM
- creates the SQL toolkit
- constructs the LangChain SQL agent with `tool-calling` mode
- attaches prompt instructions for safe query behavior

### Prompt layer

The custom instructions in `src/prompts/system_prompts.py` define the main behavior of the agent:

- limit answers to a useful number of rows
- prefer relevant columns only
- order results meaningfully
- never issue destructive statements
- re-check query syntax on failure

### Utility layer

The parser helper in `src/utils/parser.py` cleans structured model output into plain text so it renders properly in the terminal and Streamlit UI.

---

## Safety Rules

This project is designed for safe read-only database interaction. The system instructions explicitly prohibit:

- `INSERT`
- `UPDATE`
- `DELETE`
- `DROP`
- `ALTER`
- `TRUNCATE`

The intent is to support analytics and reporting workflows while reducing the risk of accidental data modification.

---

## Example Use Cases

- Business reporting dashboards via natural language
- Quick data exploration for product, sales, and customer analytics
- Internal SQL assistance for non-technical users
- Database schema analysis without writing raw SQL manually

---

## Troubleshooting

### Missing API key

If Gemini initialization fails, check that `GOOGLE_API_KEY` is present in your `.env` file.

### Database connection issues

Verify:

- MySQL is running
- the database credentials are correct
- the `DB_HOST`, `DB_PORT`, and `DB_NAME` values are accurate
- the database user has permission to read the target schema

### LangSmith not tracing

This is often caused by a missing `LANGCHAIN_API_KEY`. If tracing is enabled but no key is provided, the app still works but tracing will not be recorded.

### Query errors

The agent is configured to retry failed queries when possible, but some questions may still be outside the available schema or require a more specific prompt.

---

## Notes

This is a lightweight but practical SQL agent project for learning and experimentation. It demonstrates how to combine:

- schema-aware SQL tooling
- LLM-based query generation
- secured read-only operations
- instrumentation with LangSmith
- a terminal + web interface

If you are extending this project, you can add features such as:

- role-based permissions
- query result formatting improvements
- table-level access control
- a richer dashboard UI
- support for more database backends

---

## License

This project is intended for educational and internal use unless otherwise specified by the repository owner.
