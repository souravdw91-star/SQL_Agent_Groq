import os
import json
import redis
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.example_selectors import SemanticSimilarityExampleSelector
from langchain_core.prompts import (
    ChatPromptTemplate,
    FewShotChatMessagePromptTemplate,
)

load_dotenv()

class SQLAgentBackend:
    def __init__(self):
        # 1. Connect Redis
        self.redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            db=int(os.getenv("REDIS_DB", 0)),
            decode_responses=True
        )
        self.redis_ttl = int(os.getenv("REDIS_TTL_SECONDS", 3600))

        # 2. Connect MySQL
        user = os.getenv("MYSQL_USER")
        password = os.getenv("MYSQL_PASSWORD")
        host = os.getenv("MYSQL_HOST")
        port = os.getenv("MYSQL_PORT")
        db_name = os.getenv("MYSQL_DB")
        uri = f"mysql+pymysql://{user}:{password}@{host}:{port}/{db_name}"
        self.db = SQLDatabase.from_uri(uri)

        # 3. Cache Schema in Redis
        self.schema_cache_key = f"db_schema:{db_name}"
        self._ensure_schema_cached()

        # 4. Initialize Groq LLM (Qwen)
        model_name = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
        self.llm = ChatGroq(
            model=model_name,
            temperature=0,
            groq_api_key=os.getenv("GROQ_API_KEY")
        )

        # 5. Build RAG Example Selector
        self.example_prompt = self._build_rag_examples()

        # 6. Assemble SQL Agent
        system_prefix = """You are a careful MySQL data analyst.
Always inspect the provided schema before generating queries.
Never perform destructive actions like DROP, DELETE, TRUNCATE, or ALTER.
If the requested information cannot be deduced from the retrieved schema, explain the limitation clearly.
"""
        self.agent = create_sql_agent(
            llm=self.llm,
            db=self.db,
            agent_type="openai-tools",
            verbose=True,
            system_message=system_prefix
        )

    def _ensure_schema_cached(self):
        """Stores the database schema DDL into Redis to prevent redundant introspections."""
        try:
            cached = self.redis_client.get(self.schema_cache_key)
            if not cached:
                schema_info = self.db.get_table_info()
                self.redis_client.setex(self.schema_cache_key, self.redis_ttl, schema_info)
        except redis.ConnectionError:
            # Fall back safely if Redis is down
            pass

    def _build_rag_examples(self):
        """Indexes few-shot query patterns into a local vector store for query accuracy."""
        examples = [
            {
                "input": "How many total users signed up this month?",
                "query": "SELECT COUNT(*) FROM users WHERE created_at >= DATE_FORMAT(NOW(), '%Y-%m-01');"
            },
            {
                "input": "Show top 5 products by total sales amount",
                "query": "SELECT p.name, SUM(oi.price * oi.quantity) AS total_revenue FROM order_items oi JOIN products p ON oi.product_id = p.id GROUP BY p.id ORDER BY total_revenue DESC LIMIT 5;"
            },
            {
                "input": "Find active customers with no purchases",
                "query": "SELECT c.id, c.name FROM customers c LEFT JOIN orders o ON c.id = o.customer_id WHERE c.status = 'active' AND o.id IS NULL;"
            }
        ]

        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        example_selector = SemanticSimilarityExampleSelector.from_examples(
            examples,
            embeddings,
            FAISS,
            k=2
        )

        example_template = ChatPromptTemplate.from_messages([
            ("human", "{input}"),
            ("ai", "{query}")
        ])

        return FewShotChatMessagePromptTemplate(
            example_prompt=example_template,
            example_selector=example_selector,
            input_variables=["input"]
        )

    def query(self, user_question: str) -> dict:
        """Checks query response cache in Redis; if missed, executes agent and caches output."""
        cache_key = f"query_cache:{user_question.strip().lower()}"

        try:
            cached_result = self.redis_client.get(cache_key)
            if cached_result:
                return {"result": json.loads(cached_result), "source": "redis_cache"}
        except redis.ConnectionError:
            pass

        # Run SQL Agent (Traced to LangSmith automatically)
        agent_output = self.agent.invoke({"input": user_question})
        final_answer = agent_output.get("output", "No response generated.")

        # Cache final response for 1 hour
        try:
            self.redis_client.setex(cache_key, self.redis_ttl, json.dumps(final_answer))
        except redis.ConnectionError:
            pass

        return {"result": final_answer, "source": "llm_agent"}