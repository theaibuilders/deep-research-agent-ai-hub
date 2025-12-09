# 🔬 Deep Research AI Agent

An AI-powered research assistant that combines natural language processing with real-time web scraping to provide comprehensive, research-backed answers to your questions.

## Features

- **Natural Language Queries** - Ask questions in plain English
- **Intelligent Search Detection** - Automatically determines when web search is needed
- **Real-Time Web Scraping** - Fetches current information via BrightData SERP API
- **Self-Hosted LLM** - Uses Nosana's decentralized GPU infrastructure for AI inference
- **Beautiful Response Formatting** - Renders markdown with tables, links, and rich formatting

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   React Frontend │────▶│  FastAPI Backend │────▶│   Nosana LLM    │
│   (Vite + TS)   │     │   (Python)       │     │   (Ollama API)  │
└─────────────────┘     └────────┬─────────┘     └─────────────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │   BrightData    │
                        │   (Web Search)  │
                        └─────────────────┘
```

## Tech Stack

### Backend
- **FastAPI** - Python web framework
- **httpx** - Async HTTP client
- **Pydantic** - Data validation

### Frontend
- **React 19** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **react-markdown** - Markdown rendering with GFM support

### External Services
- **Nosana** - Decentralized GPU compute for LLM inference
- **BrightData** - Web scraping and SERP API

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- Nosana endpoint URL
- BrightData API token

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd deep_research_agent
   ```

2. **Install all dependencies**
   ```bash
   make install
   ```

   Or install separately:
   ```bash
   # Backend
   cd services/backend && pip3 install -r requirements.txt

   # Frontend
   cd services/frontend && npm install
   ```

3. **Configure environment variables**

   Create a `.env` file in `services/backend/`:
   ```env
   NOSANA_OLLAMA_URL=your-nosana-endpoint-here
   NOSANA_MODEL=gpt-oss:20b
   BRIGHTDATA_API_TOKEN=your-brightdata-token-here
   PORT=8000
   ```

### Running the Application

**Start both services:**
```bash
make dev
```

Or run them separately:

**Backend (runs on http://localhost:8000):**
```bash
make dev-backend
```

**Frontend (runs on http://localhost:5173):**
```bash
make dev-frontend
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check - returns API status |
| `/health` | GET | Health check endpoint |
| `/api/query` | POST | Submit a query for research |

### Query Request

```json
POST /api/query
{
  "query": "What are the latest developments in AI?"
}
```

### Query Response

```json
{
  "answer": "Based on my research, here are the latest developments..."
}
```

## How It Works

1. **Query Analysis** - The LLM determines if the question requires real-time web data
2. **Search Query Extraction** - Extracts optimal search terms from the user's question
3. **Web Scraping** - BrightData fetches Google search results in real-time
4. **Answer Generation** - The LLM synthesizes search results into a comprehensive answer

## Project Structure

```
deep_research_agent/
├── services/
│   ├── backend/
│   │   ├── main.py          # FastAPI application entry point
│   │   ├── agent.py         # WebSearchAgent orchestration logic
│   │   ├── llm.py           # Nosana LLM client (OpenAI-compatible)
│   │   ├── scraper.py       # BrightData web scraping client
│   │   ├── requirements.txt # Python dependencies
│   │   └── .env.example     # Environment template
│   └── frontend/
│       ├── src/
│       │   ├── App.tsx      # Main React component
│       │   └── App.css      # Styling with markdown support
│       ├── package.json     # Node dependencies
│       └── vite.config.ts   # Vite configuration
├── Makefile                  # Development commands
└── README.md                 # This file
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `NOSANA_OLLAMA_URL` | Nosana GPU endpoint URL | Yes |
| `NOSANA_MODEL` | Model name (default: `gpt-oss:20b`) | No |
| `BRIGHTDATA_API_TOKEN` | BrightData API authentication token | Yes |
| `PORT` | Backend server port (default: 8000) | No |

## License

ISC
