import os
import dotenv
import openai
from google.cloud import bigquery

dotenv.load_dotenv('utils/.env')

openai.api_key = os.getenv('OPENAI_KEY')


class SnowDepthQuestion:

    def __init__(self):
        pass


    def get_query(self, question):
        system_content = '''You are a helpful BigQuery SQL assistant. Write a BigQuery SQL query that will answer the user question below. If you are unable to determine a value for the query ask for more information. /
        <Available columns: Date (yyyy-mm-dd), latitude, longitude, snow_depth (do not use SUM()), new_snow (new snow since yesterday), elevation, state (state code like 'IL'  for Illinois, county (administrative subdivision of a state), station_name (Vail Mountain)>
        <Available tables: `avalanche-analytics-project.historical_raw.snow-depth`>
        If using the county and state columns, be sure that they are correct before returning an answer. Do not include a value if you do not know what the correct value is.
        Do not assume anything in the query. Always LIMIT results when possible.
        Return only the SQL query.'''

        completion = openai.ChatCompletion.create(
          model="gpt-4",
          messages=[
            {"role": "system", "content": system_content},
            {"role": "user", "content": question}
          ]
        )

        return completion.choices[0].message['content']


    def run_bigquery_query(self, sql_query):
        # Initialize a BigQuery client
        client = bigquery.Client(project='avalanche-analytics-project')

        try:
            # Perform a query.
            QUERY = sql_query
            query_job = client.query(QUERY)  # API request
            rows = query_job.result()  # Waits for query to finish
            result_dicts = [dict(row.items()) for row in rows]

            # Return the result
            return result_dicts
        except Exception as e:
            # Handle exceptions, you might want to log the error or raise it again
            print(f"Error: {e}")
            return None


def get_response(data, question):
        system_content = ('You are a helpful assistant. Answer the user question based on the context. '
                          'If you are unable to determine a value for the query ask for more information.'
                          f'<context>: {data}')

        completion = openai.ChatCompletion.create(
          model="gpt-3.5-turbo",
          messages=[
            {"role": "system", "content": system_content},
            {"role": "user", "content": question}
          ]
        )

        return completion.choices[0].message['content']


