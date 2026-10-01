import streamlit as st
from src.agent.builder import build_sql_agent
from src.utils.parser import extract_clean_text

st.set_page_config(page_title="MySQL Gemini Agent", page_icon="🗄️", layout="wide")

st.title("🗄️ MySQL Database Agent")
st.caption("Powered by Google Gemini, LangChain, and LangSmith Tracing")

# Initialize Agent once in session state
if "agent" not in st.session_state:
    try:
        with st.spinner("Connecting to MySQL and building agent..."):
            st.session_state.agent = build_sql_agent()
    except Exception as e:
        st.error(f"Failed to initialize agent: {e}")
        st.stop()

# Initialize message history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! Ask me any question about the database."}
    ]

# Render chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Process new user prompt
if prompt := st.chat_input("e.g., Which 5 customers placed the most orders last month?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Querying database..."):
            try:
                # Execution with LangSmith auto-tracing
                response = st.session_state.agent.invoke({"input": prompt})
                output_text = extract_clean_text(response.get("output", "No result returned."))
                st.markdown(output_text)
                
                # Append to chat history
                st.session_state.messages.append({"role": "assistant", "content": output_text})
            except Exception as e:
                error_msg = f"⚠️ Error executing query: `{e}`"
                st.markdown(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})