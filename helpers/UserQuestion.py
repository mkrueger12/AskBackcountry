import os
import json
import dotenv
import openai
from google.cloud import bigquery


dotenv.load_dotenv('utils/.env')

openai.api_key = os.getenv('OPENAI_KEY')

# Open the JSON file and load its content into a dictionary
with open('utils/functions.json', 'r') as json_file:
    functions = json.load(json_file)


class UserQuestion:

    def __init__(self, question):
        self.question = question
        self.sql = None
        self.data = None
        self.method = None

    def method_selector(self):

        ''' Determines which function should be called based on the user's query.'''

        messages = [{"role": "user", "content": self.question}]

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

        self.method = response["choices"][0]["message"]["function_call"]['name']

        return self.method

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
                            county STRING NULLABLE <Used to determine station county or location, example: 'Eagle'>,
                            latitude FLOAT NULLABLE,
                            longitude FLOAT NULLABLE,
                            elevation INTEGER NULLABLE,
                            station_name STRING NULLABLE,
                            station_id INTEGER NULLABLE,
                            Date DATE NULLABLE <yyyy-mm-dd>,
                            snow_depth FLOAT NULLABLE <do not use SUM()>,
                            new_snow FLOAT NULLABLE <inches>);
                            
                            Use Google Standard SQL.
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

        self.sql = completion.choices[0].message['content']

        return self.sql

    def snow_depth_data(self):
        # Initialize a BigQuery client
        client = bigquery.Client(project='avalanche-analytics-project')

        try:
            # Perform a query.
            QUERY = self.snow_depth_sql()
            print(QUERY)
            query_job = client.query(QUERY)  # API request
            rows = query_job.result()  # Waits for query to finish
            self.data = [dict(row.items()) for row in rows]

            # Return the result
            return self.data
        except Exception as e:
            # Handle exceptions, you might want to log the error or raise it again
            print(f"Error: {e}")
            return None

    def run(self):
        self.method_selector()

        if self.method == 'snow_depth_data':
            self.snow_depth_data()
        else:
            return ('Sorry, I could not find any results for your query.')


######################

user_question = UserQuestion("How much new snow has fallen in October 2023 in Eagle County?")
user_question.run()


