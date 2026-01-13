"""
Post Parser for the LinkedIn Post Generator Agent.

This module handles parsing and validation of generated LinkedIn posts,
extracting individual posts from the combined LLM output.
"""
import logging
import re
from typing import List

from ..resources.config import DEFAULT_CONFIG, get_compiled_post_pattern
from .models import ParsedPost

logger = logging.getLogger(__name__)


class PostParser:
    """
    Parses raw LLM output into structured LinkedIn posts.
    
    The parser handles various output formats and extracts individual
    posts with their styles and content.
    """
    
    def __init__(self):
        """Initialize the PostParser with configuration."""
        self.config = DEFAULT_CONFIG.post
        self.pattern = get_compiled_post_pattern()
    
    def parse(self, raw_posts: str) -> List[ParsedPost]:
        """
        Parse raw LLM output into structured posts.
        
        Args:
            raw_posts: The raw string output from the LLM containing
                      multiple posts with markers.
                      
        Returns:
            List of ParsedPost objects, maximum of config.max_posts.
        """
        if not raw_posts or not raw_posts.strip():
            logger.warning("Empty input provided to parser")
            return self._fallback_parse(raw_posts)
        
        # Try to split by regex pattern
        split_posts = self.pattern.split(raw_posts)
        
        # Filter and clean posts
        posts = []
        for i, post_content in enumerate(split_posts):
            cleaned = post_content.strip()
            
            # Skip if too short
            if not cleaned or len(cleaned) < self.config.min_post_length:
                continue
            
            # Determine style based on position
            style = self._get_style_for_index(len(posts))
            
            posts.append(ParsedPost(
                id=len(posts) + 1,
                style=style,
                content=cleaned,
            ))
            
            # Stop if we have enough posts
            if len(posts) >= self.config.max_posts:
                break
        
        # If parsing failed, return the whole thing as one post
        if not posts:
            logger.info("Pattern parsing failed, using fallback")
            return self._fallback_parse(raw_posts)
        
        logger.info(f"Successfully parsed {len(posts)} posts")
        return posts
    
    def _get_style_for_index(self, index: int) -> str:
        """
        Get the post style for a given index.
        
        Args:
            index: Zero-based index of the post.
            
        Returns:
            Style name for the post.
        """
        styles = self.config.post_styles
        if index < len(styles):
            return styles[index]
        return f"Variation {index + 1}"
    
    def _fallback_parse(self, raw_posts: str) -> List[ParsedPost]:
        """
        Fallback parsing when pattern matching fails.
        
        Returns the entire content as a single post.
        
        Args:
            raw_posts: The raw post content.
            
        Returns:
            List with a single ParsedPost containing all content.
        """
        content = raw_posts.strip() if raw_posts else ""
        
        if not content:
            return []
        
        return [ParsedPost(
            id=1,
            style="Generated",
            content=content,
        )]
    
    def validate_post(self, post: ParsedPost) -> bool:
        """
        Validate a parsed post meets requirements.
        
        Args:
            post: The ParsedPost to validate.
            
        Returns:
            True if the post is valid, False otherwise.
        """
        if not post.content:
            return False
        
        # Check minimum length
        if len(post.content) < self.config.min_post_length:
            return False
        
        return True
    
    def get_word_count(self, post: ParsedPost) -> int:
        """
        Get the word count for a post.
        
        Args:
            post: The ParsedPost to count words for.
            
        Returns:
            Number of words in the post content.
        """
        if not post.content:
            return 0
        return len(post.content.split())
    
    def is_optimal_length(self, post: ParsedPost) -> bool:
        """
        Check if a post is within the optimal word count range.
        
        Args:
            post: The ParsedPost to check.
            
        Returns:
            True if word count is between min and max configured values.
        """
        word_count = self.get_word_count(post)
        return (
            self.config.min_word_count <= word_count <= self.config.max_word_count
        )


# Module-level parser instance for convenience
_default_parser = None


def get_post_parser() -> PostParser:
    """
    Get the default PostParser instance.
    
    Returns:
        The default PostParser instance (singleton).
    """
    global _default_parser
    if _default_parser is None:
        _default_parser = PostParser()
    return _default_parser


def parse_posts(raw_posts: str) -> List[ParsedPost]:
    """
    Convenience function to parse posts using the default parser.
    
    Args:
        raw_posts: Raw LLM output containing posts.
        
    Returns:
        List of ParsedPost objects.
    """
    return get_post_parser().parse(raw_posts)
