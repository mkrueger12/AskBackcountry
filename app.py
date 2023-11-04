import openai
import streamlit as st
from router.main import SnowDepthQuestion, get_response

# Set Script
st.title("💬 AskBackcountry")
st.caption("🚀 A  chatbot powered by Nature")


if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "Ready to explore the outdoors? What can I help you with today?"}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

    # Get user input
    query = st.chat_input("Your Question Here")
    st.chat_message('user').write(query)
    if query:
        with st.status(":rocket: Lets Take A Look!", expanded=True):
            user_question = SnowDepthQuestion()
            sql_query = user_question.get_query(query)
            st.chat_message('assistant').write(sql_query)
            st.write("Downloading data...Almost there!")
            result = user_question.run_bigquery_query(sql_query)
            st.write("Data Found :white_check_mark:")

            if len(result) > 0:
                st.chat_message('assistant').write(get_response(data=[result, sql_query], question=query))

            else:
                st.chat_message('assistant').write('Sorry, I could not find any results for your query.'
                                                   'I can be picky. Try to be more specific.')

