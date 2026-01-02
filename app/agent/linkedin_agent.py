"""
LinkedIn Post Generator Agent using Langchain and Gemini 2.5 Flash
"""
import asyncio
from typing import AsyncGenerator, List, Dict, Any, Optional
from dataclasses import dataclass

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from google import genai
from google.genai import types


@dataclass
class AgentEvent:
    """Event emitted during agent execution"""
    type: str
    message: str
    data: Optional[Dict[str, Any]] = None


class LinkedInPostAgent:
    """
    AI Agent for generating professional LinkedIn posts.
    Uses Gemini 2.5 Flash with Google Search grounding for research.
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        
        # Initialize Google GenAI client for search grounding
        self.genai_client = genai.Client(api_key=api_key) if api_key else None
        
        # Initialize Gemini model for general tasks via Langchain
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=api_key,
            temperature=0.7,
            convert_system_message_to_human=True,
        ) if api_key else None
        
        # Prompts for different stages
        self.trending_prompt = self._create_trending_prompt()
        self.research_prompt = self._create_research_prompt()
        self.post_generation_prompt = self._create_post_prompt()
        self.refinement_prompt = self._create_refinement_prompt()
    
    def _create_trending_prompt(self) -> ChatPromptTemplate:
        """Create prompt for identifying trending topics"""
        return ChatPromptTemplate.from_messages([
            ("system", """You are an expert trend analyst specializing in professional industries and LinkedIn content.
Your task is to identify the top 5 trending topics in the given field that would make excellent LinkedIn posts.

Focus on:
- Recent developments and news
- Industry shifts and transformations
- Emerging technologies or methodologies
- Professional development opportunities
- Thought leadership angles

Return the topics as a numbered list with brief explanations of why each is trending."""),
            ("human", "Identify the top 5 trending topics in the field of: {field}\n\nAdditional context: {context}")
        ])
    
    def _create_research_prompt(self) -> ChatPromptTemplate:
        """Create prompt for deep research"""
        return ChatPromptTemplate.from_messages([
            ("system", """You are a professional research analyst creating comprehensive research reports.
Your task is to compile a detailed yet concise research report on the given topic.

The report should include:
1. **Overview**: Brief introduction to the topic
2. **Key Insights**: 3-5 main findings or developments
3. **Statistics & Data**: Relevant numbers and metrics (if available)
4. **Expert Perspectives**: Notable opinions or quotes from industry leaders
5. **Implications**: What this means for professionals in the field
6. **Action Items**: Practical takeaways

Keep the report focused and actionable, suitable for creating LinkedIn content."""),
            ("human", "Create a research report on: {topic}\n\nField: {field}\nAdditional context: {context}")
        ])
    
    def _create_post_prompt(self) -> ChatPromptTemplate:
        """Create prompt for LinkedIn post generation"""
        return ChatPromptTemplate.from_messages([
            ("system", """You are an expert LinkedIn content creator known for crafting engaging, professional posts.

Create 3 distinct LinkedIn post options based on the research report provided. Each post should:

1. **Hook**: Start with an attention-grabbing opening line
2. **Value**: Provide genuine insights or takeaways
3. **Engagement**: Include a call-to-action or thought-provoking question
4. **Format**: Use appropriate line breaks, emojis (sparingly), and formatting

Post Styles to create:
- **Post 1 - Storytelling**: Personal narrative approach connecting to the topic
- **Post 2 - Data-Driven**: Lead with statistics and insights
- **Post 3 - Thought Leadership**: Bold perspective or contrarian view

Each post should be 150-300 words, optimized for LinkedIn's algorithm and engagement.

Format each post clearly with "--- POST 1 ---", "--- POST 2 ---", "--- POST 3 ---" headers."""),
            ("human", "Research Report:\n{report}\n\nField: {field}\nTarget Audience: Professionals in {field}")
        ])
    
    def _create_refinement_prompt(self) -> ChatPromptTemplate:
        """Create prompt for post refinement"""
        return ChatPromptTemplate.from_messages([
            ("system", """You are a LinkedIn content optimization expert.
Refine the given post based on user feedback while maintaining professional quality.

Ensure the refined post:
- Addresses all feedback points
- Maintains engaging structure
- Keeps appropriate length (150-300 words)
- Preserves the core message and value"""),
            ("human", "Original Post:\n{post}\n\nUser Feedback:\n{feedback}\n\nPlease refine the post accordingly.")
        ])

    async def _search_with_gemini(self, query: str) -> str:
        """
        Perform web search using Gemini's Google Search grounding.
        Uses the google.genai SDK for search grounding.
        """
        if not self.genai_client:
            return "API key not configured. Unable to perform web search."
        
        try:
            # Use Gemini with Google Search grounding via new SDK
            response = await asyncio.to_thread(
                self.genai_client.models.generate_content,
                model="gemini-2.0-flash",
                contents=f"Search for the latest information about: {query}. Provide concise, factual information with recent developments.",
                config=types.GenerateContentConfig(
                    tools=[types.Tool(google_search=types.GoogleSearch())],
                )
            )
            
            return response.text
        except Exception as e:
            return f"Search completed with limited results: {str(e)}"

    async def get_trending_topics(self, field: str) -> List[str]:
        """Get trending topics for a specific field"""
        if not self.llm:
            return ["Configure GOOGLE_API_KEY to get trending topics"]
        
        # First, search for trending topics using Gemini with search grounding
        search_query = f"trending topics {field} 2024 2025 latest news developments"
        search_results = await self._search_with_gemini(search_query)
        
        # Then analyze and format the topics
        chain = self.trending_prompt | self.llm | StrOutputParser()
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
        Yields events for each stage of the process.
        """
        if not self.llm:
            yield {
                "type": "error",
                "message": "GOOGLE_API_KEY not configured. Please set the environment variable."
            }
            return
        
        try:
            # Stage 1: Identify trending topics
            yield {
                "type": "stage",
                "stage": "trending",
                "message": "🔍 Identifying trending topics in your field..."
            }
            
            # Search for trending topics
            search_query = f"trending topics {field} 2024 2025 latest developments news"
            yield {
                "type": "progress",
                "message": f"Searching for: {search_query}"
            }
            
            search_results = await self._search_with_gemini(search_query)
            
            yield {
                "type": "progress",
                "message": "Analyzing search results..."
            }
            
            # Analyze trending topics
            chain = self.trending_prompt | self.llm | StrOutputParser()
            trending_topics = await chain.ainvoke({
                "field": field,
                "context": f"{additional_context}\n\nRecent findings:\n{search_results}"
            })
            
            yield {
                "type": "result",
                "stage": "trending",
                "message": "✅ Trending topics identified!",
                "data": {"topics": trending_topics}
            }
            
            # Stage 2: Deep research on the top topic
            yield {
                "type": "stage",
                "stage": "research",
                "message": "📚 Conducting deep research on trending topics..."
            }
            
            # Perform additional research searches
            research_queries = [
                f"{field} industry trends statistics 2024 2025",
                f"{field} expert opinions thought leadership",
                f"{field} case studies success stories"
            ]
            
            # Parallelize search requests
            search_tasks = [self._search_with_gemini(q) for q in research_queries]
            
            for i, query in enumerate(research_queries):
                yield {
                    "type": "progress",
                    "message": f"Research query {i+1}/3: {query}"
                }
            
            research_results = await asyncio.gather(*search_tasks)
            research_data = list(research_results)
            
            yield {
                "type": "progress",
                "message": "Compiling research report..."
            }
            
            # Compile research report
            combined_research = "\n\n".join(research_data)
            
            # Clear individual results to save memory
            del research_results
            del research_data
            
            research_chain = self.research_prompt | self.llm | StrOutputParser()
            research_report = await research_chain.ainvoke({
                "topic": trending_topics.split('\n')[0] if trending_topics else field,
                "field": field,
                "context": f"{additional_context}\n\nResearch findings:\n{combined_research}"
            })
            
            # Clear large combined content
            del combined_research
            
            yield {
                "type": "result",
                "stage": "research",
                "message": "✅ Research report compiled!",
                "data": {"report": research_report}
            }
            
            # Stage 3: Generate LinkedIn posts
            yield {
                "type": "stage",
                "stage": "generation",
                "message": "✍️ Crafting LinkedIn post options..."
            }
            
            yield {
                "type": "progress",
                "message": "Generating 3 unique post variations..."
            }
            
            post_chain = self.post_generation_prompt | self.llm | StrOutputParser()
            posts = await post_chain.ainvoke({
                "report": research_report,
                "field": field
            })
            
            # Parse posts into separate entries
            post_list = self._parse_posts(posts)
            
            yield {
                "type": "result",
                "stage": "generation",
                "message": "✅ LinkedIn posts generated!",
                "data": {"posts": post_list, "raw_posts": posts}
            }
            
            # Final completion - Lightweight event
            yield {
                "type": "complete",
                "message": "🎉 All done! Review your posts below.",
                "data": {} # Data already sent in previous events to save bandwidth
            }
            
        except Exception as e:
            yield {
                "type": "error",
                "message": f"An error occurred: {str(e)}"
            }

    def _parse_posts(self, raw_posts: str) -> List[Dict[str, str]]:
        """Parse the generated posts into a structured list"""
        posts = []
        
        # Try to split by post markers
        markers = ["--- POST 1 ---", "--- POST 2 ---", "--- POST 3 ---"]
        current_content = raw_posts
        
        for i, marker in enumerate(markers):
            if marker in current_content:
                parts = current_content.split(marker, 1)
                if len(parts) > 1:
                    current_content = parts[1]
            
        # Fallback: split by common patterns
        import re
        post_pattern = r'(?:---\s*POST\s*\d+\s*---|Post\s*\d+[:\-]|#\s*Post\s*\d+)'
        split_posts = re.split(post_pattern, raw_posts, flags=re.IGNORECASE)
        
        # Filter and clean posts
        for i, post in enumerate(split_posts):
            cleaned = post.strip()
            if cleaned and len(cleaned) > 50:  # Minimum length check
                style = ["Storytelling", "Data-Driven", "Thought Leadership"][min(i, 2)] if i < 3 else f"Variation {i+1}"
                posts.append({
                    "id": i + 1,
                    "style": style,
                    "content": cleaned
                })
        
        # If parsing failed, return the whole thing as one post
        if not posts:
            posts.append({
                "id": 1,
                "style": "Generated",
                "content": raw_posts.strip()
            })
        
        return posts[:3]  # Return max 3 posts

    async def refine_post(self, post_content: str, feedback: str) -> str:
        """Refine a post based on user feedback"""
        if not self.llm:
            return "Configure GOOGLE_API_KEY to refine posts"
        
        chain = self.refinement_prompt | self.llm | StrOutputParser()
        refined = await chain.ainvoke({
            "post": post_content,
            "feedback": feedback
        })
        
        return refined

