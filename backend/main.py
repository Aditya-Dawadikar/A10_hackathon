import os
from typing import Optional
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Query
from fastapi import HTTPException
from pydantic import BaseModel
from typing import List
from fastapi.responses import StreamingResponse, JSONResponse
from langchain_google_genai import ChatGoogleGenerativeAI
from policy_controller import (
    create_policy, list_policies, create_group,
    add_policy_to_group, remove_policy_from_group, get_group_with_policies,
    get_all_groups_with_policies, update_group_policies, delete_group,
    PolicyIn, GroupIn
)

from utils.sanitizer import PromptSanitizationAgent

# Import observability functions if they exist
try:
    from observability import (
        process_sanitize_request, 
        get_metrics_data, 
        get_logs_data, 
        parse_time_range
    )
    OBSERVABILITY_ENABLED = True
except ImportError:
    OBSERVABILITY_ENABLED = False
    print("⚠️ Observability module not found. Metrics and logs endpoints will be disabled.")

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

@app.get("/")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "AI Firewall Proxy",
        "observability_enabled": OBSERVABILITY_ENABLED,
        "endpoints": [
            "/sanitize",
            "/chat", 
            "/metrics" if OBSERVABILITY_ENABLED else "/metrics (disabled)",
            "/logs" if OBSERVABILITY_ENABLED else "/logs (disabled)",
            "/policy",
            "/policies",
            "/group"
        ]
    }

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

@app.get("/groups")
async def get_all_groups():
    try:
        groups = await get_all_groups_with_policies()
        if not groups:
            raise HTTPException(status_code=404, detail="Groups not found")
        return groups
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
    
    # Support both legacy and new formats
    prompt = body.get("prompt") or body.get("payload", "")
    group_id = body.get("groupId") or body.get("group_id")
    group_name = body.get("groupName") or body.get("group_name")
    agent_id = body.get("agent_id")
    
    if not prompt:
        raise HTTPException(status_code=400, detail="Missing 'prompt' or 'payload' in request body")

    result = await agent.process(prompt, group_id=group_id, group_name=group_name)
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


@app.get("/metrics")
async def get_metrics(
    from_time: Optional[str] = Query(None, alias="from"),
    to_time: Optional[str] = Query(None, alias="to"), 
    group: Optional[str] = Query(None)
):
    """Get firewall metrics with optional time range and grouping"""
    
    if not OBSERVABILITY_ENABLED:
        raise HTTPException(status_code=501, detail="Observability module not available")
    
    # Handle time range shortcuts like "1h", "24h", "7d"
    if from_time and from_time in ["1h", "24h", "7d"]:
        from_time, to_time = parse_time_range(from_time)
    
    # Set group_by parameter
    group_by = None
    if group == "agent_id":
        group_by = "agent_id"
    elif group == "status":
        group_by = "status"
    
    metrics = get_metrics_data(from_time, to_time, group_by)
    return JSONResponse(content=metrics)

@app.get("/logs")
async def get_logs(
    status: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=100)
):
    """Get recent firewall logs with optional status filter"""
    
    if not OBSERVABILITY_ENABLED:
        raise HTTPException(status_code=501, detail="Observability module not available")
    
    # Validate status parameter
    if status and status not in ["allowed", "redacted", "blocked"]:
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid status. Must be one of: allowed, redacted, blocked"}
        )
    
    logs = get_logs_data(status, limit)
    return JSONResponse(content=logs)

class GroupPoliciesUpdate(BaseModel):
    policy_ids: List[str]

@app.put("/{group_id}/policies")
async def api_update_group_policies(group_id: str, body: GroupPoliciesUpdate):
    updated = await update_group_policies(group_id, body.policy_ids)
    if not updated:
        raise HTTPException(status_code=404, detail="Group not found")
    return updated

@app.delete("/group/{group_id}")
async def api_delete_group(group_id: str):
    """Delete a group by its ID"""
    deleted = await delete_group(group_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Group not found")
    return {"message": "Group deleted successfully"}
