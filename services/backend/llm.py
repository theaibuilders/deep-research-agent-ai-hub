"""
============================================================================
LLM CLIENT - PYTHON IMPLEMENTATION
============================================================================

This file implements the LLM (Large Language Model) client for Python.
It communicates with OpenAI-compatible APIs like Zeabur AI Hub.

KEY CONCEPTS FOR WORKSHOP:

1. OPENAI-COMPATIBLE API:
   - Standard API format used by many providers
   - POST /v1/chat/completions for chat requests
   - Request: {model, messages, temperature, max_tokens}
   - Response: {choices: [{message: {content}}]}

2. ASYNC HTTP WITH HTTPX:
   - httpx is the modern async HTTP client for Python
   - Similar to axios in JavaScript
   - Supports async/await natively

3. AUTHENTICATION:
   - Bearer token in Authorization header
   - API keys should be stored in environment variables
   - Never hardcode API keys in source code!

4. ERROR HANDLING:
   - HTTP status codes (4xx client errors, 5xx server errors)
   - Network timeouts
   - Invalid response formats

============================================================================
"""

import httpx
import os
from typing import List, Dict, Optional


class ZeaburLLM:
    """
    LLM client for Zeabur AI Hub (OpenAI-compatible API)
    
    This class provides a simple interface to interact with LLMs:
    - generate(): Single prompt to single response
    - chat(): Multi-turn conversation with message history
    
    CONFIGURATION:
    - api_key: Your Zeabur API token
    - base_url: API endpoint (defaults to Zeabur)
    - model: Which model to use (e.g., "gpt-4o-mini")
    """
    
    def __init__(self, api_key: str, model: Optional[str] = None, base_url: Optional[str] = None):
        """
        Initialize the LLM client.
        
        Args:
            api_key: Zeabur API token (required)
            model: Model name (optional, falls back to env var)
            base_url: API base URL (optional, falls back to env var)
        """
        self.api_key = api_key
        
        # URL CONFIGURATION with fallback to environment variable
        # os.getenv() returns the env var or default value
        self.base_url = base_url or os.getenv('ZEABUR_BASE_URL', 'https://sfo1.aihub.zeabur.ai')
        self.base_url = self.base_url.rstrip('/')  # Remove trailing slash
        
        # MODEL CONFIGURATION
        self.model = model or os.getenv('ZEABUR_MODEL', 'gpt-4o-mini')
        
        print(f"🔗 Connecting to Zeabur AI Hub: {self.base_url}")
        print(f"🤖 Using model: {self.model}")

    async def generate(self, prompt: str) -> str:
        """
        Generate a completion from a single prompt.
        
        OPENAI CHAT COMPLETIONS FORMAT:
        Request body structure:
        {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": "..."}],
            "temperature": 0.7,    # Creativity (0-1)
            "max_tokens": 1000,    # Max response length
            "stream": false        # Wait for complete response
        }
        
        Args:
            prompt: The text prompt to send
            
        Returns:
            str: The generated text response
            
        Raises:
            Exception: If API request fails
        """
        url = f"{self.base_url}/v1/chat/completions"
        
        print(f"📤 POST {url}")
        
        try:
            # ASYNC HTTP CLIENT
            # httpx.AsyncClient() creates an async HTTP session
            # "async with" ensures proper cleanup after request
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    url,
                    json={
                        "model": self.model,
                        # For generate(), we wrap the prompt in a single user message
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.7,
                        "max_tokens": 1000,
                        "stream": False  # Get complete response at once
                    },
                    headers={
                        "Content-Type": "application/json",
                        # BEARER TOKEN AUTH: "Bearer <token>"
                        "Authorization": f"Bearer {self.api_key}"
                    }
                )
                
                # Raise exception for 4xx/5xx status codes
                response.raise_for_status()
                
                # Parse JSON response
                data = response.json()
                
                # Extract content from OpenAI response format
                # data.choices[0].message.content
                return data["choices"][0]["message"]["content"]
                
        except httpx.HTTPStatusError as e:
            # HTTP error (4xx, 5xx)
            print(f"❌ Server Error: {e.response.status_code}")
            print(f"❌ Response: {e.response.text}")
            raise Exception(f"Zeabur API Error {e.response.status_code}: {e.response.text}")
        except httpx.RequestError as e:
            # Network error (timeout, connection refused, etc.)
            print(f"❌ Request error: {e}")
            raise Exception(f"Request failed: {str(e)}")

    async def chat(self, messages: List[Dict[str, str]]) -> str:
        """
        Chat with conversation history.
        
        MESSAGE ROLES:
        - "system": Instructions for the AI (sets behavior)
        - "user": Human messages
        - "assistant": Previous AI responses (for context)
        
        EXAMPLE:
        messages = [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "Hello!"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How are you?"}
        ]
        
        Args:
            messages: List of conversation messages
            
        Returns:
            str: The assistant's response
        """
        url = f"{self.base_url}/v1/chat/completions"
        
        print(f"📤 POST {url}")
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    url,
                    json={
                        "model": self.model,
                        # Pass the full conversation history
                        "messages": messages,
                        "temperature": 0.7,
                        # Higher max_tokens for potentially longer responses
                        "max_tokens": 2000,
                        "stream": False
                    },
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.api_key}"
                    }
                )
                
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
                
        except httpx.HTTPStatusError as e:
            print(f"❌ Server Error: {e.response.status_code}")
            print(f"❌ Response: {e.response.text}")
            raise Exception(f"Chat API Error: {e.response.text}")
        except Exception as e:
            raise Exception(f"Chat request failed: {str(e)}")
