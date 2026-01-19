# Build a Deep Research AI Agent from Scratch

This tutorial guides you through building an AI-powered research agent step by step. You'll create a Python backend with FastAPI and a React frontend that work together to answer questions using real-time web search.

## What You'll Build

```
┌─────────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE (React)                        │
│                    "What are the latest AI news?"                    │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      PYTHON BACKEND (FastAPI)                        │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────────────┐   │
│  │   Agent     │────▶│    LLM      │────▶│   Web Scraper       │   │
│  │ (Orchestrator)│    │  (Brain)    │     │ (BrightData SERP)   │   │
│  └─────────────┘     └─────────────┘     └─────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

## Prerequisites

- Python 3.9+
- Node.js 18+
- API Keys:
  - **Zeabur AI Hub** (or any OpenAI-compatible API) - for LLM
  - **BrightData** - for web search

---

## Project Structure

```
deep-research-agent/
├── services/
│   ├── backend/           # Python FastAPI backend
│   │   ├── agent.py       # AI Agent orchestration
│   │   ├── llm.py         # LLM API client
│   │   ├── scraper.py     # Web scraping client
│   │   ├── main.py        # FastAPI server
│   │   ├── requirements.txt
│   │   └── .env           # Environment variables
│   └── frontend/          # React frontend
│       ├── src/
│       │   ├── App.tsx
│       │   ├── App.css
│       │   ├── main.tsx
│       │   └── index.css
│       ├── index.html
│       ├── package.json
│       ├── vite.config.ts
│       └── .env
└── Makefile               # Convenience commands
```

---

## Step 1: Create Project Structure

```bash
mkdir -p deep-research-agent/services/backend
mkdir -p deep-research-agent/services/frontend/src
cd deep-research-agent
```

---

## Step 2: Build the Python Backend

### 2.1 Create `services/backend/requirements.txt`

```txt
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
python-dotenv>=1.0.0
httpx>=0.26.0
pydantic>=2.5.3
```

### 2.2 Create `services/backend/.env`

```env
BRIGHTDATA_API_TOKEN=YOUR_BRIGHTDATA_API_TOKEN_HERE
ZEABUR_API_TOKEN=YOUR_ZEABUR_API_TOKEN_HERE
```

### 2.3 Create `services/backend/llm.py`

```python
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
```

### 2.4 Create `services/backend/scraper.py`

```python
"""
============================================================================
WEB SCRAPER - BRIGHTDATA SERP API CLIENT (PYTHON)
============================================================================

This file implements web scraping using BrightData's SERP API.
It fetches Google search results and returns structured data.

KEY CONCEPTS FOR WORKSHOP:

1. SERP (Search Engine Results Page) APIs:
   - Services that fetch and parse search engine results
   - Return structured JSON instead of raw HTML
   - Handle anti-bot measures, CAPTCHAs, etc.

2. WHY USE A PROXY SERVICE?
   - Direct Google scraping often gets blocked
   - Proxy services handle:
     - IP rotation
     - CAPTCHA solving
     - Rate limiting
     - Geographic targeting

3. REQUEST FLOW:
   Your App -> BrightData API -> Google -> BrightData -> Your App
                                             (parses HTML)

4. AUTHENTICATION:
   - Bearer token in Authorization header
   - Token tied to "zones" (proxy configurations)

============================================================================
"""

import httpx
from typing import Dict, Any
from urllib.parse import quote


class BrightDataScraper:
    """
    Web scraper using BrightData SERP API.
    
    This class fetches Google search results through BrightData's
    proxy network and returns parsed JSON data.
    
    FEATURES:
    - Automatic HTML parsing to structured data
    - Handles anti-bot measures
    - Returns organic search results
    """
    
    def __init__(self, api_token: str, zone: str = "serp_api1"):
        """
        Initialize the scraper.
        
        Args:
            api_token: BrightData API token (from dashboard)
            zone: BrightData zone name (proxy configuration)
                  'serp_api1' is typically configured for search scraping
        """
        self.api_token = api_token
        self.base_url = "https://api.brightdata.com"
        self.zone = zone

    async def search_web(self, query: str) -> Dict[str, Any]:
        """
        Perform a web search and return parsed results.
        
        REQUEST FLOW:
        1. Construct Google search URL with query
        2. Send URL to BrightData API
        3. BrightData fetches page through proxy network
        4. BrightData parses HTML to structured JSON
        5. Return parsed results
        
        Args:
            query: Search query string
            
        Returns:
            dict: Parsed search results with organic results,
                  or error dict if request fails
        """
        try:
            # STEP 1: Construct Google search URL
            # quote() URL-encodes the query (spaces -> %20, etc.)
            # hl=en (English), gl=us (United States) for consistent results
            search_url = f"https://www.google.com/search?q={quote(query)}&hl=en&gl=us"
            
            # STEP 2: Build BrightData request body
            # This tells BrightData what to fetch and how to return it
            request_body = {
                "zone": self.zone,           # Which proxy configuration to use
                "url": search_url,           # URL to fetch
                "format": "json",            # Return JSON (not raw HTML)
                "data_format": "parsed_light" # Minimal parsed data
            }
            
            print(f"🔍 Searching BrightData for: {query}")
            print(f"📡 Request URL: {self.base_url}/request")
            
            # STEP 3: Make the API request
            # httpx.AsyncClient for async HTTP requests
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/request",
                    json=request_body,
                    headers={
                        # BEARER TOKEN AUTH
                        "Authorization": f"Bearer {self.api_token}",
                        "Content-Type": "application/json"
                    },
                    # brd_json=1 tells BrightData to return JSON in body
                    params={"brd_json": 1}
                )
                
                print(f"📥 Response status: {response.status_code}")
                
                # STEP 4: Handle HTTP errors
                # 401 = Unauthorized (bad API key)
                if response.status_code == 401:
                    print("❌ BrightData API error: 401 Unauthorized")
                    print("📄 Response:", response.text[:200])
                    return {"error": "BrightData API authentication failed. Please check your BRIGHTDATA_API_TOKEN in .env file."}
                
                # Other 4xx/5xx errors
                if response.status_code >= 400:
                    print(f"❌ BrightData API error: {response.status_code}")
                    print(f"📄 Response: {response.text[:500]}")
                    return {"error": f"API returned status {response.status_code}"}
                
                # Handle empty response
                if not response.text:
                    print("⚠️ Empty response from BrightData")
                    return {"error": "Empty response from API"}
                
                # STEP 5: Parse JSON response
                data = response.json()
                print(f"📦 Response keys: {list(data.keys()) if isinstance(data, dict) else 'not a dict'}")
                
                # BrightData wraps results in "body" field
                # The body contains "organic" array with search results
                if data and "body" in data:
                    body = data["body"]
                    # Log result count for debugging
                    if isinstance(body, dict) and "organic" in body:
                        print(f"✅ Found {len(body.get('organic', []))} organic results")
                    elif isinstance(body, list):
                        print(f"✅ Found {len(body)} results")
                    return body
                
                # Fallback: return full response if no body
                print(f"⚠️ No 'body' in response, returning full data")
                return data
                
        except httpx.HTTPStatusError as e:
            # HTTP error with response
            print(f"❌ BrightData Scraper Error: Status {e.response.status_code}")
            print(f"📄 Response Data: {e.response.text[:500]}")
            return {"error": f"HTTP error: {e.response.status_code}"}
        except Exception as e:
            # Network error or other exception
            print(f"❌ BrightData Scraper Error: {type(e).__name__}: {e}")
            return {"error": str(e)}
```

### 2.5 Create `services/backend/agent.py`

```python
"""
============================================================================
DEEP RESEARCH AI AGENT - PYTHON IMPLEMENTATION
============================================================================

This file implements the core AI Agent pattern in Python.

KEY CONCEPTS FOR WORKSHOP:

1. AI AGENT ARCHITECTURE:
   - Agent = LLM (brain) + Tools (capabilities)
   - Orchestrates reasoning and action
   - Follows: Perceive → Think → Act → Synthesize

2. ASYNC PROGRAMMING IN PYTHON:
   - Uses async/await for non-blocking I/O
   - Essential for web requests and API calls
   - Python's asyncio is similar to JavaScript's promises

3. PROMPT ENGINEERING:
   - Classification prompts (should search?)
   - Extraction prompts (search query)
   - RAG prompts (answer from context)

4. ERROR HANDLING:
   - Validate inputs at boundaries
   - Gracefully handle API failures
   - Return user-friendly error messages

============================================================================
"""

import json
from llm import ZeaburLLM
from scraper import BrightDataScraper


class WebSearchAgent:
    """
    WebSearchAgent - The main AI agent class (Python version)
    
    This class orchestrates:
    - An LLM for reasoning and generation
    - A web scraper for retrieving real-time information
    
    WORKFLOW:
    1. Receive user question
    2. Decide if web search is needed
    3. If needed: extract search query → search → synthesize answer
    4. If not needed: generate direct answer
    """
    
    def __init__(self, zeabur_api_key: str, brightdata_token: str, model: str = None):
        """
        Initialize the agent with required services.
        
        Args:
            zeabur_api_key: API key for Zeabur AI Hub
            brightdata_token: API token for BrightData SERP
            model: Optional model name override
        """
        # Initialize the LLM client - our "brain"
        self.llm = ZeaburLLM(api_key=zeabur_api_key, model=model)
        
        # Initialize the scraper - our "eyes" for the web
        self.scraper = BrightDataScraper(brightdata_token)

    async def run(self, user_query: str) -> str:
        """
        Main entry point - process a user query.
        
        AGENT WORKFLOW:
        ┌─────────────────────────────────────────────────────────┐
        │ 1. VALIDATE - Check input is valid                      │
        │ 2. REASON   - Should we search the web?                 │
        │ 3. EXTRACT  - What search query to use?                 │
        │ 4. ACT      - Execute web search                        │
        │ 5. SYNTHESIZE - Generate answer from results            │
        └─────────────────────────────────────────────────────────┘
        
        Args:
            user_query: The user's question
            
        Returns:
            str: The agent's response
        """
        print(f"\n💭 User Query: {user_query}\n")
        
        # INPUT VALIDATION: Always validate at the boundary
        if not user_query or not isinstance(user_query, str) or not user_query.strip():
            print("❌ Invalid user query provided to WebSearchAgent:", user_query)
            return "Error: Invalid query provided."

        # ========== STEP 1: REASONING ==========
        # Use LLM to decide if we need to search
        needs_search = await self._should_search(user_query)
        print(f"💡 Search needed: {'YES' if needs_search else 'NO'}")
        
        # DIRECT ANSWER PATH: Skip search if not needed
        if not needs_search:
            print("📝 Answering directly without search...")
            return await self.llm.generate(user_query)

        # ========== STEP 2: QUERY EXTRACTION ==========
        # Convert natural language to search keywords
        print("🔍 Determining what to search for...")
        search_query = await self._extract_search_query(user_query)
        print(f'🔑 Extracted search query: "{search_query}"')
        
        # Validate extracted query
        if not search_query or not isinstance(search_query, str) or not search_query.strip():
            print("❌ Invalid search query extracted:", search_query)
            return "Error: Could not extract a valid search query."
        
        # ========== STEP 3: WEB SEARCH ==========
        # Execute the search using our tool
        print("🚀 Executing web search...")
        search_results = await self._web_search(search_query.strip())
        print("🏁 Web search completed")
        
        # Debug log for troubleshooting
        print(f"📄 Raw search results preview: {search_results[:100]}...")
        
        # ========== STEP 4: SYNTHESIS ==========
        # Generate answer from search results (RAG pattern)
        print("🧠 Generating answer from search results...")
        final_answer = await self._generate_answer(user_query, search_results)
        return final_answer

    async def _should_search(self, query: str) -> bool:
        """Determine if a web search is needed for this query."""
        print(f'📋 Evaluating if search is needed for: "{query}"')
        
        # CLASSIFICATION PROMPT: Clear instruction with constrained output
        prompt = f"""Does this question require searching the web for current information? Answer only YES or NO.
    
Question: {query}

Answer:"""

        response = await self.llm.generate(prompt)
        
        # Simple parsing - check if 'yes' appears (case-insensitive)
        result = "yes" in response.lower()
        print(f"📊 Evaluation result: {'SEARCH REQUIRED' if result else 'DIRECT ANSWER'}")
        
        return result

    async def _extract_search_query(self, query: str) -> str:
        """Extract optimal search keywords from natural language."""
        print(f'📋 Extracting search query from: "{query}"')
        
        # EXTRACTION PROMPT with constraints
        prompt = f"""Extract a concise search query (3-6 words) from this question:

Question: {query}

Search query:"""

        print("📤 Sending extraction prompt to LLM...")
        response = await self.llm.generate(prompt)
        print(f'📥 Received LLM response: "{response}"')
        
        result = response.strip()
        print(f'🔑 Final extracted search query: "{result}"')
        
        return result

    async def _web_search(self, query: str) -> str:
        """Execute web search and return results as string."""
        print(f'📡 Initiating search request for query: "{query}"')
        
        # Input validation
        if not query or not isinstance(query, str) or not query.strip():
            print("❌ Invalid search query provided:", query)
            return "Error: Invalid search query provided."
        
        trimmed_query = query.strip()
        
        # Execute search via scraper
        results = await self.scraper.search_web(trimmed_query)
        print(f'📨 Search request completed for query: "{trimmed_query}"')
        
        # Handle empty or null results
        if not results:
            print("⚠️ No results found for query:", trimmed_query)
            return "No results found."
        
        # Handle error responses from scraper
        if isinstance(results, dict) and "error" in results:
            print(f"⚠️ Search returned error: {results['error']}")
            return f"Error: {results['error']}"
        
        # Handle empty collections
        if isinstance(results, (list, dict)) and len(results) == 0:
            print("⚠️ Empty results for query:", trimmed_query)
            return "No results found."

        print(f'📬 Received raw results for query: "{trimmed_query}"')
        
        # Convert to JSON string for LLM to process
        try:
            return json.dumps(results, indent=2)
        except Exception as e:
            print("❌ Failed to stringify raw results:", e)
            return "Error processing results."

    async def _generate_answer(self, original_query: str, search_results: str) -> str:
        """Generate final answer using RAG (Retrieval-Augmented Generation)."""
        print(f'📋 Generating final answer for: "{original_query}"')
        print(f"📎 With search results length: {len(search_results)} characters")
        
        # Handle error cases
        if search_results.startswith("Error:") or search_results == "No results found.":
            print("⚠️ Search returned an error or no results")
            if search_results.startswith("Error:"):
                error_detail = search_results.replace("Error: ", "")
                return f'Search failed: {error_detail}'
            return f'I couldn\'t find information about "{original_query}". Please try rephrasing your question.'
        
        # RAG PROMPT: Combines context with question
        prompt = f"""Based on the following search results, answer the user's question accurately and concisely.

User Question: {original_query}

Search Results:
{search_results}

Answer:"""

        # Use chat() with system prompt for better control
        result = await self.llm.chat([
            {"role": "system", "content": "You are a helpful AI assistant that answers questions based on search results. Be concise and accurate."},
            {"role": "user", "content": prompt}
        ])
        
        print(f"📥 Received final answer from LLM ({len(result)} characters)")
        
        return result
```

### 2.6 Create `services/backend/main.py`

```python
"""
============================================================================
FASTAPI SERVER - REST API FOR THE AI AGENT (PYTHON)
============================================================================

This file sets up a FastAPI server that exposes the AI agent as a REST API.
FastAPI is a modern, high-performance Python web framework.

KEY CONCEPTS FOR WORKSHOP:

1. FASTAPI vs EXPRESS:
   - FastAPI (Python) is similar to Express (Node.js)
   - Both create REST APIs with routing
   - FastAPI has built-in validation with Pydantic
   - FastAPI auto-generates OpenAPI docs

2. CORS (Cross-Origin Resource Sharing):
   - Browsers block requests to different origins by default
   - CORS middleware allows frontend to call our API
   - In production, specify exact allowed origins

3. PYDANTIC MODELS:
   - Define request/response shapes with type hints
   - Automatic validation of incoming data
   - Auto-generated API documentation

4. ASYNC ENDPOINTS:
   - FastAPI supports async/await natively
   - Better performance for I/O-bound operations
   - Our agent uses async for LLM and scraper calls

============================================================================
"""

import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from agent import WebSearchAgent

# LOAD ENVIRONMENT VARIABLES
load_dotenv()

# CREATE FASTAPI APPLICATION
app = FastAPI(title="Web Search AI Agent API")

# CORS MIDDLEWARE
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# CONFIGURATION
zeabur_api_key = os.getenv("ZEABUR_API_TOKEN")
brightdata_token = os.getenv("BRIGHTDATA_API_TOKEN")
zeabur_model = os.getenv("ZEABUR_MODEL")

if not zeabur_api_key or not brightdata_token:
    print("❌ Missing environment variables! Check your .env file.")
    print("Required: ZEABUR_API_TOKEN, BRIGHTDATA_API_TOKEN")
else:
    print(f"✅ Environment loaded successfully")

# LAZY INITIALIZATION
agent = None


def get_agent() -> WebSearchAgent:
    """Get or create the agent instance (singleton pattern)."""
    global agent
    if agent is None:
        if not zeabur_api_key or not brightdata_token:
            raise HTTPException(
                status_code=500,
                detail="Missing environment variables: ZEABUR_API_TOKEN or BRIGHTDATA_API_TOKEN"
            )
        agent = WebSearchAgent(zeabur_api_key, brightdata_token, zeabur_model)
    return agent


# PYDANTIC MODELS
class QueryRequest(BaseModel):
    query: str


class QueryResponse(BaseModel):
    answer: str


# API ENDPOINTS
@app.get("/")
async def root():
    return {"message": "Web Search AI Agent API is running", "status": "ok"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/api/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """POST /api/query - Main endpoint for asking questions."""
    if not request.query:
        raise HTTPException(status_code=400, detail="Query is required")
    
    print(f"Received query: {request.query}")
    
    try:
        agent_instance = get_agent()
        answer = await agent_instance.run(request.query)
        return QueryResponse(answer=answer)
    except Exception as e:
        print(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# MAIN ENTRY POINT
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    print(f"🚀 Web Search AI Agent Server running on http://localhost:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
```

---

## Step 3: Build the React Frontend

### 3.1 Initialize the Frontend

```bash
cd services/frontend
npm create vite@latest . -- --template react-ts
npm install react-markdown remark-gfm
```

### 3.2 Create `services/frontend/.env`

```env
VITE_API_URL=http://localhost:8000
```

### 3.3 Replace `services/frontend/src/App.tsx`

```tsx
/**
 * ============================================================================
 * REACT FRONTEND - USER INTERFACE FOR THE AI AGENT
 * ============================================================================
 * 
 * KEY CONCEPTS FOR WORKSHOP:
 * 
 * 1. REACT HOOKS:
 *    - useState: Manage component state (query, loading, result, etc.)
 *    - State updates trigger re-renders
 * 
 * 2. FRONTEND-BACKEND COMMUNICATION:
 *    - fetch() API for HTTP requests
 *    - POST request with JSON body
 *    - Parse JSON response
 * 
 * 3. UI STATE MANAGEMENT:
 *    - Loading state: Show spinner while waiting
 *    - Error state: Display error messages
 *    - Result state: Show AI response
 *    - History: Remember recent queries
 * 
 * ============================================================================
 */

import { useState } from 'react'
import type { FormEvent, KeyboardEvent } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import './App.css'

interface HistoryItem {
  query: string;
  answer: string;
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function App() {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState('');
  const [error, setError] = useState('');
  const [history, setHistory] = useState<HistoryItem[]>([]);

  const handleSubmit = async (e?: FormEvent) => {
    e?.preventDefault();
    
    if (!query.trim()) {
      setError('Please enter a question');
      return;
    }

    setError('');
    setResult('');
    setLoading(true);

    try {
      const response = await fetch(`${API_URL}/api/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: query.trim() }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || data.error || 'Failed to get response');
      }

      setResult(data.answer);
      
      setHistory(prev => {
        const newHistory = [{ query: query.trim(), answer: data.answer }, ...prev];
        return newHistory.slice(0, 5);
      });
    } catch (err) {
      console.error('Error:', err);
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleSubmit();
    }
  };

  return (
    <div className="app">
      <div className="container">
        <h1>🔬 Deep Research AI Agent</h1>
        <p className="subtitle">Ask anything and get comprehensive, research-backed answers</p>
        
        <div className="input-container">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask me anything..."
            disabled={loading}
          />
          <button onClick={() => handleSubmit()} disabled={loading}>
            {loading ? 'Searching...' : 'Ask'}
          </button>
        </div>

        {loading && (
          <div className="loading">
            <div className="spinner"></div>
            <p>Searching the web and generating your answer...</p>
          </div>
        )}

        {error && <div className="error">{error}</div>}

        {result && (
          <div className="result-container">
            <h2>Answer:</h2>
            <div className="result markdown-content">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{result}</ReactMarkdown>
            </div>
          </div>
        )}

        {history.length > 0 && (
          <div className="history">
            <h2>Recent Queries</h2>
            {history.map((item, index) => (
              <div key={index} className="history-item">
                <div className="history-query">{item.query}</div>
                <div className="history-answer">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{item.answer}</ReactMarkdown>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default App
```

### 3.4 Replace `services/frontend/src/App.css`

```css
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.app {
  background: linear-gradient(135deg, #1a2a6c, #b21f1f, #1a2a6c);
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px;
}

.container {
  background-color: rgba(255, 255, 255, 0.95);
  border-radius: 15px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
  width: 100%;
  max-width: 800px;
  padding: 30px;
  text-align: center;
}

h1 {
  color: #1a2a6c;
  margin-bottom: 10px;
  font-size: 2.5rem;
}

.subtitle {
  color: #666;
  margin-bottom: 30px;
  font-size: 1.1rem;
}

.input-container {
  display: flex;
  gap: 10px;
  margin-bottom: 30px;
}

.input-container input {
  flex: 1;
  padding: 15px;
  border: 2px solid #ddd;
  border-radius: 8px;
  font-size: 1rem;
  transition: border-color 0.3s;
}

.input-container input:focus {
  outline: none;
  border-color: #1a2a6c;
}

.input-container button {
  background: linear-gradient(to right, #1a2a6c, #b21f1f);
  color: white;
  border: none;
  border-radius: 8px;
  padding: 15px 25px;
  cursor: pointer;
  font-size: 1rem;
  font-weight: bold;
  transition: transform 0.2s, opacity 0.2s;
}

.input-container button:hover {
  opacity: 0.9;
  transform: translateY(-2px);
}

.input-container button:disabled {
  background: #cccccc;
  cursor: not-allowed;
  transform: none;
}

.loading {
  text-align: center;
  margin: 20px 0;
}

.spinner {
  border: 4px solid rgba(0, 0, 0, 0.1);
  border-left-color: #1a2a6c;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
  margin: 0 auto 15px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.result-container {
  background-color: #f8f9fa;
  border-radius: 8px;
  padding: 20px;
  text-align: left;
  min-height: 100px;
  margin-bottom: 20px;
}

.result-container h2 {
  color: #1a2a6c;
  margin-bottom: 15px;
  font-size: 1.5rem;
}

.result {
  line-height: 1.6;
  color: #333;
}

.markdown-content p {
  margin-bottom: 1em;
  line-height: 1.7;
}

.markdown-content ul, .markdown-content ol {
  margin: 1em 0;
  padding-left: 1.5em;
}

.markdown-content li {
  margin-bottom: 0.5em;
}

.markdown-content strong {
  color: #1a2a6c;
}

.markdown-content code {
  background-color: #f0f0f0;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Consolas', monospace;
}

.error {
  color: #b21f1f;
  background-color: #ffe6e6;
  border-radius: 8px;
  padding: 15px;
  margin-bottom: 20px;
}

.history {
  margin-top: 30px;
  text-align: left;
}

.history h2 {
  color: #1a2a6c;
  margin-bottom: 15px;
  font-size: 1.5rem;
}

.history-item {
  background-color: #f8f9fa;
  border-radius: 8px;
  padding: 15px;
  margin-bottom: 10px;
}

.history-query {
  font-weight: bold;
  color: #1a2a6c;
  margin-bottom: 5px;
}

.history-answer {
  color: #333;
  line-height: 1.5;
  max-height: 150px;
  overflow-y: auto;
}

@media (max-width: 600px) {
  .container { padding: 20px; }
  h1 { font-size: 2rem; }
  .input-container { flex-direction: column; }
}
```

### 3.5 Replace `services/frontend/src/index.css`

```css
:root {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  line-height: 1.5;
  font-weight: 400;
  font-synthesis: none;
  text-rendering: optimizeLegibility;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

body {
  margin: 0;
  min-width: 320px;
  min-height: 100vh;
}

#root {
  min-height: 100vh;
}
```

---

## Step 4: Create the Makefile

Create `Makefile` in the project root:

```makefile
.PHONY: dev-backend dev-frontend dev install-backend install-frontend install

# Start the Python backend server
dev-backend:
	cd services/backend && python3 main.py

# Start the React frontend dev server
dev-frontend:
	cd services/frontend && npm run dev

# Start both services (backend in background, frontend in foreground)
dev:
	@echo "Starting backend..."
	cd services/backend && python3 main.py &
	@echo "Starting frontend..."
	cd services/frontend && npm run dev

# Install backend dependencies
install-backend:
	cd services/backend && pip3 install -r requirements.txt

# Install frontend dependencies
install-frontend:
	cd services/frontend && npm install

# Install all dependencies
install: install-backend install-frontend
```

---

## Step 5: Run the Project

### 5.1 Install Dependencies

```bash
# Install Python dependencies
cd services/backend
pip3 install -r requirements.txt

# Install Node.js dependencies
cd ../frontend
npm install
```

### 5.2 Configure Environment Variables

1. Get your **Zeabur API Token** from [Zeabur AI Hub](https://zeabur.com/ai)
2. Get your **BrightData API Token** from [BrightData](https://brightdata.com)
3. Update `services/backend/.env` with your tokens

### 5.3 Start the Servers

**Terminal 1 - Backend:**
```bash
cd services/backend
python3 main.py
```

**Terminal 2 - Frontend:**
```bash
cd services/frontend
npm run dev
```

### 5.4 Open the App

Open http://localhost:5173 in your browser and ask a question!

---

## How It Works

1. **User asks a question** in the React frontend
2. **Frontend sends POST request** to `/api/query`
3. **Agent decides** if web search is needed
4. If needed: **extracts search keywords** using LLM
5. **BrightData fetches** Google search results
6. **LLM synthesizes** an answer from the search results
7. **Answer displayed** in the frontend with Markdown formatting

---

## Key Concepts Recap

| Concept | Description |
|---------|-------------|
| **AI Agent** | System that combines LLM reasoning with tool use |
| **RAG** | Retrieval-Augmented Generation - grounding answers in retrieved data |
| **Prompt Engineering** | Crafting prompts for classification, extraction, and synthesis |
| **OpenAI-Compatible API** | Standard API format for LLM communication |
| **SERP API** | Service for fetching structured search results |
| **FastAPI** | Modern Python web framework with async support |
| **React Hooks** | useState for managing component state |
| **CORS** | Enabling cross-origin requests from frontend to backend |

---

## Next Steps

- Add conversation memory for multi-turn chat
- Implement streaming responses
- Add more tools (calculator, code execution, etc.)
- Deploy to cloud platforms (Vercel, Railway, etc.)
