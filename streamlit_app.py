import streamlit as st
from backend.app import SQLAgentBackend

st.set_page_config(page_title="Qwen SQL Agent", page_icon="⚡", layout="wide")
st.title("⚡ Natural Language SQL Agent")
st.caption("Powered by Groq (Qwen) + LangChain + Redis Caching + LangSmith Tracing")

@st.cache_resource(show_spinner="Initializing Database and Agent...")
def load_backend():
    return SQLAgentBackend()

try:
    backend = load_backend()
except Exception as e:
    st.error(f"Failed to initialize backend. Please check your MySQL, Redis, and Groq settings. Details: {e}")
    st.stop()

# Sidebar diagnostics
with st.sidebar:
    st.subheader("System Status")
    try:
        backend.redis_client.ping()
        st.success("Redis Cache: Connected")
    except Exception:
        st.warning("Redis Cache: Offline (Operating without cache)")
    
    st.info(f"Target DB: `{backend.db._engine.url.database}`")
    
    if st.button("Clear Response Cache"):
        keys = backend.redis_client.keys("query_cache:*")
        if keys:
            backend.redis_client.delete(*keys)
            st.success(f"Cleared {len(keys)} cached entries.")
        else:
            st.info("No query cache to clear.")

# Chat history initialization
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "meta" in msg:
            st.caption(msg["meta"])

user_input = st.chat_input("Ask a question about your database (e.g., 'Show total sales by user')...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Processing schema and executing query..."):
            res = backend.query(user_input)
            response_text = res["result"]
            source = res["source"]

            st.markdown(response_text)
            meta_label = "⚡ Served from Redis Cache" if source == "redis_cache" else "🤖 Generated via Groq Qwen Agent"
            st.caption(meta_label)

            st.session_state.messages.append({
                "role": "assistant",
                "content": response_text,
                "meta": meta_label
            })