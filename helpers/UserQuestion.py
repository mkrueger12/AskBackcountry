import os
import json
import dotenv
import openai
import streamlit as st
from google.cloud import bigquery


dotenv.load_dotenv('utils/.env')

openai.api_key = os.getenv('OPENAI_KEY')

# Open the JSON file and load its content into a dictionary
with open('utils/functions.json', 'r') as json_file:
    functions = json.load(json_file)



class UserQuestion:

    def __init__(_self, question):
        _self.question = question
        _self.sql = None
        _self.data = None
        _self.method = None


@st.cache_data(persist=True, ttl='24h')
def response(data, question):
    system_content = ('You are a helpful assistant. Answer the user question based on the context. '
                      f'<context>: {data}'
                      f'If you cannot answer the question, ask for more information. ')

    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        temperature=0.3,
        messages=[
            {"role": "system", "content": system_content},
            {"role": "user", "content": question}
        ]
    )

    return completion.choices[0].message['content']


@st.cache_data(persist=True, ttl=None)
def method_selector(question):

    ''' Determines which function should be called based on the user's query.'''

    messages = [{"role": "user", "content": question}]

    response = openai.ChatCompletion.create(
        model="gpt-4",
        temperature=0,
        max_tokens=512,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        messages=messages,
        functions=functions,
    )

    return response["choices"][0]["message"]["function_call"]['name']


@st.cache_data(persist=True, ttl='24h')
def query_bq_data(sql_query):
    # Initialize a BigQuery client
    client = bigquery.Client(project='avalanche-analytics-project')

    try:
        # Perform a query.
        query_job = client.query(sql_query)  # API request
        rows = query_job.result()  # Waits for query to finish
        data = [dict(row.items()) for row in rows]

        # Return the result
        return data
    except Exception as e:
        # Handle exceptions, you might want to log the error or raise it again
        print(f"Error: {e}")
        return None


def clear_chat_history():
    st.session_state.messages = [{"role": "assistant", "content": "Lets plan an adventure!"}]
    st.session_state['sql'] = [{"question": None, "sql_query": None}]


@st.cache_data(persist=True, ttl='24h')
def snow_depth_sql(question):
    system_content = '''Given the following SQL tables, your job is to write prompts given a user’s question.
                        When a location is included in the user question, determine the state and county.

                            CREATE TABLE `avalanche-analytics-project.historical_raw.snow-depth` (
                            state STRING <example: 'IL'>,
                            county STRING <Used to determine station county or location, example: 'Eagle'>,
                            latitude FLOAT,
                            longitude FLOAT,
                            elevation INTEGER,
                            station_name STRING <example: 'Schofield Pass'>,
                            station_id INTEGER,
                            Date DATE NULLABLE <yyyy-mm-dd>,
                            snow_depth FLOAT <do not use SUM()>,
                            new_snow FLOAT <inches, only SUM() when GROUP BY station_name>);

                            Use Google Standard SQL.
                            Return only the SQL query.
                            Always LIMIT results when possible.'''

    completion = openai.ChatCompletion.create(
        model="gpt-4",
        temperature=0,
        max_tokens=512,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        messages=[
            {"role": "system", "content": system_content},
            {"role": "user", "content": question}
        ]
    )

    return completion.choices[0].message['content']
