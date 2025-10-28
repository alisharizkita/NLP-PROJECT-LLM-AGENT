from groq import Groq
from src.config import Config
from typing import List, Dict, Optional
import logging
import json

logger = logging.getLogger(__name__)

class GroqClient:
    """Groq API client for LLM interactions"""
    
    def __init__(self):
        self.client = Groq(api_key=Config.GROQ_API_KEY)
        self.model = Config.GROQ_MODEL
        logger.info(f"Initialized Groq client with model: {self.model}")
    
    def chat(self, messages: List[Dict[str, str]], 
             tools: Optional[List[Dict]] = None,
             temperature: float = 0.7,
             max_tokens: int = 1024) -> Dict:
        """
        Send chat completion request to Groq
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            tools: Optional list of tool definitions for function calling
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens in response
            
        Returns:
            Dict containing the response message
        """
        try:
            params = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            if tools:
                params["tools"] = tools
                params["tool_choice"] = "auto"
            
            response = self.client.chat.completions.create(**params)
            
            message = response.choices[0].message
            
            # Log the interaction
            logger.debug(f"LLM Request: {messages[-1]['content'][:100]}...")
            logger.debug(f"LLM Response: {message.content[:100] if message.content else 'Function call'}...")
            
            return {
                "content": message.content,
                "tool_calls": message.tool_calls if hasattr(message, 'tool_calls') else None,
                "role": message.role
            }
            
        except Exception as e:
            logger.error(f"Error calling Groq API: {e}")
            return {
                "content": "Maaf, terjadi kesalahan saat memproses permintaan kamu. Coba lagi ya!",
                "tool_calls": None,
                "role": "assistant"
            }
    
    def chat_stream(self, messages: List[Dict[str, str]], 
                    temperature: float = 0.7,
                    max_tokens: int = 1024):
        """
        Stream chat completion response
        
        Args:
            messages: List of message dicts
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            
        Yields:
            Chunks of the response
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )
            
            for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"Error streaming from Groq API: {e}")
            yield "Maaf, terjadi kesalahan saat streaming response."