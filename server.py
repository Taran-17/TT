import json
import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from agent_graph import AGENT_GRAPH
from agent_store import get_analytics, get_recent_messages, record_message
from workflow_catalog import (
    catalog_to_dicts,
    workflow_to_dict,
)


load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = FastAPI(title="TechTailor Customer Experience Agent Prototype")


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[Message]
    system_prompt: Optional[str] = None
    session_id: Optional[str] = None


class AgentAction(BaseModel):
    type: str
    parameters: Dict[str, Any] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    response: str
    actions: List[Dict[str, Any]] = []
    workflow_id: Optional[str] = None
    workflow_title: Optional[str] = None
    intent_bucket: Optional[str] = None
    workflow_summary: Optional[str] = None
    error: Optional[str] = None


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, x_groq_api_key: Optional[str] = Header(None)):
    if x_groq_api_key:
        os.environ["GROQ_API_KEY"] = x_groq_api_key

    session_id = request.session_id or "default"
    if request.messages:
        last_message = request.messages[-1]
        if last_message.role == "user":
            record_message(session_id, last_message.role, last_message.content)

    state = {
        "session_id": session_id,
        "messages": [msg.model_dump() for msg in request.messages],
        "system_prompt": request.system_prompt,
    }

    result = AGENT_GRAPH.invoke(state)
    if result.get("response"):
        record_message(
            session_id,
            "assistant",
            result.get("response", ""),
            workflow_id=result.get("workflow_id"),
            intent_bucket=result.get("intent_bucket"),
        )
    return ChatResponse(
        response=result.get("response", ""),
        actions=result.get("actions", []),
        workflow_id=result.get("workflow_id"),
        workflow_title=result.get("workflow_title"),
        intent_bucket=result.get("intent_bucket"),
        workflow_summary=result.get("workflow_summary"),
        error=result.get("error"),
    )


@app.get("/api/workflows")
async def get_workflows():
    return {"count": len(catalog_to_dicts()), "workflows": catalog_to_dicts()}


@app.get("/api/workflows/{workflow_id}")
async def get_workflow(workflow_id: str):
    from workflow_catalog import WORKFLOW_INDEX

    workflow = WORKFLOW_INDEX.get(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow_to_dict(workflow)


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    messages = get_recent_messages(session_id)
    analytics = get_analytics()
    return {"session_id": session_id, "messages": messages, "analytics": analytics}


@app.get("/api/analytics")
async def analytics():
    return get_analytics()


@app.get("/api/config")
async def get_config():
    api_key_set = bool(os.getenv("GROQ_API_KEY"))
    return {"groq_api_key_configured": api_key_set}


@app.post("/api/config")
async def save_config(config: Dict[str, str]):
    api_key = config.get("groq_api_key")
    if not api_key:
        return JSONResponse(status_code=400, content={"status": "error", "message": "No API Key provided"})

    try:
        env_path = os.path.join(BASE_DIR, ".env")
        with open(env_path, "w", encoding="utf-8") as handle:
            handle.write(f"GROQ_API_KEY={api_key}\n")
        os.environ["GROQ_API_KEY"] = api_key
        return {"status": "success", "message": "API Key saved successfully to .env"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": f"Failed to save .env file: {str(e)}"})


app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")


@app.get("/", response_class=HTMLResponse)
async def get_index():
    try:
        with open(os.path.join(BASE_DIR, "static", "index.html"), "r", encoding="utf-8") as handle:
            return HTMLResponse(content=handle.read())
    except FileNotFoundError:
        return HTMLResponse("<h2>Frontend static index.html is still generating... please refresh in a moment.</h2>")
