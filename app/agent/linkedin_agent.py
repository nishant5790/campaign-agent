"""
LinkedIn Post Generator Agent using Langchain and Gemini 2.5 Flash.

This module provides the main agent class that orchestrates the generation
of LinkedIn posts through trending topic discovery, research, and content creation.
"""
import asyncio
import logging
from typing import AsyncGenerator, Dict, Any, Optional

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser
from google import genai
from google.genai import types

from .resources.config import DEFAULT_CONFIG, Stage
from .utils.models import AgentEvent
from .utils.prompt_loader import PromptLoader
from .utils.post_parser import PostParser

logger = logging.getLogger(__name__)


class LinkedInPostAgent:
    """
    AI Agent for generating professional LinkedIn posts.
    
    Uses Gemini 2.5 Flash with Google Search grounding for research
    and LangChain for prompt orchestration.
    
    Attributes:
        api_key: Google API key for authentication
        config: Agent configuration settings
        prompt_loader: Loader for YAML-based prompts
        post_parser: Parser for extracting posts from LLM output
    """
    
    def __init__(
        self, 
        api_key: str,
        prompt_loader: Optional[PromptLoader] = None,
        post_parser: Optional[PostParser] = None,
    ):
        """
        Initialize the LinkedIn Post Agent.
        
        Args:
            api_key: Google API key for Gemini access
            prompt_loader: Optional custom prompt loader
            post_parser: Optional custom post parser
        """
        self.api_key = api_key
        self.config = DEFAULT_CONFIG
        
        # Initialize components
        self.prompt_loader = prompt_loader or PromptLoader()
        self.post_parser = post_parser or PostParser()
        
        # Initialize Google GenAI client for search grounding
        self.genai_client = genai.Client(api_key=api_key) if api_key else None
        
        # Initialize Gemini model for general tasks via Langchain
        self.llm = self._create_llm() if api_key else None
        
        logger.info("LinkedInPostAgent initialized")
    
    def _create_llm(self) -> ChatGoogleGenerativeAI:
        """Create and configure the LLM instance."""
        return ChatGoogleGenerativeAI(
            model=self.config.model.llm_model,
            google_api_key=self.api_key,
            temperature=self.config.model.llm_temperature,
            convert_system_message_to_human=True,
        )
    
    async def _search_with_gemini(self, query: str) -> str:
        """
        Perform web search using Gemini's Google Search grounding.
        
        Args:
            query: The search query to execute.
            
        Returns:
            Search results as formatted text.
        """
        if not self.genai_client:
            return "API key not configured. Unable to perform web search."
        
        try:
            response = await asyncio.to_thread(
                self.genai_client.models.generate_content,
                model=self.config.model.search_model,
                contents=f"Search for the latest information about: {query}. "
                        f"Provide concise, factual information with recent developments.",
                config=types.GenerateContentConfig(
                    tools=[types.Tool(google_search=types.GoogleSearch())],
                )
            )
            return response.text
        except Exception as e:
            logger.warning(f"Search error for query '{query}': {e}")
            return f"Search completed with limited results: {str(e)}"
    
    def _build_search_query(self, template: str, **kwargs) -> str:
        """Build a search query from template and parameters."""
        return template.format(**kwargs)
    
    async def get_trending_topics(self, field: str) -> str:
        """
        Get trending topics for a specific field.
        
        Args:
            field: The professional field to analyze.
            
        Returns:
            Formatted string with trending topics.
        """
        if not self.llm:
            return "Configure GOOGLE_API_KEY to get trending topics"
        
        # Search for trending topics
        search_query = self._build_search_query(
            self.config.search.trending_query_template,
            field=field
        )
        search_results = await self._search_with_gemini(search_query)
        
        # Analyze and format topics
        template = self.prompt_loader.get_template("trending_topics")
        chain = template | self.llm | StrOutputParser()
        
        result = await chain.ainvoke({
            "field": field,
            "context": f"Recent search findings:\n{search_results}"
        })
        
        return result
    
    async def generate_posts_stream(
        self, 
        field: str, 
        additional_context: str = ""
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Generate LinkedIn posts with streaming updates.
        
        Yields events for each stage of the generation process:
        - trending: Identifying trending topics
        - research: Conducting deep research
        - generation: Creating post variations
        
        Args:
            field: The professional field to create content for.
            additional_context: Optional additional context or requirements.
            
        Yields:
            Dictionary events with type, message, and optional data.
        """
        if not self.llm:
            yield AgentEvent.error_event(
                "GOOGLE_API_KEY not configured. Please set the environment variable."
            ).to_dict()
            return
        
        try:
            # Stage 1: Identify trending topics
            async for event in self._stage_trending(field, additional_context):
                yield event
            
            # Store trending topics from the last result event
            trending_topics = self._last_stage_data.get("topics", "")
            
            # Stage 2: Deep research
            async for event in self._stage_research(
                field, trending_topics, additional_context
            ):
                yield event
            
            # Store research report
            research_report = self._last_stage_data.get("report", "")
            
            # Stage 3: Generate posts
            async for event in self._stage_generation(field, research_report):
                yield event
            
            # Final completion
            yield AgentEvent.complete_event(
                "🎉 All done! Review your posts below."
            ).to_dict()
            
        except Exception as e:
            logger.exception("Error during post generation")
            yield AgentEvent.error_event(f"An error occurred: {str(e)}").to_dict()
    
    async def _stage_trending(
        self, 
        field: str, 
        additional_context: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Execute the trending topics identification stage."""
        self._last_stage_data = {}
        
        yield AgentEvent.stage_event(
            Stage.TRENDING,
            "🔍 Identifying trending topics in your field..."
        ).to_dict()
        
        # Build and execute search
        search_query = self._build_search_query(
            self.config.search.trending_query_template,
            field=field
        )
        
        yield AgentEvent.progress_event(f"Searching for: {search_query}").to_dict()
        
        search_results = await self._search_with_gemini(search_query)
        
        yield AgentEvent.progress_event("Analyzing search results...").to_dict()
        
        # Analyze trending topics
        template = self.prompt_loader.get_template("trending_topics")
        chain = template | self.llm | StrOutputParser()
        
        trending_topics = await chain.ainvoke({
            "field": field,
            "context": f"{additional_context}\n\nRecent findings:\n{search_results}"
        })
        
        self._last_stage_data = {"topics": trending_topics}
        
        yield AgentEvent.result_event(
            Stage.TRENDING,
            "✅ Trending topics identified!",
            {"topics": trending_topics}
        ).to_dict()
    
    async def _stage_research(
        self, 
        field: str,
        trending_topics: str,
        additional_context: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Execute the deep research stage."""
        self._last_stage_data = {}
        
        yield AgentEvent.stage_event(
            Stage.RESEARCH,
            "📚 Conducting deep research on trending topics..."
        ).to_dict()
        
        # Build research queries
        research_queries = [
            self._build_search_query(q, field=field)
            for q in self.config.search.research_queries
        ]
        
        # Log research queries
        for i, query in enumerate(research_queries, 1):
            yield AgentEvent.progress_event(
                f"Research query {i}/{len(research_queries)}: {query}"
            ).to_dict()
        
        # Execute searches in parallel
        search_tasks = [self._search_with_gemini(q) for q in research_queries]
        research_results = await asyncio.gather(*search_tasks)
        
        yield AgentEvent.progress_event("Compiling research report...").to_dict()
        
        # Compile research report
        combined_research = "\n\n".join(research_results)
        
        template = self.prompt_loader.get_template("research_report")
        chain = template | self.llm | StrOutputParser()
        
        # Extract first topic as main focus
        first_topic = trending_topics.split('\n')[0] if trending_topics else field
        
        research_report = await chain.ainvoke({
            "topic": first_topic,
            "field": field,
            "context": f"{additional_context}\n\nResearch findings:\n{combined_research}"
        })
        
        self._last_stage_data = {"report": research_report}
        
        yield AgentEvent.result_event(
            Stage.RESEARCH,
            "✅ Research report compiled!",
            {"report": research_report}
        ).to_dict()
    
    async def _stage_generation(
        self, 
        field: str,
        research_report: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Execute the post generation stage."""
        self._last_stage_data = {}
        
        yield AgentEvent.stage_event(
            Stage.GENERATION,
            "✍️ Crafting LinkedIn post options..."
        ).to_dict()
        
        yield AgentEvent.progress_event(
            "Generating 3 unique post variations..."
        ).to_dict()
        
        # Generate posts
        template = self.prompt_loader.get_template("post_generation")
        chain = template | self.llm | StrOutputParser()
        
        raw_posts = await chain.ainvoke({
            "report": research_report,
            "field": field
        })
        
        # Parse posts into structured format
        parsed_posts = self.post_parser.parse(raw_posts)
        post_list = [post.to_dict() for post in parsed_posts]
        
        self._last_stage_data = {"posts": post_list, "raw_posts": raw_posts}
        
        yield AgentEvent.result_event(
            Stage.GENERATION,
            "✅ LinkedIn posts generated!",
            {"posts": post_list, "raw_posts": raw_posts}
        ).to_dict()
    
    async def refine_post(self, post_content: str, feedback: str) -> str:
        """
        Refine a post based on user feedback.
        
        Args:
            post_content: The original post content to refine.
            feedback: User feedback describing desired changes.
            
        Returns:
            The refined post content.
        """
        if not self.llm:
            return "Configure GOOGLE_API_KEY to refine posts"
        
        template = self.prompt_loader.get_template("refinement")
        chain = template | self.llm | StrOutputParser()
        
        refined = await chain.ainvoke({
            "post": post_content,
            "feedback": feedback
        })
        
        return refined
