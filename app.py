import streamlit as st
from helpers.UserQuestion import UserQuestion, response, snow_depth_sql, method_selector, query_bq_data, clear_chat_history, location_extraction


################### SET UI COMPONENTS ###################

st.title("💬 AskBackcountry")
st.caption("🚀 An Adventure Planning Companion")
st.write(st.session_state)

st.sidebar.button('Clear Chat History', on_click=clear_chat_history)

################## INITIALIZE SESSION STATE ##################

if "sql" not in st.session_state:
    st.session_state['sql'] = [{"question": None, "sql_query": None}]

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Lets plan an adventure!"}]

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


################## RUN APP ##################


# Get user input
query = st.chat_input("How much snow is at Berthoud Pass?")

if query:

    st.session_state.messages.append({"role": "user", "content": query})
    st.chat_message('user').write(query)

    with st.spinner(":brain: Thinking..."):
        user_question = UserQuestion(query)
        user_question.method = method_selector(query)  # Collect data for the user question
        user_question.location = location_extraction(query)  # Extract location from user question
        query = query + ' Additional context:' + user_question.location

        ######## COLLECT THE CORRECT DATA ########

        if user_question.method == 'snow_depth_data':
            user_question.sql = snow_depth_sql(query)
            user_question.data = query_bq_data(user_question.sql)

        st.session_state.sql.append({"question": query, "sql_query": user_question.sql})
        result = user_question.data
        st.write(result)

        if result is not None and len(result) > 0:
            #st.write(":white_check_mark: Data Found")
            response = response([result], query)
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.chat_message('assistant').write(response)

        else:
            msg = ('Sorry, I could not find any results for your query.'
                   'I can be picky. Try to be more specific.')
            st.session_state.messages.append({"role": "assistant", "content": msg})
            st.chat_message('assistant').write(msg)

