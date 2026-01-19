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
# load_dotenv() reads .env file and adds variables to os.environ
# Call this early, before accessing environment variables
load_dotenv()

# CREATE FASTAPI APPLICATION
# The title appears in auto-generated API documentation
app = FastAPI(title="Web Search AI Agent API")

# ============================================================================
# CORS MIDDLEWARE
# ============================================================================
# CORS allows web pages from other domains to make requests to our API.
# Without CORS, browsers will block frontend -> backend requests.
#
# SECURITY NOTE:
# - allow_origins=["*"] allows ALL origins (not secure for production)
# - In production, list specific allowed origins:
#   allow_origins=["https://myapp.com", "https://www.myapp.com"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # Which origins can access (production: specific URLs)
    allow_credentials=True,        # Allow cookies/auth headers
    allow_methods=["*"],          # Which HTTP methods (GET, POST, etc.)
    allow_headers=["*"],          # Which headers are allowed
)

# ============================================================================
# CONFIGURATION
# ============================================================================

# Get configuration from environment variables
# os.getenv() returns None if variable doesn't exist
zeabur_api_key = os.getenv("ZEABUR_API_TOKEN")
brightdata_token = os.getenv("BRIGHTDATA_API_TOKEN")
zeabur_model = os.getenv("ZEABUR_MODEL")

# Log configuration status
if not zeabur_api_key or not brightdata_token:
    print("❌ Missing environment variables! Check your .env file.")
    print("Required: ZEABUR_API_TOKEN, BRIGHTDATA_API_TOKEN")
else:
    print(f"✅ Environment loaded successfully")

# ============================================================================
# AGENT INITIALIZATION
# ============================================================================

# LAZY INITIALIZATION PATTERN
# We don't create the agent immediately because:
# 1. Environment might not be fully loaded
# 2. We want to fail gracefully with HTTP error, not crash
# 3. Agent creation might be slow/expensive
agent = None


def get_agent() -> WebSearchAgent:
    """
    Get or create the agent instance (singleton pattern).
    
    LAZY LOADING:
    - Agent is created on first request, not at startup
    - Allows app to start even if config is missing
    - Returns informative error if config is missing
    
    Returns:
        WebSearchAgent: The singleton agent instance
        
    Raises:
        HTTPException: If environment variables are missing
    """
    global agent
    if agent is None:
        # Validate configuration before creating agent
        if not zeabur_api_key or not brightdata_token:
            raise HTTPException(
                status_code=500,
                detail="Missing environment variables: ZEABUR_API_TOKEN or BRIGHTDATA_API_TOKEN"
            )
        # Create the agent instance
        agent = WebSearchAgent(zeabur_api_key, brightdata_token, zeabur_model)
    return agent


# ============================================================================
# PYDANTIC MODELS - Request/Response Schemas
# ============================================================================
# Pydantic models define the shape of data and provide:
# - Automatic validation
# - Type hints for IDE support
# - Auto-generated API documentation

class QueryRequest(BaseModel):
    """
    Request body for the /api/query endpoint.
    
    Example JSON:
    {"query": "What is the weather today?"}
    """
    query: str  # The user's question (required)


class QueryResponse(BaseModel):
    """
    Response body for the /api/query endpoint.
    
    Example JSON:
    {"answer": "The weather is sunny and 72°F..."}
    """
    answer: str  # The agent's response


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """
    GET / - Health check and welcome message.
    
    Returns basic API status. Useful for:
    - Checking if server is running
    - Load balancer health checks
    - Quick manual testing
    """
    return {"message": "Web Search AI Agent API is running", "status": "ok"}


@app.get("/health")
async def health_check():
    """
    GET /health - Dedicated health check endpoint.
    
    Standard endpoint for container orchestration (Kubernetes, etc.)
    and monitoring systems.
    """
    return {"status": "healthy"}


@app.post("/api/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """
    POST /api/query - Main endpoint for asking questions.
    
    FASTAPI FEATURES DEMONSTRATED:
    - request: QueryRequest - Auto-validates request body
    - response_model=QueryResponse - Auto-validates/documents response
    - async def - Supports async operations
    
    REQUEST:
    {
        "query": "What are the latest AI developments?"
    }
    
    RESPONSE:
    {
        "answer": "Recent AI developments include..."
    }
    
    HTTP STATUS CODES:
    - 200: Success
    - 400: Bad Request (invalid/missing query)
    - 500: Internal Server Error (agent error)
    
    Args:
        request: Validated QueryRequest object
        
    Returns:
        QueryResponse: The agent's answer
    """
    # Validate query is not empty
    # Pydantic ensures query exists, but we check if it's meaningful
    if not request.query:
        raise HTTPException(status_code=400, detail="Query is required")
    
    print(f"Received query: {request.query}")
    
    try:
        # Get agent instance (lazy loading)
        agent_instance = get_agent()
        
        # Process query through agent (async call)
        answer = await agent_instance.run(request.query)
        
        # Return structured response
        return QueryResponse(answer=answer)
    except Exception as e:
        # Log error for debugging
        print(f"Error processing query: {e}")
        
        # Return 500 error with message
        # In production, you might want to hide internal details
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    """
    Run the server directly with: python main.py
    
    UVICORN:
    - ASGI server for running FastAPI
    - High-performance, production-ready
    - Supports hot reload in development
    
    Alternative: uvicorn main:app --reload
    """
    import uvicorn
    
    # Get port from environment (useful for deployment platforms)
    port = int(os.getenv("PORT", 8000))
    
    print(f"🚀 Web Search AI Agent Server running on http://localhost:{port}")
    
    # Start the server
    # host="0.0.0.0" allows external connections (not just localhost)
    uvicorn.run(app, host="0.0.0.0", port=port)
