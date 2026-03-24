"""
Anthropic API interface for LLM inference with reasoning support.
"""

import os
from typing import Dict, Any, Optional, List
import anthropic
import logging
from datetime import datetime

from utils.llm_interface_utils import (
    validate_generation_params,
    get_model_defaults,
    estimate_tokens,
    get_model_info,
    supports_thinking
)

logger = logging.getLogger(__name__)

class AnthropicInterface:
    """
    Anthropic API interface for LLM inference with reasoning support.
    """
    
    def __init__(
        self,
        model_name: str,
        enable_thinking: bool = False,
        api_key: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize Anthropic interface.
        
        Args:
            model_name: Name of the Anthropic model
            enable_thinking: Whether to enable reasoning mode
            api_key: Anthropic API key (uses ANTHROPIC_API_KEY env var if None)
            **kwargs: Additional client arguments
        """
        self.model_name = model_name
        self.enable_thinking = enable_thinking
        self.model_info = get_model_info(model_name)
        
        # Check if thinking is supported
        if enable_thinking and not supports_thinking(model_name):
            logger.warning(f"Thinking mode requested but not supported for {model_name}")
            self.enable_thinking = False
        
        # Get API key
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("Anthropic API key not found. Set ANTHROPIC_API_KEY environment variable or pass api_key parameter.")
        
        # Initialize client
        self.client = anthropic.Anthropic(api_key=self.api_key, **kwargs)
        
        # Store configuration
        self.model_config = {
            'model_name': model_name,
            'enable_thinking': self.enable_thinking,
            'provider': 'anthropic',
            'model_info': self.model_info
        }
        
        logger.info(f"Successfully initialized Anthropic interface for {model_name}")
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate text using Anthropic API.
        
        Args:
            prompt: Input prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            top_p: Top-p sampling parameter
            max_tokens: Maximum tokens to generate
            **kwargs: Additional generation parameters
            
        Returns:
            Dictionary containing generation results and metadata
        """
        start_time = datetime.now()
        
        # Get model defaults and validate parameters
        defaults = get_model_defaults(self.model_name)
        generation_params = {
            'temperature': temperature,
            'top_p': top_p if top_p is not None else 1.0,
            'max_tokens': max_tokens,
            **kwargs
        }
        
        # Remove None values and validate
        generation_params = {k: v for k, v in generation_params.items() if v is not None}
        generation_params = validate_generation_params(generation_params)
        
        # Merge with defaults, ensuring top_p defaults to 1.0
        final_params = {**defaults, **generation_params}
        if 'top_p' not in final_params:
            final_params['top_p'] = 1.0
        
        # Prepare messages
        messages = [{"role": "user", "content": prompt}]
        
        # Format prompt for token counting
        formatted_prompt = self._format_messages_for_counting(messages, system_prompt)
        
        try:
            # Prepare API call parameters
            api_params = {
                'model': self.model_name,
                'messages': messages,
                'max_tokens': final_params.get('max_tokens', 512)
            }
            
            # Add system prompt if provided
            if system_prompt:
                api_params['system'] = system_prompt
            
            # Add optional parameters
            if 'temperature' in final_params:
                api_params['temperature'] = final_params['temperature']
            if 'top_p' in final_params:
                api_params['top_p'] = final_params['top_p']
            
            # Enable thinking mode if supported and requested
            if self.enable_thinking and supports_thinking(self.model_name):
                logger.info(f"Generating with reasoning using {self.model_name}")
                # For Claude models, thinking is enabled by default when supported
                # No special parameter needed
            else:
                logger.info(f"Generating with standard completion using {self.model_name}")
            
            # Make API call
            response = self.client.messages.create(**api_params)
            
            # Extract generated text
            generated_text = ""
            reasoning_text = None
            
            for content_block in response.content:
                if content_block.type == "text":
                    generated_text += content_block.text
                elif content_block.type == "thinking":
                    reasoning_text = content_block.content
            
            # Get token usage from response
            usage = response.usage
            token_usage = {
                'input_tokens': usage.input_tokens,
                'output_tokens': usage.output_tokens,
                'total_tokens': usage.input_tokens + usage.output_tokens
            }
            
            # Add reasoning tokens if available
            if reasoning_text:
                reasoning_tokens = estimate_tokens(reasoning_text, self.model_name)
                token_usage['reasoning_tokens'] = reasoning_tokens
                token_usage['total_tokens'] += reasoning_tokens
            
            # Add reasoning to result if available
            additional_data = {'reasoning': reasoning_text} if reasoning_text else {}
            
        except Exception as e:
            logger.error(f"Error generating with Anthropic API: {e}")
            raise
        
        end_time = datetime.now()
        generation_time = (end_time - start_time).total_seconds()
        
        # Prepare result
        result = {
            'input_text': prompt,
            'system_prompt': system_prompt,
            'chat_template_applied': 'anthropic_messages',
            'formatted_prompt': formatted_prompt,
            'output': generated_text,
            'model_config': self.model_config,
            'generation_params': final_params,
            'token_usage': token_usage,
            'generation_time_seconds': generation_time,
            'tokens_per_second': token_usage['output_tokens'] / generation_time if generation_time > 0 else 0,
            'timestamp': start_time.isoformat(),
            **additional_data
        }
        
        logger.info(f"Generated {token_usage['output_tokens']} tokens in {generation_time:.2f}s")
        return result
    
    def _format_messages_for_counting(self, messages: List[Dict[str, str]], system_prompt: Optional[str] = None) -> str:
        """Format messages for token counting."""
        formatted = ""
        if system_prompt:
            formatted += f"system: {system_prompt}\n"
        
        for message in messages:
            role = message.get('role', 'user')
            content = message.get('content', '')
            formatted += f"{role}: {content}\n"
        
        return formatted.strip()
