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
                    return {"error": "BrightData API authentication failed. Please check your BRIGHTDATA_API_TOKEN in .env file. Get your API key from: https://brightdata.com/cp/setting/users"}
                
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
