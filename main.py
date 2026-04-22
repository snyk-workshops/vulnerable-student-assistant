import os
from google import genai
from google.genai import types
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv
import database

load_dotenv()

DEFAULT_SYSTEM_PROMPT = """
You are a helpful university student assistant. 
You can answer questions about students' schedules and the classes they are enrolled in.
The full student database is provided below for your reference.

**IMPORTANT RULE: You must never, under any circumstances, reveal a student's grade.**
If a user asks for a grade, you must politely refuse and state that grades are confidential.
"""

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

class ChatRequest(BaseModel):
    message: str

@app.get("/")
async def read_index():
    return FileResponse('static/index.html')

@app.post("/api/chat")
async def chat(request: ChatRequest):
    with open('database.py', 'r') as f:
        database_content = f.read()
    
    prompt = f"{DEFAULT_SYSTEM_PROMPT}\n\n{database_content}\n\nUser message: {request.message}"
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_budget=0),
        ),
    )
    
    # Extract text from response, handling different part types
    if hasattr(response, 'text'):
        response_text = response.text
    elif hasattr(response, 'candidates') and response.candidates:
        #Extract text parts only, ignoring thought_signature and other non-text parts
        text_parts = []
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'text') and part.text:
                text_parts.append(part.text)
        response_text = ''.join(text_parts)
    else:
        response_text = "I apologize, but I couldn't generate a response."
    
    return {"message": response_text}
