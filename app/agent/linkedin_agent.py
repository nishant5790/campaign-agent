"""
LinkedIn Post Generator Agent using Langchain and Gemini 2.5 Flash.

This module provides the main agent class that orchestrates the generation
of LinkedIn posts through conversational chat, plan approval, trending topic
discovery, research, and content creation.
"""
import asyncio
import logging
import re
from typing import AsyncGenerator, Dict, Any, Optional

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from google import genai
from google.genai import types

from .resources.config import DEFAULT_CONFIG, Stage
from .utils.models import AgentEvent
from .utils.prompt_loader import PromptLoader
from .utils.post_parser import PostParser
from .chat_session import ChatSession

logger = logging.getLogger(__name__)

# Regex to detect embedded [PLAN_READY]...[END_PLAN] blocks (legacy - kept as fallback)
PLAN_PATTERN = re.compile(
    r'(?:\*\*|\[)?\s*PLAN_READY\s*(?:\]|\*\*)?\s*(.*?)\s*(?:\*\*|\[)?\s*END_PLAN\s*(?:\]|\*\*)?',
    re.DOTALL | re.IGNORECASE
)

# Detect AI intent to present a plan (the AI says it's ready but forgets markers)
PLAN_INTENT_PATTERN = re.compile(
    r"(here'?s?\s+(a|the|my)\s+(content\s+)?plan|proposed\s+plan|content\s+plan\s+for|plan\s+for\s+your|i\s+have\s+(a|enough|all)\s+.{0,30}(plan|information)|plan\s+tailored)",
    re.IGNORECASE
)


class LinkedInPostAgent:
    """
    AI Agent for generating professional LinkedIn posts.
    
    Uses Gemini 2.5 Flash with Google Search grounding for research
    and LangChain for prompt orchestration. Supports conversational
    chat to gather user requirements before generating posts.
    
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

    # ─── Chat & Plan Methods ─────────────────────────────────────

    async def chat(self, session: ChatSession, user_message: str) -> Dict[str, Any]:
        """
        Process a user message in the conversational flow.
        
        Uses a 2-step approach:
        1. Run the conversational LLM to get the chat response.
        2. If the response signals plan-readiness (via markers OR intent keywords),
           immediately fire a dedicated plan_generation LLM call to get a clean,
           structured plan — rather than relying on the chat LLM to self-embed markers.
        """
        if not self.llm:
            return {
                "response": "GOOGLE_API_KEY not configured.",
                "plan": None,
                "status": "error",
            }

        # Add user message to history
        session.add_user_message(user_message)

        # Build messages for the LLM
        messages = self._build_chat_messages(session)

        try:
            result = await self.llm.ainvoke(messages)
            ai_text = result.content
        except Exception as e:
            logger.exception("Chat LLM error")
            return {
                "response": f"Sorry, I ran into an issue: {str(e)}",
                "plan": None,
                "status": "error",
            }

        logger.info("Chat AI raw output (first 300 chars): %s", ai_text[:300])

        # --- Strategy 1: Embedded [PLAN_READY]...[END_PLAN] markers (ideal case) ---
        plan_match = PLAN_PATTERN.search(ai_text)
        if plan_match:
            plan_text = plan_match.group(1).strip()
            conversational_text = PLAN_PATTERN.sub("", ai_text).strip()
            if not conversational_text:
                conversational_text = "Here's my proposed plan for your LinkedIn post. Please review it and let me know if you'd like to approve or adjust anything! 👇"

            session.add_ai_message(conversational_text)
            session.set_plan(plan_text)
            self._extract_context_from_plan(session, plan_text)
            logger.info("Plan detected via PLAN_PATTERN markers.")

            return {
                "response": conversational_text,
                "plan": plan_text,
                "status": "plan_pending",
            }

        # --- Strategy 2: Intent detection — AI says it has a plan but forgot markers ---
        intent_match = PLAN_INTENT_PATTERN.search(ai_text)
        if intent_match:
            logger.info("Plan intent detected in AI response; generating structured plan...")

            # Build conversation context summary for plan generation
            conversation_context = self._build_context_summary(session)

            try:
                plan_text = await self._generate_structured_plan(conversation_context)
            except Exception as e:
                logger.exception("Plan generation step failed")
                # Fall back to treating this as a normal chat turn
                session.add_ai_message(ai_text)
                return {"response": ai_text, "plan": None, "status": "chatting"}

            # Strip everything after the intent phrase from the AI text so we only
            # keep the conversational warm-up before the (now-missing) plan text.
            conversational_text = ai_text.strip()

            session.add_ai_message(conversational_text)
            session.set_plan(plan_text)
            self._extract_context_from_plan(session, plan_text)

            return {
                "response": conversational_text,
                "plan": plan_text,
                "status": "plan_pending",
            }

        # --- Normal chat turn ---
        session.add_ai_message(ai_text)
        return {
            "response": ai_text,
            "plan": None,
            "status": "chatting",
        }

    def _build_chat_messages(self, session: ChatSession) -> list:
        """Build the message list for the chat LLM call."""
        # Load the chat system prompt
        chat_prompt_data = self.prompt_loader.get_prompt("chat_system")
        system_text = chat_prompt_data["system"].strip()

        messages = [SystemMessage(content=system_text)]

        # Add conversation history
        for role, content in session.chat_history:
            if role == "human":
                messages.append(HumanMessage(content=content))
            elif role == "ai":
                messages.append(AIMessage(content=content))

        return messages

    def _extract_context_from_plan(self, session: ChatSession, plan_text: str) -> None:
        """
        Extract structured context from the plan text and conversation.
        
        Parses the plan to find topic, tone, audience etc.
        """
        ctx = session.user_context

        # Extract from plan text using simple pattern matching
        lines = plan_text.lower()
        
        # Try to extract topic focus
        topic_match = re.search(r'topic\s*focus:\s*(.+)', plan_text, re.IGNORECASE)
        if topic_match:
            ctx["topic"] = topic_match.group(1).strip()
            ctx["field"] = topic_match.group(1).strip()

        tone_match = re.search(r'tone:\s*(.+)', plan_text, re.IGNORECASE)
        if tone_match:
            ctx["tone"] = tone_match.group(1).strip()

        audience_match = re.search(r'target\s*audience:\s*(.+)', plan_text, re.IGNORECASE)
        if audience_match:
            ctx["audience"] = audience_match.group(1).strip()

        # If field not found from plan, try to infer from conversation
        if "field" not in ctx:
            # Use the first user message as a hint for the field
            user_messages = [c for r, c in session.chat_history if r == "human"]
            if user_messages:
                ctx["field"] = user_messages[0][:100]

    def _build_context_summary(self, session: ChatSession) -> str:
        """Build a readable conversation summary for the plan generation prompt."""
        lines = []
        for role, content in session.chat_history:
            label = "User" if role == "human" else "Assistant"
            lines.append(f"{label}: {content[:500]}")
        return "\n".join(lines)

    async def _generate_structured_plan(self, conversation_context: str) -> str:
        """
        Fire a dedicated second LLM call using the plan_generation prompt
        to get a clean, structured plan from the accumulated conversation context.
        """
        plan_prompt_data = self.prompt_loader.get_prompt("plan_generation")
        system_text = plan_prompt_data["system"].strip()
        human_template = plan_prompt_data.get("human", "User Context:\n{context}\n\nCreate a research and content plan for their LinkedIn post.")
        human_text = human_template.format(context=conversation_context)

        messages = [
            SystemMessage(content=system_text),
            HumanMessage(content=human_text),
        ]
        result = await self.llm.ainvoke(messages)
        return result.content.strip()

    # ─── Web Search ──────────────────────────────────────────────

    async def _search_with_gemini(self, query: str) -> str:
        """
        Perform web search using Gemini's Google Search grounding.
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
        """Get trending topics for a specific field."""
        if not self.llm:
            return "Configure GOOGLE_API_KEY to get trending topics"
        
        search_query = self._build_search_query(
            self.config.search.trending_query_template,
            field=field
        )
        search_results = await self._search_with_gemini(search_query)
        
        template = self.prompt_loader.get_template("trending_topics")
        chain = template | self.llm | StrOutputParser()
        
        result = await chain.ainvoke({
            "field": field,
            "context": f"Recent search findings:\n{search_results}"
        })
        
        return result

    # ─── Streaming Pipeline ──────────────────────────────────────

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
            
            trending_topics = self._last_stage_data.get("topics", "")
            
            # Stage 2: Deep research
            async for event in self._stage_research(
                field, trending_topics, additional_context
            ):
                yield event
            
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

    async def generate_posts_from_session(
        self,
        session: ChatSession
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Generate posts using context extracted from a chat session.
        
        This is the entry point after a plan is approved.
        """
        field = session.get_field()
        additional_context = session.get_additional_context()

        # Include the plan as additional context
        if session.plan:
            additional_context += f"\n\nApproved Content Plan:\n{session.plan}"

        session.status = "executing"

        async for event in self.generate_posts_stream(field, additional_context):
            yield event

        session.status = "done"
    
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
        
        search_query = self._build_search_query(
            self.config.search.trending_query_template,
            field=field
        )
        
        yield AgentEvent.progress_event(f"Searching for: {search_query}").to_dict()
        
        search_results = await self._search_with_gemini(search_query)
        
        yield AgentEvent.progress_event("Analyzing search results...").to_dict()
        
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
        
        research_queries = [
            self._build_search_query(q, field=field)
            for q in self.config.search.research_queries
        ]
        
        for i, query in enumerate(research_queries, 1):
            yield AgentEvent.progress_event(
                f"Research query {i}/{len(research_queries)}: {query}"
            ).to_dict()
        
        search_tasks = [self._search_with_gemini(q) for q in research_queries]
        research_results = await asyncio.gather(*search_tasks)
        
        yield AgentEvent.progress_event("Compiling research report...").to_dict()
        
        combined_research = "\n\n".join(research_results)
        
        template = self.prompt_loader.get_template("research_report")
        chain = template | self.llm | StrOutputParser()
        
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
        
        template = self.prompt_loader.get_template("post_generation")
        chain = template | self.llm | StrOutputParser()
        
        raw_posts = await chain.ainvoke({
            "report": research_report,
            "field": field
        })
        
        parsed_posts = self.post_parser.parse(raw_posts)
        post_list = [post.to_dict() for post in parsed_posts]
        
        self._last_stage_data = {"posts": post_list, "raw_posts": raw_posts}
        
        yield AgentEvent.result_event(
            Stage.GENERATION,
            "✅ LinkedIn posts generated!",
            {"posts": post_list, "raw_posts": raw_posts}
        ).to_dict()
    
    async def refine_post(self, post_content: str, feedback: str) -> str:
        """Refine a post based on user feedback."""
        if not self.llm:
            return "Configure GOOGLE_API_KEY to refine posts"
        
        template = self.prompt_loader.get_template("refinement")
        chain = template | self.llm | StrOutputParser()
        
        refined = await chain.ainvoke({
            "post": post_content,
            "feedback": feedback
        })
        
        return refined
