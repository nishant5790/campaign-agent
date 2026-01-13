"""
LinkedIn Post Generator Agent Package.

This package provides an AI-powered agent for generating professional
LinkedIn posts using Google's Gemini AI with web search grounding.

Main Components:
    - LinkedInPostAgent: The main agent class for post generation
    - PromptLoader: Loads prompts from YAML configuration
    - PostParser: Parses LLM output into structured posts
    - AgentEvent: Event dataclass for streaming updates
    - DEFAULT_CONFIG: Default agent configuration

Example Usage:
    ```python
    from app.agent import LinkedInPostAgent
    
    agent = LinkedInPostAgent(api_key="your-api-key")
    
    # Stream post generation
    async for event in agent.generate_posts_stream("Artificial Intelligence"):
        print(event)
    
    # Refine a post
    refined = await agent.refine_post(post_content, feedback)
    ```
"""

from .linkedin_agent import LinkedInPostAgent

# Import from utils
from .utils.prompt_loader import PromptLoader, get_prompt_loader
from .utils.post_parser import PostParser, get_post_parser, parse_posts
from .utils.models import (
    AgentEvent,
    ParsedPost,
    ResearchReport,
    GenerationResult,
    AgentStage,
    AgentEventType,
)

# Import from resources
from .resources.config import (
    DEFAULT_CONFIG,
    AgentConfig,
    ModelConfig,
    SearchConfig,
    PostConfig,
    EventType,
    Stage,
)

__all__ = [
    # Main agent
    "LinkedInPostAgent",
    
    # Prompt handling
    "PromptLoader",
    "get_prompt_loader",
    
    # Post parsing
    "PostParser",
    "get_post_parser",
    "parse_posts",
    
    # Data models
    "AgentEvent",
    "ParsedPost",
    "ResearchReport",
    "GenerationResult",
    "AgentStage",
    "AgentEventType",
    
    # Configuration
    "DEFAULT_CONFIG",
    "AgentConfig",
    "ModelConfig",
    "SearchConfig",
    "PostConfig",
    "EventType",
    "Stage",
]

__version__ = "2.1.0"
