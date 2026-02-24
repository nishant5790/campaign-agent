"""
LinkedIn Post Generator - Main FastAPI Application
"""
import os
import json
import asyncio
from pathlib import Path
from typing import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel
from dotenv import load_dotenv

from app.agent.linkedin_agent import LinkedInPostAgent
from app.agent.chat_session import session_manager

load_dotenv()

# Get the base directory (project root)
BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

# Global agent instance
agent: LinkedInPostAgent = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global agent
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("WARNING: GOOGLE_API_KEY not set. Agent will not function properly.")
    agent = LinkedInPostAgent(api_key=api_key)
    yield
    # Cleanup if needed


app = FastAPI(
    title="LinkedIn Post Generator",
    description="AI-powered LinkedIn post generator using Langchain and Gemini",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ─── Request Models ─────────────────────────────────────────────

class ChatRequest(BaseModel):
    """Request model for chat messages"""
    session_id: str
    message: str


class ApprovePlanRequest(BaseModel):
    """Request model for plan approval"""
    session_id: str


class RefineRequest(BaseModel):
    """Request model for post refinement"""
    post_content: str
    feedback: str


# ─── Pages ───────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main HTML page"""
    return FileResponse(str(STATIC_DIR / "index.html"))


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "linkedin-post-generator"}


# ─── Session Management ─────────────────────────────────────────

@app.post("/api/sessions")
async def create_session():
    """Create a new chat session"""
    session = session_manager.create_session()
    return {
        "success": True,
        "session_id": session.session_id,
        "status": session.status,
    }


# ─── Chat ────────────────────────────────────────────────────────

@app.post("/api/chat")
async def chat_message(request: ChatRequest):
    """
    Send a chat message and receive AI response.
    
    The AI will ask clarifying questions and eventually produce
    a research plan when it has enough context.
    """
    if not agent:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    session = session_manager.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    result = await agent.chat(session, request.message)

    return {
        "success": True,
        "response": result["response"],
        "plan": result.get("plan"),
        "status": result["status"],
        "session": session.to_dict(),
    }


# ─── Plan Approval & Generation ─────────────────────────────────

@app.post("/api/approve-plan")
async def approve_plan(request: ApprovePlanRequest):
    """
    Approve the generated plan and start post generation via SSE.
    """
    if not agent:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    session = session_manager.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.status != "plan_pending":
        raise HTTPException(
            status_code=400,
            detail=f"Session is not awaiting plan approval (status: {session.status})"
        )

    session.approve_plan()

    async def stream() -> AsyncGenerator[str, None]:
        try:
            async for event in agent.generate_posts_from_session(session):
                yield json.dumps(event)
        except Exception as e:
            yield json.dumps({
                "type": "error",
                "message": str(e)
            })

    return EventSourceResponse(stream(), media_type="text/event-stream")


# ─── Post Refinement ────────────────────────────────────────────

@app.post("/api/refine")
async def refine_post(request: RefineRequest):
    """Refine a LinkedIn post based on user feedback"""
    if not agent:
        raise HTTPException(status_code=500, detail="Agent not initialized")
    
    try:
        refined_post = await agent.refine_post(request.post_content, request.feedback)
        return {"success": True, "refined_post": refined_post}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
