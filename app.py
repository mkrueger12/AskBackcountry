import streamlit as st
import json
import traceback
import logging
from trubrics.integrations.streamlit import FeedbackCollector
from helpers.UserQuestion import UserQuestion, response, snow_depth_sql, method_selector, query_bq_data, clear_chat_history, location_extraction, weather_forecast, upload_blob_from_memory, co_field_obv


################### SET LOGGING ###################
# Configure logging
logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')



################### SET UI COMPONENTS ###################
st.warning('This app is still in development. You may see outages or issues. Please be patient and provide your feedback. '
           ' **How to Use** - There are currently two modules SNOW & WEATHER. '
           '**SNOW** supports questions about the snowpack in the US SNOTEL network and questions about CAIC field observations. '
           ' **WEATHER** can provide a forecast for any location in the United States. '
           'The more specific you can be the better the results. Enjoy!', icon="⚠️")

st.title("💬 AskBackcountry")
st.caption("🚀 An Adventure Planning Companion")

#st.write(st.session_state)

# Using the "with" syntax
with st.sidebar.form(key='my_form'):
    text_input = st.text_input(label='Please Provide Feedback')
    submit_button = st.form_submit_button(label='Submit', on_click=upload_blob_from_memory,
                                        kwargs=dict(bucket_name='ask-bc-analytics', contents=json.dumps({"request": text_input}), destination_blob_name='feature_requests'))


st.sidebar.button('Clear Chat History', on_click=clear_chat_history)

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


################## RUN APP ##################


# Get user input
query = st.chat_input("How much snow is at Berthoud Pass?")
try:
    if query:

        logging.info(f"User query: {query}")

        st.session_state.messages.append({"role": "user", "content": query})
        st.chat_message('user').write(query)

        with st.spinner(":brain: Thinking..."):
            user_question = UserQuestion(query)
            user_question.method, args = method_selector(user_question.question)  # Collect data for the user question
            st.session_state.method.append({"question": query, "method": user_question.method})

            logging.info(f"Method selected: {user_question.method}")
            try:

                user_question.location = json.loads(location_extraction(user_question.question))  # Extract location from user question
                query = (user_question.question + ' Additional context:' + user_question.location['county'] + ' ' + user_question.location['state']
                         + ' Elevation: ' + str(user_question.location['elevation']))

            except Exception as e:
                logging.error(f"Error occurred: {str(e)}")
                st.error('Sorry, I could not determine the location. Please add more info like what state it is located in.', icon="🚨")

            ######## COLLECT THE CORRECT DATA ########

            if user_question.method == 'snow_depth_data':
                user_question.sql = snow_depth_sql(query)

                logging.info(f"Snow depth SQL query: {user_question.sql}")

                user_question.data = query_bq_data(user_question.sql)

                st.session_state.sql.append({"question": query, "sql_query": user_question.sql})

                upload_blob_from_memory(bucket_name='ask-bc-analytics', contents=json.dumps(st.session_state.sql),
                                        destination_blob_name='sql-queries')

            if user_question.method == 'weather_forecast':
                lat = user_question.location['latitude']
                lon = user_question.location['longitude']
                user_question.data = 'Forecast: ' + str(weather_forecast(lat, lon))

            if user_question.method == 'co_field_obv':

                print(args['zone'])

                user_question.data = co_field_obv(args['zone'])


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
