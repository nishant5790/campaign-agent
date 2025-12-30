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
    version="1.0.0",
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


class GenerateRequest(BaseModel):
    """Request model for post generation"""
    field: str
    additional_context: str = ""


class RefineRequest(BaseModel):
    """Request model for post refinement"""
    post_content: str
    feedback: str


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main HTML page"""
    return FileResponse(str(STATIC_DIR / "index.html"))


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "linkedin-post-generator"}


async def generate_stream(field: str, additional_context: str) -> AsyncGenerator[str, None]:
    """Stream generation events using SSE"""
    try:
        async for event in agent.generate_posts_stream(field, additional_context):
            yield json.dumps(event)
    except Exception as e:
        yield json.dumps({
            "type": "error",
            "message": str(e)
        })


@app.post("/api/generate")
async def generate_posts(request: GenerateRequest):
    """Generate LinkedIn posts using SSE streaming"""
    if not agent:
        raise HTTPException(status_code=500, detail="Agent not initialized")
    
    return EventSourceResponse(
        generate_stream(request.field, request.additional_context),
        media_type="text/event-stream"
    )


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


@app.get("/api/trending/{field}")
async def get_trending_topics(field: str):
    """Get trending topics for a specific field"""
    if not agent:
        raise HTTPException(status_code=500, detail="Agent not initialized")
    
    try:
        topics = await agent.get_trending_topics(field)
        return {"success": True, "topics": topics}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)

