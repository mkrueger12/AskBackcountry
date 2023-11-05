import os
import dotenv
import openai
from google.cloud import bigquery

dotenv.load_dotenv('utils/.env')

openai.api_key = os.getenv('OPENAI_KEY')


class UserQuestion:

    def __init__(self, question):
        self.question = question
        self.snow_depth_sql = None

    def snow_depth_sql(self):
        system_content = '''You are a helpful BigQuery SQL assistant. Write a BigQuery SQL query that will answer the user question below. If you are unable to determine a value for the query ask for more information. /
        <Available columns: Date (yyyy-mm-dd), latitude, longitude, snow_depth (do not use SUM()), new_snow (new snow since yesterday), elevation, state (state code like 'IL'  for Illinois, county (administrative subdivision of a state), station_name (Vail Mountain)>
        <Available tables: `avalanche-analytics-project.historical_raw.snow-depth`>
        If using the county and state columns, be sure that they are correct before returning an answer. Do not include a value if you do not know what the correct value is.
        Do not assume anything in the query. Always LIMIT results when possible.
        Return only the SQL query.'''

        system_content = '''Given the following SQL tables, your job is to write queries given a user’s question. 
                            CREATE TABLE `avalanche-analytics-project.historical_raw.snow-depth` (
                            state STRING NULLABLE <state code like 'IL'  for Illinois>,
                            county STRING NULLABLE <Used to determine station county or location>,
                            latitude FLOAT NULLABLE,
                            longitude FLOAT NULLABLE,
                            elevation INTEGER NULLABLE,
                            station_name STRING NULLABLE,
                            station_id INTEGER NULLABLE,
                            Date DATE NULLABLE <yyyy-mm-dd>,
                            snow_depth FLOAT NULLABLE <do not use SUM()>,
                            new_snow FLOAT NULLABLE <inches>);
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
                {"role": "user", "content": self.question}
            ]
        )

        return completion.choices[0].message['content']

    def collect_snow_depth_data(self):
        # Initialize a BigQuery client
        client = bigquery.Client(project='avalanche-analytics-project')

        try:
            # Perform a query.
            QUERY = self.snow_depth_sql()
            query_job = client.query(QUERY)  # API request
            rows = query_job.result()  # Waits for query to finish
            result_dicts = [dict(row.items()) for row in rows]

            # Return the result
            return result_dicts
        except Exception as e:
            # Handle exceptions, you might want to log the error or raise it again
            print(f"Error: {e}")
            return None
