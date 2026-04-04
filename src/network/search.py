"""Web search + knowledge base queries."""

from __future__ import annotations

import logging
from typing import Any, Optional

logger = logging.getLogger("jarvis.search")


class SearchEngine:
    """Unified web search interface with multiple providers."""
    
    def __init__(self):
        self._default_engine = "duckduckgo"  # Default to privacy-friendly engine
    
    async def duckduckgo_search(
        self,
        query: str,
        max_results: int = 10,
        safe_search: str = "moderate",
    ) -> list[dict[str, Any]] | None:
        """DuckDuckGo search (no API key required)."""
        from src.network.requests import get_json
        
        query_url = f"https://api.duckduckgo.com/?q={query.replace(' ', '+')}&format=json&max_results={max_results}&safe_search={safe_search}"
        
        try:
            result = await get_json(query_url, max_retries=3)
            if result and "Results" in result:
                return [
                    {
                        "title": item.get("Title"),
                        "url": item.get("href", ""),
                        "snippet": item.get("Abstract"),
                        "date": item.get("Date"),
                    }
                    for item in result["Results"][:max_results]
                ]
        except Exception as e:
            logger.error(f"DuckDuckGo search failed: {e}")
        
        return None
    
    async wiki_search(
        self,
        query: str,
        max_results: int = 5,
    ) -> list[dict[str, Any]] | None:
        """Wikipedia API search."""
        from src.network.requests import get_json
        
        # Clean query for API
        clean_query = query.replace(" ", "%20").replace(".", "")
        search_url = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={clean_query}&limit={max_results}&namespace=0&origin=*&format=json"
        
        try:
            result = await get_json(search_url, max_retries=3)
            if result and len(result) > 1:
                return [
                    {
                        "title": title,
                        "url": f"https://en.wikipedia.org/wiki/{term.replace(' ', '_')}",
                        "snippet": snippet,
                    }
                    for title, snippet, term in zip(result[1], result[2], result[3])
                ]
        except Exception as e:
            logger.error(f"Wikipedia search failed: {e}")
        
        return None
    
    async def google_search(
        self,
        query: str,
        api_key: Optional[str] = None,
        cse_id: Optional[str] = None,
        max_results: int = 10,
    ) -> list[dict[str, Any]] | None:
        """Google Custom Search API (requires API key + CSE ID)."""
        if not api_key or not cse_id:
            logger.warning("Google search requires API_KEY and GOOGLE_CSE_ID environment variables")
            return None
        
        query_url = f"https://www.googleapis.com/customsearch/v1?key={api_key}&cx={cse_id}&q={query}"
        
        try:
            result = await get_json(query_url, max_retries=3)
            if result and "items" in result:
                return [
                    {
                        "title": item.get("title"),
                        "url": item.get("link", ""),
                        "snippet": item.get("snippet"),
                    }
                    for item in result["items"][:max_results]
                ]
        except Exception as e:
            logger.error(f"Google search failed: {e}")
        
        return None


# Singleton instance
search_engine = SearchEngine()
