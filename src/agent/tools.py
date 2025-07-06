import asyncio
import json
import os
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
import aiohttp
from langchain_core.tools import BaseTool
from pydantic import PrivateAttr


class GoogleCustomSearchTool(BaseTool):
    """Google Custom Search API tool."""
    
    name: str = "google_custom_search"
    description: str = "Search the web using Google Custom Search API"
    _api_key: Optional[str] = PrivateAttr()
    _cx: Optional[str] = PrivateAttr()
    _endpoint: str = PrivateAttr(default="https://www.googleapis.com/customsearch/v1")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._api_key = os.getenv("GOOGLE_CSE_API_KEY")
        self._cx = os.getenv("GOOGLE_CSE_CX")
        
    async def _arun(self, query: str) -> List[Dict[str, Any]]:
        """Async search using Google Custom Search API."""
        if not self._api_key or not self._cx:
            raise ValueError("GOOGLE_CSE_API_KEY and GOOGLE_CSE_CX must be set in environment")
            
        params = {
            "key": self._api_key,
            "cx": self._cx,
            "q": query,
            "num": 5
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(self._endpoint, params=params) as response:
                if response.status == 429:
                    raise Exception("Rate limit exceeded")
                elif response.status != 200:
                    raise Exception(f"Search failed with status {response.status}")
                    
                data = await response.json()
                results = []
                for item in data.get("items", []):
                    results.append({
                        "title": item.get("title", ""),
                        "snippet": item.get("snippet", ""),
                        "url": item.get("link", ""),
                        "query": query,
                        "mock": False
                    })
                return results

    def _run(self, query: str) -> List[Dict[str, Any]]:
        """Sync wrapper for async search."""
        return asyncio.run(self._arun(query))


class MockWebSearchTool(BaseTool):
    """Mock web search tool for testing and offline use."""
    
    name: str = "mock_web_search"
    description: str = "Mock web search for testing purposes"
    _mock_data: Dict[str, List[Dict[str, Any]]] = PrivateAttr()
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._mock_data = {
            "python programming": [
                {
                    "title": "Python Programming Language",
                    "snippet": "Python is a high-level, interpreted programming language known for its simplicity and readability.",
                    "url": "https://python.org",
                    "query": "python programming"
                },
                {
                    "title": "Learn Python - Tutorials",
                    "snippet": "Comprehensive tutorials and documentation for learning Python programming.",
                    "url": "https://docs.python.org",
                    "query": "python programming"
                }
            ],
            "machine learning": [
                {
                    "title": "Machine Learning Basics",
                    "snippet": "Machine learning is a subset of artificial intelligence that enables computers to learn without explicit programming.",
                    "url": "https://ml-basics.com",
                    "query": "machine learning"
                },
                {
                    "title": "Introduction to ML",
                    "snippet": "A comprehensive introduction to machine learning concepts and algorithms.",
                    "url": "https://ml-intro.org",
                    "query": "machine learning"
                }
            ],
            "artificial intelligence": [
                {
                    "title": "What is Artificial Intelligence",
                    "snippet": "Artificial Intelligence (AI) refers to the simulation of human intelligence in machines.",
                    "url": "https://ai-definition.org",
                    "query": "artificial intelligence"
                },
                {
                    "title": "AI Applications",
                    "snippet": "Real-world applications of artificial intelligence in various industries.",
                    "url": "https://ai-applications.com",
                    "query": "artificial intelligence"
                }
            ],
            "world cup 2022": [
                {
                    "title": "Argentina win World Cup 2022",
                    "snippet": "Argentina won the 2022 FIFA World Cup, beating France 4-2 on penalties after a 3-3 draw in extra time.",
                    "url": "https://www.fifa.com/worldcup/news/argentina-win",
                    "query": "world cup 2022"
                },
                {
                    "title": "FIFA World Cup 2022 Final",
                    "snippet": "The 2022 FIFA World Cup final was played between Argentina and France on December 18, 2022, at Lusail Stadium in Qatar.",
                    "url": "https://fifa-world-cup-2022.com/final",
                    "query": "world cup 2022"
                }
            ],
            "argentina goals 2022 final": [
                {
                    "title": "Argentina Goals in 2022 World Cup Final",
                    "snippet": "Argentina scored 3 goals in the 2022 World Cup final: Messi (2) and Di Maria (1).",
                    "url": "https://argentina-goals-2022.com",
                    "query": "argentina goals 2022 final"
                }
            ],
            "france goals 2022 final": [
                {
                    "title": "France Goals in 2022 World Cup Final",
                    "snippet": "France scored 3 goals in the 2022 World Cup final: Mbappe (3) including a hat-trick.",
                    "url": "https://france-goals-2022.com",
                    "query": "france goals 2022 final"
                }
            ],
            "who won the 2022 fifa world cup": [
                {
                    "title": "Argentina win World Cup 2022",
                    "snippet": "Argentina won the 2022 FIFA World Cup, beating France 4-2 on penalties after a 3-3 draw in extra time.",
                    "url": "https://www.fifa.com/worldcup/news/argentina-win",
                    "query": "who won the 2022 fifa world cup"
                }
            ]
        }
    
    async def _arun(self, query: str) -> List[Dict[str, Any]]:
        """Async mock search."""
        # Simulate network delay
        await asyncio.sleep(0.1)
        
        # Find best matching mock data
        query_lower = query.lower()
        for key, results in self._mock_data.items():
            if key in query_lower or query_lower in key:
                # Add mock flag to each result
                return [dict(r, mock=True) for r in results]
        
        # Return generic results if no match
        return [
            {
                "title": f"Search Results for: {query}",
                "snippet": f"This is a mock result for the query: {query}. In a real implementation, this would contain actual search results.",
                "url": f"https://mock-search.com/results?q={query}",
                "query": query,
                "mock": True
            }
        ]
    
    def _run(self, query: str) -> List[Dict[str, Any]]:
        """Sync wrapper for async mock search."""
        return asyncio.run(self._arun(query))


def get_search_tool() -> BaseTool:
    """Get the appropriate search tool based on environment."""
    if os.getenv("GOOGLE_CSE_API_KEY") and os.getenv("GOOGLE_CSE_CX"):
        return GoogleCustomSearchTool()
    else:
        return MockWebSearchTool()


async def search_multiple_queries(queries: List[str]) -> List[Dict[str, Any]]:
    """Search multiple queries concurrently and merge results."""
    search_tool = get_search_tool()
    
    # Run searches concurrently
    tasks = [search_tool._arun(query) for query in queries]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Merge and deduplicate results
    all_docs = []
    seen_urls = set()
    
    for result in results:
        if isinstance(result, Exception):
            print(f"Search error: {result}")
            continue
            
        for doc in result:
            url = doc.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                all_docs.append(doc)
    
    return all_docs 