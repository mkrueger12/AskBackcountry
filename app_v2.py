import streamlit as st
import json
import dotenv
import openai
import os
import traceback
import logging
from trubrics.integrations.streamlit import FeedbackCollector
from helpers.UserQuestion import UserQuestion, response, snow_depth_sql, method_selector, query_bq_data, clear_chat_history, location_extraction, weather_forecast, upload_blob_from_memory


################### SET LOGGING ###################
# Configure logging
logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


dotenv.load_dotenv('.env')


openai.api_key = os.getenv('OPENAI_KEY')


################### SET UI COMPONENTS ###################
st.warning('This app is still in development. You may see outages or issues. Please be patient and provide your feedback. '
           ' How to Use - There are currently two modules SNOW & WEATHER. SNOW supports questions about the snowpack in Colorado only.'
           ' WEATHER can provide a forecast for any location in the United States. Enjoy!', icon="⚠️")

st.title("💬 AskBackcountry")
st.caption("🚀 An Adventure Planning Companion")

#st.write(st.session_state)

st.sidebar.button('Clear Chat History', on_click=clear_chat_history)

collector = FeedbackCollector(project='default', email='mkrueger190@gmail.com', password='eFAivz%y%rc7n54')


################## INITIALIZE SESSION STATE ##################

if ["sql", "method", "errors"] not in st.session_state:
    st.session_state['sql'] = [{"question": None, "sql_query": None}]
    st.session_state['method'] = [{"question": None, "method": None}]
    st.session_state['error'] = [{"question": None, "error": None, "traceback": None}]
    st.session_state['primary'] = [{"question": None, "response": None, "feedback": None}]
    st.session_state['feedback_submitted_thumbs'] = []

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Lets plan an adventure!"}]

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


################## INIT OpenAI ##################

assistant = openai.beta.assistants.create(
    name="Ask BC",
    instructions="You are a backcountry trip planning assistant. Answer questions provided by the user.",
    tools=tools,
    model="gpt-4-1106-preview"
)

thread = openai.beta.threads.create()


################## RUN APP ##################


# Get user input
query = st.chat_input("How much snow is at Berthoud Pass?")
try:
    if query:

        message = openai.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=query
        )


        logging.info(f"User query: {query}")

        st.session_state.messages.append({"role": "user", "content": query})
        st.chat_message('user').write(query)

        with st.spinner(":brain: Thinking..."):

            user_question = UserQuestion(query)

            run = openai.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=assistant.id,
                instructions="Please answer the users question"
            )

            run = openai.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )

            if run.status == 'requires_action':

                tool = run.required_action.submit_tool_outputs.tool_calls[0].function.name
                args = run.required_action.submit_tool_outputs.tool_calls[0].function.arguements

                st.session_state.method.append({"question": query, "method": tool})

                logging.info(f"Method selected: {tool}")

            user_question.location = json.loads(location_extraction(user_question.question))  # Extract location from user question
            query = (user_question.question + ' Additional context:' + user_question.location['county'] + ' ' + user_question.location['state']
                         + ' Elevation: ' + str(user_question.location['elevation']))


            ######## COLLECT THE CORRECT DATA ########

            if tool == 'snow_depth_data':
                user_question.sql = snow_depth_sql(query)

                logging.info(f"Snow depth SQL query: {user_question.sql}")

                user_question.data = query_bq_data(user_question.sql)

            if user_question.method == 'weather_forecast':
                lat = user_question.location['latitude']
                lon = user_question.location['longitude']
                user_question.data = 'Forecast: ' + str(weather_forecast(lat, lon))

            st.session_state.sql.append({"question": query, "sql_query": user_question.sql})

            upload_blob_from_memory(bucket_name='ask-bc-analytics', contents=json.dumps(st.session_state.sql),
                                        destination_blob_name='sql-queries')
            result = user_question.data
            #st.write(result)

            if result is not None and len(result) > 0:

                response = response([user_question.data], user_question.question)
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.chat_message('assistant').write(response)

                st.button("Good Answer", type="primary", on_click=upload_blob_from_memory,
                          kwargs=dict(bucket_name='ask-bc-analytics', contents=json.dumps({"question": user_question.question, "response": response, "feedback": 'good'}), destination_blob_name='feedback'))

                st.button("Bad Answer", type="primary", on_click=upload_blob_from_memory,
                          kwargs=dict(bucket_name='ask-bc-analytics', contents=json.dumps(
                              {"question": user_question.question, "response": response, "feedback": 'bad'}),
                                      destination_blob_name='feedback'))

            else:
                msg = ('Sorry, I could not find any results for your query.'
                       'I can be picky. Try to be more specific.')
                st.session_state.messages.append({"role": "assistant", "content": msg})
                st.chat_message('assistant').write(msg)

except Exception as e:

    logging.exception("An error occurred:")
    logging.error(f"Error occurred: {str(e)}")
    st.session_state.error.append({"question": user_question.question, "error": str(e), "traceback": traceback.format_exc()})
    upload_blob_from_memory(bucket_name='ask-bc-analytics', contents=json.dumps(st.session_state.error), destination_blob_name='errors')
    st.error('Sorry, something went wrong. Please refresh and try again.', icon="🚨")
