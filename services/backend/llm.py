import httpx
import os
from typing import List, Dict, Optional


class NosanaLLM:
    def __init__(self, base_url: str, model: Optional[str] = None):
        # Clean up the URL - remove trailing slashes and /api if present
        self.base_url = base_url.rstrip('/').removesuffix('/api')
        self.model = model or os.getenv('NOSANA_MODEL', 'gpt-oss:20b')
        
        print(f"🔗 Connecting to: {self.base_url}")
        print(f"🤖 Using model: {self.model}")

    async def generate(self, prompt: str) -> str:
        """Generate a completion using OpenAI-compatible format"""
        url = f"{self.base_url}/v1/chat/completions"
        
        print(f"📤 POST {url}")
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    url,
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.7,
                        "max_tokens": 1000,
                        "stream": False
                    },
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 404 or response.status_code == 405:
                    print("⚠️  OpenAI endpoint failed, trying native Ollama format...")
                    return await self._generate_native_ollama(prompt)
                
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
                
        except httpx.HTTPStatusError as e:
            print(f"❌ Server Error: {e.response.status_code}")
            if e.response.status_code in (404, 405):
                return await self._generate_native_ollama(prompt)
            raise Exception(f"Nosana API Error {e.response.status_code}: {e.response.text}")
        except httpx.RequestError as e:
            print(f"❌ Request error: {e}")
            raise Exception(f"Request failed: {str(e)}")

    async def _generate_native_ollama(self, prompt: str) -> str:
        """Fallback: Try native Ollama format"""
        url = f"{self.base_url}/api/generate"
        
        print(f"📤 Trying native Ollama: POST {url}")
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    url,
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False
                    },
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                data = response.json()
                return data["response"]
        except Exception as e:
            print(f"❌ Native Ollama also failed: {e}")
            raise Exception("Both API formats failed. Check Nosana documentation for correct endpoint.")

    async def chat(self, messages: List[Dict[str, str]]) -> str:
        """Chat with conversation history"""
        url = f"{self.base_url}/v1/chat/completions"
        
        print(f"📤 POST {url}")
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    url,
                    json={
                        "model": self.model,
                        "messages": messages,
                        "temperature": 0.7,
                        "max_tokens": 1000,
                        "stream": False
                    },
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code in (404, 405):
                    print("⚠️  Trying native Ollama chat...")
                    return await self._chat_native_ollama(messages)
                
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (404, 405):
                return await self._chat_native_ollama(messages)
            raise Exception(f"Chat API Error: {e.response.text}")
        except Exception as e:
            raise Exception(f"Chat request failed: {str(e)}")

    async def _chat_native_ollama(self, messages: List[Dict[str, str]]) -> str:
        """Fallback: Native Ollama chat"""
        url = f"{self.base_url}/api/chat"
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    url,
                    json={
                        "model": self.model,
                        "messages": messages,
                        "stream": False
                    },
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                data = response.json()
                return data["message"]["content"]
        except Exception as e:
            raise Exception(f"Native chat also failed: {str(e)}")
