import os
import openai
from google.cloud import bigquery

openai.api_key = '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'


def get_query(question):
    system_content = '''You are a helpful BigQuery SQL assistant. Write a BigQuery SQL query that will answer the user question below. If you are unable to determine a value for the query ask for more information. /
    <Available columns: Date (yyyy-mm-dd), latitude, longitude, snow_depth (do not use SUM()), new_snow (new snow since yesterday), elevation, state (state code like 'IL'  for Illinois, county, station_name>
    <Available tables: `avalanche-analytics-project.historical_raw.snow-depth`>
    If using the county and state columns, be sure that they are correct before returning an answer. Do not include a value if you do not know what the correct value is.
    do not assume anything in the query.
    Return only the SQL query.'''

    completion = openai.ChatCompletion.create(
      model="gpt-4",
      messages=[
        {"role": "system", "content": system_content},
        {"role": "user", "content": question}
      ]
    )

    return completion.choices[0].message['content']


def run_bigquery_query(sql_query):
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

question = '<Question: Which snotel site near Vail, CO received the most snow since last Monday?>'

query = get_query(question)
print(query)

result = run_bigquery_query(query)
print(result)

