"""
Configuration settings for the LinkedIn Post Generator Agent.

This module centralizes all configuration constants, model settings,
and templates used by the agent.
"""
from dataclasses import dataclass, field
from typing import List
import re


@dataclass(frozen=True)
class ModelConfig:
    """Configuration for AI models."""
    # Primary model for general LLM tasks (via Langchain)
    llm_model: str = "gemini-2.5-flash"
    llm_temperature: float = 0.7
    
    # Model for search-grounded queries (via google.genai)
    search_model: str = "gemini-2.0-flash"


@dataclass(frozen=True)
class SearchConfig:
    """Configuration for web search queries."""
    # Template patterns for search queries
    trending_query_template: str = "trending topics {field} 2024 2025 latest news developments"
    
    # Research query templates
    research_queries: tuple = (
        "{field} industry trends statistics 2024 2025",
        "{field} expert opinions thought leadership",
        "{field} case studies success stories",
    )


@dataclass(frozen=True)
class PostConfig:
    """Configuration for post generation and parsing."""
    # Post markers for parsing
    post_markers: tuple = (
        "--- POST 1 ---",
        "--- POST 2 ---",
        "--- POST 3 ---",
    )
    
    # Post styles corresponding to each marker
    post_styles: tuple = (
        "Storytelling",
        "Data-Driven",
        "Thought Leadership",
    )
    
    # Regex pattern for splitting posts
    post_split_pattern: str = r'(?:---\s*POST\s*\d+\s*---|Post\s*\d+[:\-]|#\s*Post\s*\d+)'
    
    # Minimum post length (characters) for validation
    min_post_length: int = 50
    
    # Maximum number of posts to return
    max_posts: int = 3
    
    # Recommended post length range (words)
    min_word_count: int = 150
    max_word_count: int = 300


@dataclass(frozen=True)
class AgentConfig:
    """Main configuration container for the agent."""
    model: ModelConfig = field(default_factory=ModelConfig)
    search: SearchConfig = field(default_factory=SearchConfig)
    post: PostConfig = field(default_factory=PostConfig)
    
    # Path to prompts file (relative to this config file)
    prompts_file: str = "prompts.yml"


# Event types emitted during agent execution
class EventType:
    """Constants for agent event types."""
    STAGE = "stage"
    PROGRESS = "progress"
    RESULT = "result"
    COMPLETE = "complete"
    ERROR = "error"


# Stage identifiers
class Stage:
    """Constants for agent processing stages."""
    TRENDING = "trending"
    RESEARCH = "research"
    GENERATION = "generation"


# Default configuration instance
DEFAULT_CONFIG = AgentConfig()


def get_compiled_post_pattern() -> re.Pattern:
    """Get compiled regex pattern for post parsing."""
    return re.compile(DEFAULT_CONFIG.post.post_split_pattern, flags=re.IGNORECASE)
