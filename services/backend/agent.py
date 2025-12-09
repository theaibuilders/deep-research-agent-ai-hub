import json
from llm import NosanaLLM
from scraper import BrightDataScraper


class WebSearchAgent:
    def __init__(self, nosana_url: str, brightdata_token: str, model: str = None):
        self.llm = NosanaLLM(nosana_url, model)
        self.scraper = BrightDataScraper(brightdata_token)

    async def run(self, user_query: str) -> str:
        print(f"\n💭 User Query: {user_query}\n")
        
        # Validate input
        if not user_query or not isinstance(user_query, str) or not user_query.strip():
            print("❌ Invalid user query provided to WebSearchAgent:", user_query)
            return "Error: Invalid query provided."

        # Step 1: Determine if we need to search
        needs_search = await self._should_search(user_query)
        print(f"💡 Search needed: {'YES' if needs_search else 'NO'}")
        
        if not needs_search:
            print("📝 Answering directly without search...")
            return await self.llm.generate(user_query)

        # Step 2: Extract search query
        print("🔍 Determining what to search for...")
        search_query = await self._extract_search_query(user_query)
        print(f'🔑 Extracted search query: "{search_query}"')
        
        # Validate the extracted search query
        if not search_query or not isinstance(search_query, str) or not search_query.strip():
            print("❌ Invalid search query extracted:", search_query)
            return "Error: Could not extract a valid search query."
        
        # Step 3: Perform web search
        print("🚀 Executing web search...")
        search_results = await self._web_search(search_query.strip())
        print("🏁 Web search completed")
        
        # Log the raw search results for debugging
        print(f"📄 Raw search results preview: {search_results[:100]}...")
        
        # Step 4: Generate answer based on search results
        print("🧠 Generating answer from search results...")
        final_answer = await self._generate_answer(user_query, search_results)
        return final_answer

    async def _should_search(self, query: str) -> bool:
        print(f'📋 Evaluating if search is needed for: "{query}"')
        
        prompt = f"""Does this question require searching the web for current information? Answer only YES or NO.
    
Question: {query}

Answer:"""

        response = await self.llm.generate(prompt)
        
        result = "yes" in response.lower()
        print(f"📊 Evaluation result: {'SEARCH REQUIRED' if result else 'DIRECT ANSWER'}")
        
        return result

    async def _extract_search_query(self, query: str) -> str:
        print(f'📋 Extracting search query from: "{query}"')
        
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
        print(f'📡 Initiating search request for query: "{query}"')
        
        # Validate input query
        if not query or not isinstance(query, str) or not query.strip():
            print("❌ Invalid search query provided:", query)
            return "Error: Invalid search query provided."
        
        trimmed_query = query.strip()
        results = await self.scraper.search_web(trimmed_query)
        print(f'📨 Search request completed for query: "{trimmed_query}"')
        
        # Handle raw JSON response
        if not results:
            print("⚠️ No results found for query:", trimmed_query)
            return "No results found."
        
        # Check if results is an error object
        if isinstance(results, dict) and "error" in results:
            print(f"⚠️ Search returned error: {results['error']}")
            return f"Error: {results['error']}"
        
        # Check for empty results
        if isinstance(results, (list, dict)) and len(results) == 0:
            print("⚠️ Empty results for query:", trimmed_query)
            return "No results found."

        print(f'📬 Received raw results for query: "{trimmed_query}"')
        
        # Return the raw JSON as a string
        try:
            return json.dumps(results, indent=2)
        except Exception as e:
            print("❌ Failed to stringify raw results:", e)
            return "Error processing results."

    async def _generate_answer(self, original_query: str, search_results: str) -> str:
        print(f'📋 Generating final answer for: "{original_query}"')
        print(f"📎 With search results length: {len(search_results)} characters")
        
        # Check if we have an error message instead of results
        if search_results.startswith("Error:") or search_results == "No results found.":
            print("⚠️ Search returned an error or no results")
            # Extract the actual error message if present
            if search_results.startswith("Error:"):
                error_detail = search_results.replace("Error: ", "")
                return f'Search failed: {error_detail}'
            return f'I couldn\'t find information about "{original_query}" due to a search error. Please try rephrasing your question.'
        
        prompt = f"""Based on the following search results, answer the user's question accurately and concisely.

User Question: {original_query}

Search Results:
{search_results}

Answer:"""

        result = await self.llm.chat([
            {"role": "system", "content": "You are a helpful AI assistant that answers questions based on search results. Be concise and accurate."},
            {"role": "user", "content": prompt}
        ])
        
        print(f"📥 Received final answer from LLM ({len(result)} characters)")
        
        return result
