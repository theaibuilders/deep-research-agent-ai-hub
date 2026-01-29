# Web Search AI Agent - Project Specification

Create a full-stack AI-powered research agent application with a Python FastAPI backend and React TypeScript frontend. The agent answers user questions by intelligently deciding whether to search the web for real-time information or answer directly.

---

## Project Structure

```
deep-research-agent/
├── services/
│   ├── backend/
│   │   ├── main.py              # FastAPI server
│   │   ├── agent.py             # WebSearchAgent orchestration
│   │   ├── llm.py               # LLM client (OpenAI-compatible)
│   │   ├── scraper.py           # BrightData web scraper
│   │   ├── requirements.txt     # Python dependencies
│   │   ├── .env                 # Environment variables
│   │   └── .env.example         # Environment template
│   └── frontend/
│       ├── src/
│       │   ├── App.tsx          # Main React component
│       │   ├── App.css          # Styling
│       │   ├── main.tsx         # Entry point
│       │   └── index.css        # Global styles
│       ├── index.html           # HTML template
│       ├── package.json         # Node dependencies
│       ├── vite.config.ts       # Vite configuration
│       ├── tsconfig.json        # TypeScript config
│       └── .env                 # Frontend environment
└── Makefile                     # Development commands
```

---

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  React Frontend │────▶│  FastAPI Backend │────▶│  Zeabur AI Hub  │
│   (Vite + TS)   │     │    (Python)      │     │ (OpenAI-compat) │
└─────────────────┘     └────────┬─────────┘     └─────────────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │   BrightData    │
                        │   (Web Search)  │
                        └─────────────────┘
```

---

## Backend Specification

### File: `services/backend/requirements.txt`

```
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
python-dotenv>=1.0.0
httpx>=0.26.0
pydantic>=2.5.3
```

### File: `services/backend/.env.example`

```
BRIGHTDATA_API_TOKEN=YOUR_BRIGHTDATA_API_TOKEN_HERE
ZEABUR_API_TOKEN=YOUR_ZEABUR_API_TOKEN_HERE
ZEABUR_MODEL=gpt-4o-mini
ZEABUR_BASE_URL=https://sfo1.aihub.zeabur.ai
PORT=8000
```

### File: `services/backend/llm.py`

Create a `ZeaburLLM` class that communicates with OpenAI-compatible APIs:

**Constructor:**
- `__init__(self, api_key: str, model: Optional[str] = None, base_url: Optional[str] = None)`
- Default base_url: `https://sfo1.aihub.zeabur.ai` (fallback to `ZEABUR_BASE_URL` env var)
- Default model: `gpt-4o-mini` (fallback to `ZEABUR_MODEL` env var)
- Print connection info on init

**Methods:**
- `async generate(self, prompt: str) -> str`: Send single prompt, return response
- `async chat(self, messages: List[Dict[str, str]]) -> str`: Send conversation history, return response

**API Details:**
- Endpoint: `POST {base_url}/v1/chat/completions`
- Headers: `Authorization: Bearer {api_key}`, `Content-Type: application/json`
- Request body: `{"model": str, "messages": list, "temperature": 0.7, "max_tokens": 1000-2000, "stream": false}`
- Response: Extract `data["choices"][0]["message"]["content"]`

**Error Handling:**
- Use `httpx.AsyncClient` with 120 second timeout
- Handle `HTTPStatusError` (4xx/5xx) and `RequestError` (network errors)
- Print error details and raise descriptive exceptions

### File: `services/backend/scraper.py`

Create a `BrightDataScraper` class for web search via BrightData SERP API:

**Constructor:**
- `__init__(self, api_token: str, zone: str = "serp_api1")`
- Base URL: `https://api.brightdata.com`

**Methods:**
- `async search_web(self, query: str) -> Dict[str, Any]`: Perform Google search

**Implementation:**
1. Construct Google URL: `https://www.google.com/search?q={url_encoded_query}&hl=en&gl=us`
2. POST to `{base_url}/request` with params `{"brd_json": 1}`
3. Request body: `{"zone": zone, "url": search_url, "format": "json", "data_format": "parsed_light"}`
4. Headers: `Authorization: Bearer {api_token}`, `Content-Type: application/json`
5. Use 30 second timeout
6. Extract and return `data["body"]` which contains organic search results
7. Return `{"error": message}` dict on any failure (don't raise exceptions)

### File: `services/backend/agent.py`

Create a `WebSearchAgent` class that orchestrates LLM and web search:

**Constructor:**
- `__init__(self, zeabur_api_key: str, brightdata_token: str, model: str = None)`
- Initialize `ZeaburLLM` and `BrightDataScraper` instances

**Main Method:**
- `async run(self, user_query: str) -> str`

**Workflow:**
1. Validate input (non-empty string)
2. Call `_should_search(query)` - ask LLM if web search is needed
3. If NO: return `llm.generate(query)` directly
4. If YES:
   - Call `_extract_search_query(query)` - get 3-6 word search terms
   - Call `_web_search(search_query)` - execute search
   - Call `_generate_answer(query, results)` - synthesize answer using RAG

**Helper Methods:**

`async _should_search(self, query: str) -> bool`:
- Prompt: "Does this question require searching the web for current information? Answer only YES or NO.\n\nQuestion: {query}\n\nAnswer:"
- Return `"yes" in response.lower()`

`async _extract_search_query(self, query: str) -> str`:
- Prompt: "Extract a concise search query (3-6 words) from this question:\n\nQuestion: {query}\n\nSearch query:"
- Return stripped response

`async _web_search(self, query: str) -> str`:
- Call `scraper.search_web(query)`
- Return `json.dumps(results, indent=2)` or error message

`async _generate_answer(self, original_query: str, search_results: str) -> str`:
- Handle error cases (results starting with "Error:" or "No results found.")
- Use RAG prompt with system message:
  - System: "You are a helpful AI assistant that answers questions based on search results. Be concise and accurate."
  - User: "Based on the following search results, answer the user's question accurately and concisely.\n\nUser Question: {original_query}\n\nSearch Results:\n{search_results}\n\nAnswer:"

**Logging:**
- Include emoji-prefixed print statements showing workflow progress
- Log: query received, search decision, extracted query, search execution, answer generation

### File: `services/backend/main.py`

Create FastAPI server exposing the agent as REST API:

**Setup:**
- Load `.env` with `python-dotenv`
- Create FastAPI app with title "Web Search AI Agent API"
- Add CORS middleware allowing all origins (development)
- Read env vars: `ZEABUR_API_TOKEN`, `BRIGHTDATA_API_TOKEN`, `ZEABUR_MODEL`

**Pydantic Models:**
- `QueryRequest`: `query: str`
- `QueryResponse`: `answer: str`

**Endpoints:**
- `GET /` → `{"message": "Web Search AI Agent API is running", "status": "ok"}`
- `GET /health` → `{"status": "healthy"}`
- `POST /api/query` → Accept `QueryRequest`, return `QueryResponse`

**Agent Initialization:**
- Use lazy initialization (singleton pattern)
- Create agent on first `/api/query` request
- Raise HTTP 500 if env vars missing

**Entry Point:**
- Run with uvicorn on `0.0.0.0:{PORT}` (default 8000)

---

## Frontend Specification

### File: `services/frontend/package.json`

```json
{
  "name": "frontend",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "lint": "eslint .",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "react-markdown": "^10.0.0",
    "remark-gfm": "^4.0.0"
  },
  "devDependencies": {
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0",
    "@vitejs/plugin-react": "^4.0.0",
    "typescript": "~5.6.0",
    "vite": "^6.0.0"
  }
}
```

### File: `services/frontend/.env`

```
VITE_API_URL=http://localhost:8000
```

### File: `services/frontend/vite.config.ts`

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
})
```

### File: `services/frontend/src/App.tsx`

Create main React component with:

**State (useState hooks):**
- `query: string` - input field value
- `loading: boolean` - API request in progress
- `result: string` - AI response
- `error: string` - error message
- `history: HistoryItem[]` - recent queries (max 5)

**Interface:**
```typescript
interface HistoryItem {
  query: string;
  answer: string;
}
```

**Configuration:**
- `API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'`

**handleSubmit function:**
1. Validate non-empty query
2. Reset error/result, set loading true
3. POST to `${API_URL}/api/query` with `{"query": query.trim()}`
4. On success: set result, prepend to history (limit 5)
5. On error: set error message
6. Finally: set loading false

**UI Components:**
1. Header: "🔬 Deep Research AI Agent" with subtitle
2. Input container: text input + "Ask" button (shows "Searching..." when loading)
3. Loading indicator: spinner + message
4. Error display: red background
5. Result display: ReactMarkdown with remarkGfm plugin
6. History section: list of recent queries with markdown answers

**Features:**
- Enter key submits query
- Input disabled while loading
- Controlled input component

### File: `services/frontend/src/App.css`

**Styling Requirements:**

1. **Global Reset:**
   - `* { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Segoe UI', sans-serif; }`

2. **App Container:**
   - Gradient background: `linear-gradient(135deg, #1a2a6c, #b21f1f, #1a2a6c)`
   - Full viewport height, centered content

3. **Main Container:**
   - White/semi-transparent background with rounded corners (15px)
   - Box shadow for depth
   - Max width 800px, padding 30px

4. **Header:**
   - h1: color #1a2a6c, 2.5rem
   - Subtitle: color #666, 1.1rem

5. **Input Section:**
   - Flex layout with gap
   - Input: border 2px solid #ddd, focus border #1a2a6c
   - Button: gradient background, white text, hover effects
   - Disabled state: gray background, no pointer

6. **Loading Spinner:**
   - CSS animation rotating circle
   - Border with one colored side

7. **Result Container:**
   - Light gray background (#f8f9fa)
   - Markdown styles: headers, paragraphs, lists, tables, code, links, blockquotes

8. **Error Display:**
   - Red background (#ffe6e6), red text (#b21f1f)

9. **History Section:**
   - Cards with light background
   - Bold query, scrollable answer (max-height 150px)

10. **Responsive:**
    - @media max-width 600px: stack input vertically

### File: `services/frontend/src/main.tsx`

```typescript
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
```

### File: `services/frontend/src/index.css`

Basic reset styles (can be minimal since App.css handles most styling).

### File: `services/frontend/index.html`

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Web Search AI Agent</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

---

## Makefile

```makefile
.PHONY: dev-backend dev-frontend dev install-backend install-frontend install

dev-backend:
	cd services/backend && python3 main.py

dev-frontend:
	cd services/frontend && npm run dev

dev:
	@echo "Starting backend..."
	cd services/backend && python3 main.py &
	@echo "Starting frontend..."
	cd services/frontend && npm run dev

install-backend:
	cd services/backend && pip3 install -r requirements.txt

install-frontend:
	cd services/frontend && npm install

install: install-backend install-frontend
```

---

## API Reference

### POST /api/query

**Request:**
```json
{
  "query": "What are the latest developments in AI?"
}
```

**Response:**
```json
{
  "answer": "Based on recent search results, here are the latest AI developments..."
}
```

**Error Response (4xx/5xx):**
```json
{
  "detail": "Error message"
}
```

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ZEABUR_API_TOKEN` | Zeabur AI Hub API token | Required |
| `ZEABUR_MODEL` | LLM model name | `gpt-4o-mini` |
| `ZEABUR_BASE_URL` | LLM API base URL | `https://sfo1.aihub.zeabur.ai` |
| `BRIGHTDATA_API_TOKEN` | BrightData SERP API token | Required |
| `PORT` | Backend server port | `8000` |
| `VITE_API_URL` | Backend URL for frontend | `http://localhost:8000` |

---

## Running the Application

1. Install dependencies: `make install`
2. Configure `services/backend/.env` with your API tokens
3. Start backend: `make dev-backend` (runs on http://localhost:8000)
4. Start frontend: `make dev-frontend` (runs on http://localhost:5173)
5. Open http://localhost:5173 in browser
