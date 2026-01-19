import httpx
import os
from typing import List, Dict, Optional


class ZeaburLLM:
    """LLM client for Zeabur AI Hub (OpenAI-compatible API)"""
    
    def __init__(self, api_key: str, model: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key
        self.base_url = base_url or os.getenv('ZEABUR_BASE_URL', 'https://sfo1.aihub.zeabur.ai')
        self.base_url = self.base_url.rstrip('/')
        self.model = model or os.getenv('ZEABUR_MODEL', 'gpt-4o-mini')
        
        print(f"🔗 Connecting to Zeabur AI Hub: {self.base_url}")
        print(f"🤖 Using model: {self.model}")

    async def generate(self, prompt: str) -> str:
        """Generate a completion using OpenAI-compatible format"""
        url = f"{self.base_url}/v1/chat/completions"
        
        print(f"📤 POST {url}")
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    url,
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.7,
                        "max_tokens": 1000,
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
            raise Exception(f"Zeabur API Error {e.response.status_code}: {e.response.text}")
        except httpx.RequestError as e:
            print(f"❌ Request error: {e}")
            raise Exception(f"Request failed: {str(e)}")

    async def chat(self, messages: List[Dict[str, str]]) -> str:
        """Chat with conversation history"""
        url = f"{self.base_url}/v1/chat/completions"
        
        print(f"📤 POST {url}")
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    url,
                    json={
                        "model": self.model,
                        "messages": messages,
                        "temperature": 0.7,
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
