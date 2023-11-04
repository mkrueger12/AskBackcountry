import openai
import streamlit as st
from router.main import SnowDepthQuestion, get_response

# Set Script
st.title("💬 AskBackcountry")
st.caption("🚀 An Adventure Planning Companion")
#st.write(st.session_state)

# set UI
def clear_chat_history():
    st.session_state.messages = [{"role": "assistant", "content": "Lets plan an adventure!"}]
    st.session_state['sql'] = [{"question": None, "sql_query": None}]


st.sidebar.button('Clear Chat History', on_click=clear_chat_history)

#Set context
if "sql" not in st.session_state:
    st.session_state['sql'] = [{"question": None, "sql_query": None}]

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Lets plan an adventure!"}]

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Get user input
query = st.chat_input("Your Question Here")

if query:
    st.session_state.messages.append({"role": "user", "content": query})
    st.chat_message('user').write(query)

    with st.spinner(":brain: Thinking..."):
        user_question = SnowDepthQuestion()
        sql_query = user_question.get_query(query)
        st.session_state.sql.append({"question": query, "sql_query": sql_query})
        result = user_question.run_bigquery_query(sql_query)
        #st.write(result)

        if result is not None and len(result) > 0:
            st.write(":white_check_mark: Data Found")
            st.write(":chart_with_upwards_trend: Analyzing")
            msg = get_response(data=[result, sql_query], question=query)
            st.session_state.messages.append({"role": "assistant", "content": msg})
            st.chat_message('assistant').write(msg)

        else:
            msg = ('Sorry, I could not find any results for your query.'
                   'I can be picky. Try to be more specific.')
            st.session_state.messages.append({"role": "assistant", "content": msg})
            st.chat_message('assistant').write(msg)

