"""
LLM client wrapper for Appaveli CodeMind
"""


import os
import logging
import sys
from pathlib import Path


root_path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_path))

from appaveli_codemind.bootstrap import *
from typing import Dict, List, Optional, Any
from openai import OpenAI


logger = logging.getLogger(__name__)


class OpenAIClient:
    """Wrapper for OpenAI API client with CodeMind-specific functionality"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OpenAI client
        
        Args:
            api_key: OpenAI API key (if not provided, uses environment variable)
        """
        self.api_key = api_key or  os.getenv('OPENAI_API_KEY')

        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        self.client = OpenAI(api_key=self.api_key)
        self.default_model = os.getenv('OPENAI_MODEL', 'gpt-4o')
        self.max_tokens = int(os.getenv('OPENAI_MAX_TOKENS', '4000'))
        
        logger.info(f"Initialized OpenAI client with model: {self.default_model}")
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a chat completion
        
        Args:
            messages: List of message dictionaries
            model: Model to use (defaults to configured model)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters
            
        Returns:
            API response dictionary
        """
        try:
            response = self.client.chat.completions.create(
                model=model or self.default_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens or self.max_tokens,
                **kwargs
            )
            
            return {
                'content': response.choices[0].message.content,
                'usage': response.usage.dict() if response.usage else {},
                'model': response.model,
                'finish_reason': response.choices[0].finish_reason
            }
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    def estimate_cost(self, tokens: int, model: Optional[str] = None) -> float:
        """
        Estimate cost for token usage
        
        Args:
            tokens: Number of tokens
            model: Model used
            
        Returns:
            Estimated cost in USD
        """
        model = model or self.default_model
        
        # Rough pricing estimates
        pricing = {
            'gpt-4o': 0.005,  # $5 per 1M tokens
            'gpt-4o-mini': 0.0015,  # $1.50 per 1M tokens
            'gpt-4': 0.03,  # $30 per 1M tokens
        }
        
        rate = pricing.get(model, 0.005)  # Default to gpt-4o pricing
        return (tokens / 1_000_000) * rate