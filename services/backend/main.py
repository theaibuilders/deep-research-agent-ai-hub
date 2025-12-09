import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from agent import WebSearchAgent

# Load environment variables
load_dotenv()

app = FastAPI(title="Web Search AI Agent API")

# CORS middleware to allow frontend to communicate
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get environment variables
nosana_url = os.getenv("NOSANA_OLLAMA_URL")
brightdata_token = os.getenv("BRIGHTDATA_API_TOKEN")
nosana_model = os.getenv("NOSANA_MODEL")

if not nosana_url or not brightdata_token:
    print("❌ Missing environment variables! Check your .env file.")
    print("Required: NOSANA_OLLAMA_URL, BRIGHTDATA_API_TOKEN")
else:
    print(f"✅ Environment loaded successfully")

# Initialize the agent (lazy initialization)
agent = None


def get_agent() -> WebSearchAgent:
    global agent
    if agent is None:
        if not nosana_url or not brightdata_token:
            raise HTTPException(
                status_code=500,
                detail="Missing environment variables: NOSANA_OLLAMA_URL or BRIGHTDATA_API_TOKEN"
            )
        agent = WebSearchAgent(nosana_url, brightdata_token, nosana_model)
    return agent


class QueryRequest(BaseModel):
    query: str


class QueryResponse(BaseModel):
    answer: str


@app.get("/")
async def root():
    return {"message": "Web Search AI Agent API is running", "status": "ok"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/api/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
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


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    print(f"🚀 Web Search AI Agent Server running on http://localhost:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
