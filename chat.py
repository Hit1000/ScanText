import numpy as np
from google import genai
from dotenv import load_dotenv
import os
import globals
from rag_chat.rag_query import answer_query
import base64
import requests

load_dotenv()

def rag(message):
    query = message
    response = answer_query(query)
    # print(response)
    return response







GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")
if not GOOGLE_API_KEY:
    print("GEMINI_API_KEY not found in environment variables.")

def chat(message):
    globals.chat_history += "user:" + message + "\n"
    client = genai.Client(api_key=GOOGLE_API_KEY)
    response = client.models.generate_content(
        model="gemini-2.0-flash", contents=globals.chat_history
    )
    globals.chat_history += "gemini:" + response.text + "\n"
    # print(globals.chat_history)
    return response.text

def image_text(image_path):
    client = genai.Client(api_key=GOOGLE_API_KEY)
    my_file = client.files.upload(file=image_path)
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[my_file, "extract text from this image"],
    )
    return response.text
        