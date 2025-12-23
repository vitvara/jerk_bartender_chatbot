from openai import OpenAI
import os

openai_token = os.environ['OPEN_AI_TOKEN']
client = OpenAI(api_key=openai_token)
