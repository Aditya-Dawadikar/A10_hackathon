import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Query
from fastapi import HTTPException
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
from langchain_google_genai import ChatGoogleGenerativeAI
from policy_controller import (
    create_policy, list_policies, create_group,
    add_policy_to_group, remove_policy_from_group, get_group_with_policies,
    PolicyIn, GroupIn
)

from utils.sanitizer import PromptSanitizationAgent

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("❌ Missing GOOGLE_API_KEY in environment variables or .env file")

# Create Gemini LLM client
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.7,
    google_api_key=GOOGLE_API_KEY
)


# ---------- FastAPI Setup ----------
app = FastAPI()
agent = PromptSanitizationAgent()

class PromptRequest(BaseModel):
    target_llm: str
    prompt: str

@app.post("/policy")
async def api_create_policy(policy: PolicyIn):
    return await create_policy(policy)

@app.get("/policies")
async def api_list_policies():
    return await list_policies()

@app.post("/group")
async def api_create_group(group: GroupIn):
    return await create_group(group)

@app.get("/group")
async def get_group_info(
    groupId: str | None = Query(None),
    name: str | None = Query(None)
):
    group = await get_group_with_policies(group_id=groupId, name=name)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return group

@app.post("/group/{group_id}/add/{policy_id}")
async def api_add_policy_to_group(group_id: str, policy_id: str):
    group = await add_policy_to_group(group_id, policy_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return group

@app.delete("/group/{group_id}/remove/{policy_id}")
async def api_remove_policy_from_group(group_id: str, policy_id: str):
    group = await remove_policy_from_group(group_id, policy_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return group

@app.post("/sanitize")
async def sanitize(request: Request):
    body = await request.json()
    prompt = body.get("prompt")
    group_id = body.get("groupId")
    group_name = body.get("groupName")

    result = await agent.process(prompt, group_id=group_id, group_name=group_name)  # ✅ await
    return result

@app.post("/chat")
async def chat(request: Request):
    body = await request.json()
    prompt = body.get("prompt", "")
    group_id = body.get("groupId")
    group_name = body.get("groupName")

    # 1. Run sanitization (await just like /sanitize)
    result = await agent.process(prompt, group_id=group_id, group_name=group_name)

    if result["status"] == "blocked":
        # Return JSON immediately if malicious
        return result

    # 2. Stream LLM response for allowed prompts
    redacted_prompt = result["redacted_prompt"]

    async def stream_llm():
        async for chunk in agent.llm.astream(redacted_prompt):
            if chunk.content:
                # yield plain text tokens
                yield chunk.content

    return StreamingResponse(stream_llm(), media_type="text/plain")