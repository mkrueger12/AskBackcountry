import openai
import streamlit as st
from router.main import SnowDepthQuestion, get_response

# Set Script
st.title("💬 AskBackcountry")
st.caption("🚀 A  chatbot powered by OpenAI LLM")


if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "Ready to explore the outdoors? What can I help you with today?"}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# Get user input
    query = st.chat_input("Your Question Here")
    if query:
        user_question = SnowDepthQuestion()
        sql_query = user_question.get_query(query)
        result = user_question.run_bigquery_query(sql_query)
        st.chat_message('assistant').write(get_response(data=[result, sql_query], question=query))

