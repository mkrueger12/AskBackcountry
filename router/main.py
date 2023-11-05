import openai
import json
import dotenv
import os

dotenv.load_dotenv('utils/.env')

openai.api_key = os.getenv('OPENAI_KEY')

def GPT_QB(user_query):

    ''' Determines which function should be called based on the user's query.'''

    messages = [{"role": "user", "content": user_query}]
    functions = [
        {
            "name": "snow_depth_data",
            "description": "Collects Snow Depth and Snow Fall data based on the user's question.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_question": {
                        "type": "string",
                        "description": "How much new snow has fallen in the last 24 hours in Eagle County?",
                    },
                },
                "required": ["user_question"],
            },
        },
        {
            "name": "get_query_hunting",
            "description": "Generates a SQL query for hunting related data based on the user's question.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_question": {
                        "type": "string",
                        "description": "What was the archery elk success rate for GMU 49?",
                    },
                },
                "required": ["user_question"],
            },
        }
    ]

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

    return response["choices"][0]["message"]["function_call"]


response = GPT_QB("How many tags were issued game management unit 23?")
