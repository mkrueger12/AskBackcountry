import os
import json
import requests
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
        _self.location = None


@st.cache_data(persist=True, ttl='24h')
def response(data, question):
    system_content = ('You are a helpful assistant. Answer the user question based on the context. '
                      f'<context>: {data}'
                      f'If you cannot answer the question, ask for more information. ')

    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        temperature=0.0,
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


@st.cache_data(persist=True, ttl=None)
def location_extraction(question):
    system_content = ('You will be provided with a text, and your task is to extract the county, state, elevation, latitude, and longitude from it.'
                      'If you are unsure return None for the given field.'
                      '#### Example ###'
                      'Text: How much snow is at Loveland Pass?'
                      'Response: {"county": "Clear Creek", "state": "CO", "elevation": 11900, "latitude": 39.6806, "longitude": -105.8972}')

    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
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


@st.cache_data(persist=True, ttl='1h')
def weather_forecast(latitude, longitude):

    url = f'https://api.weather.gov/points/{latitude},{longitude}'
    response = requests.get(url)
    data = response.json()
    forecast = requests.get(data['properties']['forecast'])
    forecast = forecast.json()

    return forecast['properties']['periods'][:6]


@st.cache_data(persist=True, ttl='24h')
def snow_depth_sql(question):
    system_content = '''Given the following SQL tables, your job is to write prompts given a user’s question.

                            CREATE TABLE `avalanche-analytics-project.historical_raw.snow-depth` (
                            state STRING <example: 'IL'>,
                            county STRING <Used to determine station county or location, example: 'Eagle'>,
                            latitude FLOAT,
                            longitude FLOAT,
                            elevation INTEGER,
                            station_id INTEGER,
                            station_name STRING <only use if station mentioned by user, example: 'Vail Mountain'>,
                            Date DATE NULLABLE <yyyy-mm-dd>,
                            snow_depth FLOAT <do not use SUM()>,
                            new_snow FLOAT <inches, only SUM() when GROUP BY station_name>);
                            
                            <example>
                            
                            user question: How much snow is at Loveland Pass? Additional Context:{"county": "Clear Creek", "state": "CO", "elevation": 11900}
                            Response:   WITH LatestDate AS (
                                                          SELECT MAX(Date) AS max_date
                                                          FROM `avalanche-analytics-project.historical_raw.snow-depth`
                                                          WHERE county = 'Clear Creek' AND state = 'CO' AND elevation > 9900
                                                        )
                                                        
                                                        SELECT AVG(snow_depth) AS average_snow_depth
                                                        FROM `avalanche-analytics-project.historical_raw.snow-depth` AS s
                                                        JOIN LatestDate AS ld
                                                        ON s.Date = ld.max_date
                                                        WHERE s.county = 'Clear Creek' AND s.state = 'CO' AND s.elevation > 9900;
                                                                    
                            <example>

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
