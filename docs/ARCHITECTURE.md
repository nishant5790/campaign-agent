# LinkedIn Post Generator - Architecture Documentation

This document provides a comprehensive overview of the LinkedIn Post Generator Agent architecture, including system design, workflow, and extension guidelines.

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Module Structure](#module-structure)
4. [Agent Workflow](#agent-workflow)
5. [Prompt System](#prompt-system)
6. [Configuration](#configuration)
7. [Data Models](#data-models)
8. [API Reference](#api-reference)
9. [Extension Guide](#extension-guide)
10. [Troubleshooting](#troubleshooting)

---

## System Overview

The LinkedIn Post Generator is an AI-powered agent that creates professional LinkedIn posts by:

1. **Discovering Trends**: Using Google Search grounding to identify trending topics in a professional field
2. **Conducting Research**: Performing parallel web searches to compile comprehensive research
3. **Generating Content**: Creating multiple post variations optimized for LinkedIn engagement
4. **Refining Posts**: Iteratively improving posts based on user feedback

### Key Technologies

| Component | Technology | Purpose |
|-----------|------------|---------|
| AI Model | Gemini 2.5 Flash | Primary LLM for content generation |
| Search | Gemini 2.0 Flash + Google Search | Web search with grounding |
| Framework | LangChain | Prompt orchestration and chaining |
| Backend | FastAPI | REST API and SSE streaming |
| Frontend | Vanilla JS + SSE | Real-time UI updates |

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                           Frontend (static/)                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                          │
│  │index.html│  │styles.css│  │  app.js  │                          │
│  └────┬─────┘  └──────────┘  └────┬─────┘                          │
│       │                           │                                  │
│       └───────────┬───────────────┘                                  │
│                   │ SSE Stream                                       │
└───────────────────┼──────────────────────────────────────────────────┘
                    │
┌───────────────────┼──────────────────────────────────────────────────┐
│                   ▼                                                   │
│            ┌─────────────┐                                           │
│            │   main.py   │  FastAPI Application                      │
│            │  (API Layer)│                                           │
│            └──────┬──────┘                                           │
│                   │                                                   │
│   ┌───────────────┼───────────────────────────────────────────┐     │
│   │               ▼            Agent Package                   │     │
│   │   ┌─────────────────────┐                                 │     │
│   │   │  LinkedInPostAgent  │  Main Orchestrator              │     │
│   │   └──────────┬──────────┘                                 │     │
│   │              │                                             │     │
│   │   ┌──────────┴──────────┐                                 │     │
│   │   │                     │                                 │     │
│   │   ▼                     ▼                                 │     │
│   │ ┌─────────────┐  ┌─────────────┐                         │     │
│   │ │  resources/ │  │   utils/    │                         │     │
│   │ │  ├─config   │  │  ├─models   │                         │     │
│   │ │  └─prompts  │  │  ├─parser   │                         │     │
│   │ └─────────────┘  │  └─loader   │                         │     │
│   │                  └─────────────┘                         │     │
│   └───────────────────────────────────────────────────────────┘     │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
                    │
                    ▼
          ┌─────────────────┐
          │  Google Gemini  │
          │      API        │
          └─────────────────┘
```

---

## Module Structure

```
campaign-agent/
├── docs/
│   └── ARCHITECTURE.md         # This documentation
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   └── agent/
│       ├── __init__.py         # Package exports and documentation
│       ├── linkedin_agent.py   # Main agent orchestration class
│       ├── resources/          # Configuration and static resources
│       │   ├── __init__.py
│       │   ├── config.py       # Configuration constants
│       │   └── prompts.yml     # All prompts in YAML format
│       └── utils/              # Utility modules
│           ├── __init__.py
│           ├── prompt_loader.py # YAML prompt loading and templating
│           ├── post_parser.py   # Post parsing and validation
│           └── models.py        # Dataclasses and type definitions
├── static/
│   ├── index.html
│   ├── styles.css
│   └── app.js
├── README.md
├── requirements.txt
└── ...
```

### Module Responsibilities

| Module | Location | Responsibility |
|--------|----------|----------------|
| `linkedin_agent.py` | `agent/` | Orchestrates the generation pipeline, manages LLM calls, handles streaming |
| `config.py` | `agent/resources/` | Centralizes all configuration constants and patterns |
| `prompts.yml` | `agent/resources/` | Contains all prompt text in editable YAML format |
| `prompt_loader.py` | `agent/utils/` | Loads YAML prompts, creates ChatPromptTemplate objects, caches templates |
| `post_parser.py` | `agent/utils/` | Parses raw LLM output into structured posts, validates content |
| `models.py` | `agent/utils/` | Defines data structures for events, posts, and results |

---

## Agent Workflow

The agent follows a three-stage pipeline for generating LinkedIn posts:

### Stage 1: Trending Topic Discovery

```
Input: Professional field (e.g., "Artificial Intelligence")
    │
    ▼
┌────────────────────────────┐
│  Search Query Generation   │
│  Template: trending_query  │
└─────────────┬──────────────┘
              │
              ▼
┌────────────────────────────┐
│  Google Search (Gemini)    │
│  Model: gemini-2.0-flash   │
└─────────────┬──────────────┘
              │
              ▼
┌────────────────────────────┐
│  Topic Analysis (LLM)      │
│  Prompt: trending_topics   │
└─────────────┬──────────────┘
              │
              ▼
Output: Top 5 trending topics with explanations
```

### Stage 2: Deep Research

```
Input: Trending topics + field
    │
    ▼
┌────────────────────────────┐
│  Generate Research Queries │
│  (3 parallel queries)      │
└─────────────┬──────────────┘
              │
              ▼
┌────────────────────────────┐
│  Parallel Web Searches     │
│  asyncio.gather()          │
└─────────────┬──────────────┘
              │
              ▼
┌────────────────────────────┐
│  Research Compilation      │
│  Prompt: research_report   │
└─────────────┬──────────────┘
              │
              ▼
Output: Comprehensive research report
```

### Stage 3: Post Generation

```
Input: Research report + field
    │
    ▼
┌────────────────────────────┐
│  Post Generation (LLM)     │
│  Prompt: post_generation   │
└─────────────┬──────────────┘
              │
              ▼
┌────────────────────────────┐
│  Post Parsing              │
│  PostParser.parse()        │
└─────────────┬──────────────┘
              │
              ▼
Output: 3 structured posts (Storytelling, Data-Driven, Thought Leadership)
```

### Event Flow

During execution, the agent emits events via Server-Sent Events (SSE):

| Event Type | Purpose | Data |
|------------|---------|------|
| `stage` | Signals start of a new stage | Stage name |
| `progress` | Updates on current activity | Progress message |
| `result` | Stage completion with data | Stage output |
| `complete` | All stages finished | Summary |
| `error` | Error occurred | Error message |

---

## Prompt System

### YAML Structure

Prompts are stored in `app/agent/resources/prompts.yml` with the following structure:

```yaml
prompt_name:
  description: "Brief description of the prompt's purpose"
  system: |
    System message content defining the AI's role and behavior.
    Can span multiple lines.
  human: |
    Human message template with {variable} placeholders.
    Variables are substituted at runtime.
```

### Available Prompts

| Prompt Name | Variables | Purpose |
|-------------|-----------|---------|
| `trending_topics` | `{field}`, `{context}` | Identify trending topics |
| `research_report` | `{topic}`, `{field}`, `{context}` | Compile research |
| `post_generation` | `{report}`, `{field}` | Generate posts |
| `refinement` | `{post}`, `{feedback}` | Refine based on feedback |

### Loading Prompts

```python
from app.agent import PromptLoader

# Create loader instance
loader = PromptLoader()

# Get ChatPromptTemplate
template = loader.get_template("trending_topics")

# Use with LangChain
chain = template | llm | StrOutputParser()
result = await chain.ainvoke({"field": "AI", "context": "..."})
```

### Modifying Prompts

To modify agent behavior, edit `app/agent/resources/prompts.yml`:

1. Open `prompts.yml` in any text editor
2. Modify the `system` or `human` message text
3. Preserve `{variable}` placeholders used by the code
4. Save the file - changes take effect on next agent initialization

**Important**: Do not rename prompt keys or remove required variables without updating the agent code.

---

## Configuration

### Configuration Classes

```python
from app.agent import DEFAULT_CONFIG

# Model settings
DEFAULT_CONFIG.model.llm_model        # "gemini-2.5-flash"
DEFAULT_CONFIG.model.llm_temperature  # 0.7
DEFAULT_CONFIG.model.search_model     # "gemini-2.0-flash"

# Search settings
DEFAULT_CONFIG.search.trending_query_template
DEFAULT_CONFIG.search.research_queries

# Post settings
DEFAULT_CONFIG.post.min_post_length   # 50
DEFAULT_CONFIG.post.max_posts         # 3
DEFAULT_CONFIG.post.post_styles       # ("Storytelling", "Data-Driven", ...)
```

### Customizing Configuration

To use custom configuration:

```python
from app.agent.resources.config import AgentConfig, ModelConfig

custom_config = AgentConfig(
    model=ModelConfig(
        llm_model="gemini-2.0-pro",
        llm_temperature=0.5,
    )
)
```

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GOOGLE_API_KEY` | Google AI API key | Yes |
| `ENVIRONMENT` | `development` or `production` | No |
| `PORT` | Server port (default: 8000) | No |

---

## Data Models

### AgentEvent

Represents events emitted during generation:

```python
@dataclass
class AgentEvent:
    type: str                           # Event type
    message: str                        # Human-readable message
    stage: Optional[str] = None         # Stage identifier
    data: Optional[Dict[str, Any]] = None  # Payload

    def to_dict(self) -> Dict[str, Any]: ...

    # Factory methods
    @classmethod
    def stage_event(cls, stage: str, message: str) -> "AgentEvent": ...
    @classmethod
    def progress_event(cls, message: str) -> "AgentEvent": ...
    @classmethod
    def result_event(cls, stage: str, message: str, data: dict) -> "AgentEvent": ...
    @classmethod
    def complete_event(cls, message: str) -> "AgentEvent": ...
    @classmethod
    def error_event(cls, message: str) -> "AgentEvent": ...
```

### ParsedPost

Represents a parsed LinkedIn post:

```python
@dataclass
class ParsedPost:
    id: int         # Sequential ID (1, 2, 3)
    style: str      # "Storytelling", "Data-Driven", "Thought Leadership"
    content: str    # Post text content

    def to_dict(self) -> Dict[str, Any]: ...
```

---

## API Reference

### POST /api/generate

Generate LinkedIn posts with SSE streaming.

**Request Body:**
```json
{
    "field": "Artificial Intelligence",
    "additional_context": "Focus on enterprise applications"
}
```

**Response:** Server-Sent Events stream

**Event Examples:**
```
data: {"type": "stage", "stage": "trending", "message": "Identifying topics..."}
data: {"type": "progress", "message": "Searching for: trending topics AI..."}
data: {"type": "result", "stage": "trending", "data": {"topics": "..."}}
data: {"type": "complete", "message": "All done!"}
```

### POST /api/refine

Refine a post based on feedback.

**Request Body:**
```json
{
    "post_content": "Original post text...",
    "feedback": "Make it more concise and add a question"
}
```

**Response:**
```json
{
    "success": true,
    "refined_post": "Refined post text..."
}
```

### GET /api/trending/{field}

Get trending topics for a field.

**Response:**
```json
{
    "success": true,
    "topics": "1. Topic one...\n2. Topic two..."
}
```

### GET /health

Health check endpoint.

**Response:**
```json
{
    "status": "healthy",
    "service": "linkedin-post-generator"
}
```

---

## Extension Guide

### Adding a New Prompt

1. **Add to `app/agent/resources/prompts.yml`:**
```yaml
my_new_prompt:
  description: "Description of the new prompt"
  system: |
    System message defining AI behavior...
  human: |
    Human message with {variables}...
```

2. **Use in agent:**
```python
template = self.prompt_loader.get_template("my_new_prompt")
chain = template | self.llm | StrOutputParser()
result = await chain.ainvoke({"variable": value})
```

### Adding a New Post Style

1. **Update `app/agent/resources/config.py`:**
```python
@dataclass(frozen=True)
class PostConfig:
    post_styles: tuple = (
        "Storytelling",
        "Data-Driven",
        "Thought Leadership",
        "Tutorial",  # New style
    )
```

2. **Update `prompts.yml`** post_generation prompt to include the new style.

### Adding a New Generation Stage

1. **Create stage method in `linkedin_agent.py`:**
```python
async def _stage_custom(self, ...) -> AsyncGenerator[Dict[str, Any], None]:
    yield AgentEvent.stage_event("custom", "Starting custom stage...").to_dict()
    # ... implementation
    yield AgentEvent.result_event("custom", "Done!", {"data": result}).to_dict()
```

2. **Add to `generate_posts_stream`:**
```python
async def generate_posts_stream(...):
    # ... existing stages
    async for event in self._stage_custom(...):
        yield event
```

3. **Add stage constant in `app/agent/resources/config.py`:**
```python
class Stage:
    TRENDING = "trending"
    RESEARCH = "research"
    GENERATION = "generation"
    CUSTOM = "custom"  # New stage
```

### Creating Custom Parser

```python
from app.agent import PostParser

class CustomParser(PostParser):
    def parse(self, raw_posts: str) -> List[ParsedPost]:
        # Custom parsing logic
        ...

# Use in agent
agent = LinkedInPostAgent(
    api_key=key,
    post_parser=CustomParser()
)
```

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| "API key not configured" | Missing GOOGLE_API_KEY | Set environment variable |
| "Prompt not found" | Typo in prompt name | Check prompts.yml keys |
| Empty posts returned | Parsing failed | Check LLM output format |
| Slow generation | Network latency | Consider caching |

### Debugging

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Check prompt loading:

```python
from app.agent import get_prompt_loader

loader = get_prompt_loader()
print(loader.list_prompts())  # List available prompts
```

### Performance Tips

1. **Parallel Searches**: Research queries run in parallel via `asyncio.gather()`
2. **Prompt Caching**: Templates are cached after first load
3. **Memory Management**: Large search results are cleared after use
4. **Streaming**: Use SSE streaming for responsive UI

---

## Version History

| Version | Changes |
|---------|---------|
| 2.1.0 | Reorganized into resources/ and utils/ directories |
| 2.0.0 | Refactored architecture with YAML prompts, modular design |
| 1.0.0 | Initial release with embedded prompts |

---
