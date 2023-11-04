import openai
import streamlit as st
from router.main import SnowDepthQuestion, get_response

# Set Script
st.title("💬 AskBackcountry")
st.caption("🚀 A  chatbot powered by Nature")
st.write(st.session_state)


def clear_chat_history():
    st.session_state.messages = [{"role": "assistant", "content": "How may I assist you today?"}]


st.sidebar.button('Clear Chat History', on_click=clear_chat_history)

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# Get user input
query = st.chat_input("Your Question Here")

if query:
    st.session_state.messages.append({"role": "user", "content": query})
    st.chat_message('user').write(query)

    with st.spinner(":brain: Thinking..."):
        user_question = SnowDepthQuestion()
        sql_query = user_question.get_query(query)
        #st.chat_message('assistant').write(sql_query)
        result = user_question.run_bigquery_query(sql_query)
        st.write(result)
        st.write(":white_check_mark: Data Found")

        if result is not None and len(result) > 0:
            st.write(":chart_with_upwards_trend: Analyzing")
            msg = get_response(data=[result, sql_query], question=query)
            st.session_state.messages.append({"role": "assistant", "content": msg})
            st.chat_message('assistant').write(msg)

        else:
            msg = ('Sorry, I could not find any results for your query.'
                   'I can be picky. Try to be more specific.')
            st.session_state.messages.append({"role": "assistant", "content": msg})
            st.chat_message('assistant').write(msg)

