import httpx
from typing import Dict, Any
from urllib.parse import quote


class BrightDataScraper:
    def __init__(self, api_token: str, zone: str = "serp_api1"):
        self.api_token = api_token
        self.base_url = "https://api.brightdata.com"
        self.zone = zone

    async def search_web(self, query: str) -> Dict[str, Any]:
        try:
            search_url = f"https://www.google.com/search?q={quote(query)}&hl=en&gl=us"
            
            request_body = {
                "zone": self.zone,
                "url": search_url,
                "format": "json",
                "data_format": "parsed_light"
            }
            
            print(f"🔍 Searching BrightData for: {query}")
            print(f"📡 Request URL: {self.base_url}/request")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/request",
                    json=request_body,
                    headers={
                        "Authorization": f"Bearer {self.api_token}",
                        "Content-Type": "application/json"
                    },
                    params={"brd_json": 1}
                )
                
                print(f"📥 Response status: {response.status_code}")
                
                # Check for HTTP errors
                if response.status_code == 401:
                    print("❌ BrightData API error: 401 Unauthorized")
                    print("📄 Response:", response.text[:200])
                    return {"error": "BrightData API authentication failed. Please check your BRIGHTDATA_API_TOKEN in .env file. Get your API key from: https://brightdata.com/cp/setting/users"}
                
                if response.status_code >= 400:
                    print(f"❌ BrightData API error: {response.status_code}")
                    print(f"📄 Response: {response.text[:500]}")
                    return {"error": f"API returned status {response.status_code}"}
                
                if not response.text:
                    print("⚠️ Empty response from BrightData")
                    return {"error": "Empty response from API"}
                
                data = response.json()
                print(f"📦 Response keys: {list(data.keys()) if isinstance(data, dict) else 'not a dict'}")
                
                # Return the body directly as JSON without any parsing
                if data and "body" in data:
                    body = data["body"]
                    if isinstance(body, dict) and "organic" in body:
                        print(f"✅ Found {len(body.get('organic', []))} organic results")
                    elif isinstance(body, list):
                        print(f"✅ Found {len(body)} results")
                    return body
                
                # If no body exists, return the entire response data
                print(f"⚠️ No 'body' in response, returning full data")
                return data
                
        except httpx.HTTPStatusError as e:
            print(f"❌ BrightData Scraper Error: Status {e.response.status_code}")
            print(f"📄 Response Data: {e.response.text[:500]}")
            return {"error": f"HTTP error: {e.response.status_code}"}
        except Exception as e:
            print(f"❌ BrightData Scraper Error: {type(e).__name__}: {e}")
            return {"error": str(e)}
