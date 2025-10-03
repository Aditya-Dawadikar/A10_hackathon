import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
from langchain_google_genai import ChatGoogleGenerativeAI

from utils.sanitizer import PromptSanitizationAgent

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("❌ Missing GOOGLE_API_KEY in environment variables or .env file")

# Create Gemini LLM client
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",   # ✅ replace with valid model id
    temperature=0.7,
    google_api_key=GOOGLE_API_KEY
)


# ---------- FastAPI Setup ----------
app = FastAPI()
agent = PromptSanitizationAgent()

class PromptRequest(BaseModel):
    target_llm: str
    prompt: str


@app.post("/sanitize")
async def sanitize(request: Request):
    body = await request.json()
    prompt = body.get("prompt", "")
    result = agent.process(prompt)

    return result

@app.post("/chat")
async def chat(request: Request):
    body = await request.json()
    prompt = body.get("prompt", "")

    # 1. Run sanitization
    result = agent.process(prompt)

    if result["status"] == "blocked":
        # Return immediately if malicious
        return result

    # 2. Stream LLM response for allowed prompts
    redacted_prompt = result["redacted_prompt"]

    async def stream_llm():
        async for chunk in agent.llm.astream(redacted_prompt):
            # Each chunk is a message object -> yield only text tokens
            if chunk.content:
                yield chunk.content

    return StreamingResponse(stream_llm(), media_type="text/plain")