import openai
import dotenv
import os
import json


dotenv.load_dotenv('.env')


openai.api_key = os.getenv('OPENAI_KEY')

tools = [{
    "type": "function",
    "function": {
        "name": "snow_depth_data",
        "description": "Collects Snow Depth and Snow Fall data.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_question": {
                    "type": "string",
                    "description": "How much new snow has fallen in the last 24 hours in Eagle County?"
                }
            },
            "required": [
                "user_question"
            ]
        }
    }
}, {
    "type": "function",
    "function": {
        "name": "weather_forecast",
        "description": "Returns the 3-day weather forecast for a given location.",
        "parameters": {
            "type": "object",
            "properties": {
                "latitude": {
                    "type": "string",
                    "description": "Latitude of the location in decimal degrees."
                },
                "longitude": {
                    "type": "string",
                    "description": "longitude of the location in decimal degrees."
                }
            },
            "required": ['latitude', 'longitude']
        }
    }
}]

assistant = openai.beta.assistants.create(
    name="Ask BC",
    instructions="You are a backcountry trip planning assistant. Answer questions provided by the user.",
    tools=tools,
    model="gpt-4-1106-preview"
)

thread = openai.beta.threads.create()

message = openai.beta.threads.messages.create(
    thread_id=thread.id,
    role="user",
    content="What is the weather forecast for Vail Mountain?"
)

run = openai.beta.threads.runs.create(
    thread_id=thread.id,
    assistant_id=assistant.id,
    instructions="Please answer the users question"
)

run = openai.beta.threads.runs.retrieve(
    thread_id=thread.id,
    run_id=run.id
)

messages = openai.beta.threads.messages.list(
    thread_id=thread.id
)
