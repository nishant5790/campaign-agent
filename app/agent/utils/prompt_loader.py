"""
Prompt Loader for the LinkedIn Post Generator Agent.

This module handles loading prompts from YAML files and converting them
to LangChain ChatPromptTemplate objects.
"""
import logging
from pathlib import Path
from typing import Dict, Any, Optional

import yaml
from langchain_core.prompts import ChatPromptTemplate

from ..resources.config import DEFAULT_CONFIG

logger = logging.getLogger(__name__)


class PromptLoader:
    """
    Loads and manages prompts from YAML configuration files.
    
    Provides methods to load prompts and convert them to LangChain
    ChatPromptTemplate objects for use with LLM chains.
    """
    
    def __init__(self, prompts_file: Optional[str] = None):
        """
        Initialize the PromptLoader.
        
        Args:
            prompts_file: Path to the YAML prompts file. If None, uses default
                         from config relative to the resources directory.
        """
        if prompts_file is None:
            # Default to prompts.yml in the resources directory
            resources_dir = Path(__file__).parent.parent / "resources"
            prompts_file = resources_dir / DEFAULT_CONFIG.prompts_file
        
        self.prompts_path = Path(prompts_file)
        self._prompts_cache: Optional[Dict[str, Any]] = None
        self._templates_cache: Dict[str, ChatPromptTemplate] = {}
    
    def _load_prompts(self) -> Dict[str, Any]:
        """
        Load prompts from YAML file.
        
        Returns:
            Dictionary containing all prompt configurations.
            
        Raises:
            FileNotFoundError: If prompts file doesn't exist.
            yaml.YAMLError: If YAML parsing fails.
        """
        if self._prompts_cache is not None:
            return self._prompts_cache
        
        if not self.prompts_path.exists():
            raise FileNotFoundError(
                f"Prompts file not found: {self.prompts_path}"
            )
        
        logger.info(f"Loading prompts from {self.prompts_path}")
        
        with open(self.prompts_path, 'r', encoding='utf-8') as f:
            self._prompts_cache = yaml.safe_load(f)
        
        return self._prompts_cache
    
    def get_prompt(self, prompt_name: str) -> Dict[str, str]:
        """
        Get raw prompt data by name.
        
        Args:
            prompt_name: Name of the prompt (e.g., 'trending_topics', 'research_report')
            
        Returns:
            Dictionary with 'system' and 'human' keys containing prompt text.
            
        Raises:
            KeyError: If prompt name doesn't exist.
        """
        prompts = self._load_prompts()
        
        if prompt_name not in prompts:
            available = list(prompts.keys())
            raise KeyError(
                f"Prompt '{prompt_name}' not found. Available prompts: {available}"
            )
        
        return prompts[prompt_name]
    
    def get_template(self, prompt_name: str) -> ChatPromptTemplate:
        """
        Get a ChatPromptTemplate for the specified prompt.
        
        Templates are cached after first creation for efficiency.
        
        Args:
            prompt_name: Name of the prompt to load.
            
        Returns:
            ChatPromptTemplate ready for use with LangChain.
        """
        if prompt_name in self._templates_cache:
            return self._templates_cache[prompt_name]
        
        prompt_data = self.get_prompt(prompt_name)
        
        # Create ChatPromptTemplate from system and human messages
        template = ChatPromptTemplate.from_messages([
            ("system", prompt_data["system"].strip()),
            ("human", prompt_data["human"].strip()),
        ])
        
        self._templates_cache[prompt_name] = template
        logger.debug(f"Created template for prompt: {prompt_name}")
        
        return template
    
    def get_all_templates(self) -> Dict[str, ChatPromptTemplate]:
        """
        Load and return all available prompt templates.
        
        Returns:
            Dictionary mapping prompt names to ChatPromptTemplate objects.
        """
        prompts = self._load_prompts()
        
        return {
            name: self.get_template(name)
            for name in prompts.keys()
            if isinstance(prompts[name], dict) and 'system' in prompts[name]
        }
    
    def reload(self) -> None:
        """
        Clear caches and reload prompts from file.
        
        Useful for development when prompts are being modified.
        """
        self._prompts_cache = None
        self._templates_cache.clear()
        logger.info("Prompt cache cleared, will reload on next access")
    
    def list_prompts(self) -> list:
        """
        List all available prompt names.
        
        Returns:
            List of prompt names available in the YAML file.
        """
        prompts = self._load_prompts()
        return [
            name for name, data in prompts.items()
            if isinstance(data, dict) and 'system' in data
        ]


# Default loader instance
_default_loader: Optional[PromptLoader] = None


def get_prompt_loader() -> PromptLoader:
    """
    Get the default PromptLoader instance.
    
    Creates the loader on first call (singleton pattern).
    
    Returns:
        The default PromptLoader instance.
    """
    global _default_loader
    if _default_loader is None:
        _default_loader = PromptLoader()
    return _default_loader
