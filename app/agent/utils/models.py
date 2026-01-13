"""
Data models for the LinkedIn Post Generator Agent.

This module defines dataclasses and types used throughout the agent
for structured data representation and type safety.
"""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from enum import Enum

from ..resources.config import EventType, Stage


class AgentStage(Enum):
    """Enumeration of agent processing stages."""
    TRENDING = Stage.TRENDING
    RESEARCH = Stage.RESEARCH
    GENERATION = Stage.GENERATION


class AgentEventType(Enum):
    """Enumeration of event types emitted by the agent."""
    STAGE = EventType.STAGE
    PROGRESS = EventType.PROGRESS
    RESULT = EventType.RESULT
    COMPLETE = EventType.COMPLETE
    ERROR = EventType.ERROR


@dataclass
class AgentEvent:
    """
    Event emitted during agent execution.
    
    Events are used to communicate progress, results, and errors
    during the streaming generation process.
    
    Attributes:
        type: The type of event (stage, progress, result, complete, error)
        message: Human-readable message describing the event
        stage: Optional stage identifier for stage/result events
        data: Optional additional data payload
    """
    type: str
    message: str
    stage: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for JSON serialization."""
        result = {
            "type": self.type,
            "message": self.message,
        }
        if self.stage is not None:
            result["stage"] = self.stage
        if self.data is not None:
            result["data"] = self.data
        return result
    
    @classmethod
    def stage_event(cls, stage: str, message: str) -> "AgentEvent":
        """Create a stage start event."""
        return cls(
            type=EventType.STAGE,
            message=message,
            stage=stage,
        )
    
    @classmethod
    def progress_event(cls, message: str) -> "AgentEvent":
        """Create a progress update event."""
        return cls(
            type=EventType.PROGRESS,
            message=message,
        )
    
    @classmethod
    def result_event(
        cls, 
        stage: str, 
        message: str, 
        data: Dict[str, Any]
    ) -> "AgentEvent":
        """Create a result event with data payload."""
        return cls(
            type=EventType.RESULT,
            message=message,
            stage=stage,
            data=data,
        )
    
    @classmethod
    def complete_event(cls, message: str = "Generation complete!") -> "AgentEvent":
        """Create a completion event."""
        return cls(
            type=EventType.COMPLETE,
            message=message,
            data={},
        )
    
    @classmethod
    def error_event(cls, message: str) -> "AgentEvent":
        """Create an error event."""
        return cls(
            type=EventType.ERROR,
            message=message,
        )


@dataclass
class ParsedPost:
    """
    A parsed LinkedIn post with metadata.
    
    Attributes:
        id: Sequential identifier for the post
        style: The style of the post (Storytelling, Data-Driven, etc.)
        content: The actual post content
    """
    id: int
    style: str
    content: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "style": self.style,
            "content": self.content,
        }


@dataclass
class ResearchReport:
    """
    Research report compiled by the agent.
    
    Attributes:
        topic: The main topic researched
        field: The professional field context
        content: The full research report content
        sources: Optional list of search queries used
    """
    topic: str
    field: str
    content: str
    sources: List[str] = field(default_factory=list)


@dataclass
class GenerationResult:
    """
    Complete result of a post generation session.
    
    Attributes:
        field: The professional field specified
        trending_topics: Identified trending topics
        research_report: Compiled research report
        posts: List of generated posts
        raw_posts: Raw post output before parsing
    """
    field: str
    trending_topics: str
    research_report: str
    posts: List[ParsedPost]
    raw_posts: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "field": self.field,
            "trending_topics": self.trending_topics,
            "research_report": self.research_report,
            "posts": [post.to_dict() for post in self.posts],
            "raw_posts": self.raw_posts,
        }
