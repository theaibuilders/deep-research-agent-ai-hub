"""
============================================================================
DEEP RESEARCH AI AGENT - PYTHON IMPLEMENTATION
============================================================================

This file implements the core AI Agent pattern in Python. It mirrors the
TypeScript version but uses Python's async/await syntax.

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
        
        DEPENDENCY INJECTION:
        - Pass in credentials instead of hardcoding
        - Allows for different configurations (dev/prod)
        - Makes testing easier
        
        Args:
            zeabur_api_key: API key for Zeabur AI Hub
            brightdata_token: API token for BrightData SERP
            model: Optional model name override
        """
        # Initialize the LLM client - our "brain"
        self.llm = ZeaburLLM(api_key=zeabur_api_key, model=model)
        
        # Initialize the scraper - our "eyes" for the web
        self.scraper = BrightDataScraper(brightdata_token)

    async def run(self, user_query: str, use_web_search: bool = True) -> str:
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
            use_web_search: Whether to use web search (defaults to True)
            
        Returns:
            str: The agent's response
        """
        print(f"\n💭 User Query: {user_query}")
        print(f"🌐 Web Search: {'ENABLED' if use_web_search else 'DISABLED'}\n")
        
        # INPUT VALIDATION: Always validate at the boundary
        if not user_query or not isinstance(user_query, str) or not user_query.strip():
            print("❌ Invalid user query provided to WebSearchAgent:", user_query)
            return "Error: Invalid query provided."

        # CHECK USER PREFERENCE: If web search is disabled, answer directly
        if not use_web_search:
            print("📝 Web search disabled by user - answering directly with LLM...")
            return await self.llm.generate(user_query)

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
        """
        Determine if a web search is needed for this query.
        
        PROMPT ENGINEERING: Classification Prompt
        - Ask LLM a simple YES/NO question
        - Constrains output for reliable parsing
        - Saves cost/time when search isn't needed
        
        EXAMPLES:
        - "What is 2+2?" -> NO (general knowledge)
        - "What's Bitcoin price today?" -> YES (real-time data)
        - "Who won the Super Bowl 2024?" -> YES (recent events)
        
        Args:
            query: The user's original question
            
        Returns:
            bool: True if web search is needed
        """
        print(f'📋 Evaluating if search is needed for: "{query}"')
        
        # CLASSIFICATION PROMPT: Clear instruction with constrained output
        prompt = f"""Does this question require searching the web for current information? Answer only YES or NO.
    
Question: {query}

Answer:"""

        response = await self.llm.generate(prompt)
        
        # Simple parsing - check if 'yes' appears (case-insensitive)
        # More robust than exact string matching
        result = "yes" in response.lower()
        print(f"📊 Evaluation result: {'SEARCH REQUIRED' if result else 'DIRECT ANSWER'}")
        
        return result

    async def _extract_search_query(self, query: str) -> str:
        """
        Extract optimal search keywords from natural language.
        
        PROMPT ENGINEERING: Extraction Prompt
        - Transform verbose questions into concise search terms
        - LLM understands intent and extracts key concepts
        
        EXAMPLE TRANSFORMATIONS:
        - "Can you tell me what the weather is like in NYC?" -> "weather NYC"
        - "I want to know about recent AI developments" -> "recent AI developments 2024"
        
        Args:
            query: The user's natural language question
            
        Returns:
            str: Optimized search keywords (3-6 words)
        """
        print(f'📋 Extracting search query from: "{query}"')
        
        # EXTRACTION PROMPT with constraints
        # "3-6 words" prevents overly long or short queries
        prompt = f"""Extract a concise search query (3-6 words) from this question:

Question: {query}

Search query:"""

        print("📤 Sending extraction prompt to LLM...")
        response = await self.llm.generate(prompt)
        print(f'📥 Received LLM response: "{response}"')
        
        # Clean up response
        result = response.strip()
        print(f'🔑 Final extracted search query: "{result}"')
        
        return result

    async def _web_search(self, query: str) -> str:
        """
        Execute web search and return results as string.
        
        This is the "Tool" execution - the action the agent takes.
        
        ERROR HANDLING:
        - Validate input before making API call
        - Handle empty results gracefully
        - Return string format for LLM consumption
        
        Args:
            query: Search keywords
            
        Returns:
            str: JSON string of search results, or error message
        """
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
        """
        Generate final answer using RAG (Retrieval-Augmented Generation).
        
        RAG PATTERN:
        1. Retrieval: We already have search results
        2. Augmentation: Inject results into prompt as context
        3. Generation: LLM generates answer grounded in facts
        
        PROMPT STRUCTURE:
        - System prompt: Defines assistant behavior
        - User content: Question + Context (search results)
        - Clear instruction: "Answer based on search results"
        
        Args:
            original_query: The user's original question
            search_results: JSON string of search results
            
        Returns:
            str: The synthesized answer
        """
        print(f'📋 Generating final answer for: "{original_query}"')
        print(f"📎 With search results length: {len(search_results)} characters")
        
        # Handle error cases - don't try to synthesize from errors
        if search_results.startswith("Error:") or search_results == "No results found.":
            print("⚠️ Search returned an error or no results")
            if search_results.startswith("Error:"):
                error_detail = search_results.replace("Error: ", "")
                return f'Search failed: {error_detail}'
            return f'I couldn\'t find information about "{original_query}" due to a search error. Please try rephrasing your question.'
        
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
