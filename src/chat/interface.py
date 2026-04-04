#!/usr/bin/env python3
"""Chat interface for JARVIS CLUSTER with network + tools integration."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Optional
import sys

logger = logging.getLogger("jarvis.chat")


class ChatInterface:
    """Main chat interface with persistent memory and context awareness."""
    
    def __init__(
        self,
        memory_file: str = None,
        network_available: bool = True,
    ):
        self._memory = __import__("src.chat.memory").ChatMemory(memory_file)
        
        self._network_available = network_available
        
        # Context tracking
        self._conversation_context: list[dict] = []
        self._task_history: dict = {}
    
    async def respond(self, query: str) -> str:
        """Generate response to user query."""
        logger.info(f"Processing: {query}")
        
        # Initialize task ID for tracking
        task_id = hash(query) % 10**6
        
        # Check if we have network access
        if self._network_available:
            try:
                from src.network.search import SearchEngine
                
                search_engine = SearchEngine()
                results = await search_engine.duckduckgo_search(query)
                
                if results:
                    snippet = f"🔍 Search results: {len(results)} found"
                    
                    # Show top result snippet
                    first_result = results[0]
                    snippet += f"\n   - {first_result.get('title', 'N/A')}"
                    
                    # Check weather if applicable
                    if any(term in query.lower() for term in ["weather", "météo", "température"]):
                        try:
                            import aiohttp
                            
                            async with aiohttp.ClientSession() as session:
                                async with session.get(
                                    "https://api.open-meteo.com/v1/forecast?latitude=48.8566&longitude=2.3522&current=temperature_2m,weather_code",
                                    timeout=10.0
                                ) as resp:
                                    if resp.status == 200:
                                        weather = await resp.json()
                                        temp_c = weather.get("current", {}).get("temperature_2m")
                                        
                                        if temp_c is not None:
                                            snippet += f"\n   🌤️ Weather in Paris: {temp_c}°C"
                        except Exception as e:
                            logger.warning(f"Weather query failed: {e}")
                    
                    # Check stocks if applicable
                    if any(term in query.lower() for term in ["stock", "bourse", "actions"]):
                        try:
                            result = await self._fetch_stocks(query)
                            
                            if result.get("success"):
                                price = result.get("price", "N/A")
                                change = result.get("changePercent", "N/A")
                                snippet += f"\n   📈 Stock: ${price} ({change})"
                        except Exception as e:
                            logger.warning(f"Stock query failed: {e}")
                    
                    # Check GitHub if applicable
                    if any(term in query.lower() for term in ["github", "repo"]):
                        try:
                            result = await self._search_github(query)
                            
                            if result.get("success") and result.get("repositories"):
                                repo_info = result["repositories"][0]
                                snippet += f"\n   🐙 GitHub: {repo_info['name']} (★{repo_info.get('stargazers_count', 'N/A')})"
                        except Exception as e:
                            logger.warning(f"GitHub search failed: {e}")
                
            except ImportError:
                logger.info("Network search not available - using text response only")
            
            # Add to memory
            self._memory.add_message("system", snippet)
        
        return f"\n{snippet}\n\n" + self._generate_text_response(query, results if "results" in dir() else None)
    
    async def respond_with_tools(
        self,
        query: str,
        available_tools: list[str],
    ) -> str:
        """Generate response with tool execution."""
        logger.info(f"Processing with tools: {query}")
        
        # Check calculator
        if any(term in query.lower() for term in ["+", "-", "*", "/", "calculate", "math"]):
            try:
                from src.tools.calculator import Calculator
                
                calc = Calculator()
                result = await calc.evaluate(query)
                
                if result["success"]:
                    return f"\n{result['result']}\n" + self._generate_text_response(query, result)
                else:
                    return f"\nError: {result.get('error', 'Unknown error')}\n"
            except Exception as e:
                logger.warning(f"Calculator failed: {e}")
        
        # Check code execution
        if any(term in query.lower() for term in ["python", "code", "script"]):
            try:
                from src.tools.code_executor import CodeExecutor
                
                executor = CodeExecutor()
                result = await executor.execute(query)
                
                if result["success"]:
                    return f"\n{result['output']}\n" + self._generate_text_response(query, result)
                else:
                    return f"\nError: {result.get('error', 'Unknown error')}\n"
            except Exception as e:
                logger.warning(f"Code executor failed: {e}")
        
        # Fallback to search if network available
        if self._network_available:
            try:
                from src.network.search import SearchEngine
                
                search_engine = SearchEngine()
                results = await search_engine.duckduckgo_search(query)
                
                if results:
                    snippet = f"🔍 Found {len(results)} results for '{query}'\n"
                    
                    # Add top result details
                    for i, result in enumerate(results[:2], 1):
                        title = result.get('title', 'No title')
                        url = result.get('url', 'N/A')
                        snippet += f"\n{i}. {title}\n   URL: {url}"
                    
                    # Get first snippet if available
                    if len(results) > 0 and "snippet" in results[0]:
                        snippet += f"\n   {results[0]['snippet'][:200]}..."
                    
                    self._memory.add_message("system", snippet)
                    
                    return snippet + "\n\nWould you like me to search another source or help with something else?"
                
            except Exception as e:
                logger.warning(f"Search failed: {e}")
        
        # Default text response
        return f"\nI've processed your request about '{query}'. " \
               f"If I need more information, please let me know!\n\n" \
               f"Available tools: {', '.join(available_tools)}\n" \
               f"Try asking about weather, stocks, or use calculator for math!"


    async def _fetch_stocks(self, symbol: str) -> dict[str, Any]:
        """Fetch stock data (requires Finnhub API key)."""
        try:
            import finnhub
            
            client = finnhub.Client(api_key=os.getenv("FINNHUB_API_KEY", ""))
            stock = client.stock_quote(symbol=symbol.lower(), region="us")
            
            return {
                "success": True,
                "price": stock.get("c", "N/A"),
                "changePercent": f"{stock.get('d', 0):.2f}" if stock else "N/A",
            }
        except Exception as e:
            logger.warning(f"Stock fetch failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _search_github(self, query: str) -> dict[str, Any]:
        """Search GitHub repositories (requires GitHub token)."""
        try:
            import aiohttp
            
            headers = {
                "Accept": "application/vnd.github.v3+json",
            }
            
            if not os.getenv("GITHUB_TOKEN"):
                # Use anonymous search
                url = "https://api.github.com/search/repositories"
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, params={"q": query}, timeout=10.0) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            
                            return {
                                "success": True,
                                "repositories": [
                                    {
                                        "name": item.get("name"),
                                        "owner": item.get("owner", {}).get("login"),
                                        "full_name": item.get("full_name"),
                                        "description": item.get("description", ""),
                                        "stargazers_count": item.get("stargazers_count"),
                                    }
                                    for item in data.get("items", [])[:3]
                                ],
                            }
            
            return {"success": True, "repositories": []}
        except Exception as e:
            logger.warning(f"GitHub search failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _generate_text_response(
        self,
        query: str,
        context_data: Optional[dict] = None,
    ) -> str:
        """Generate contextual text response."""
        responses = {
            "weather": "🌤️  I can check the weather for you! Try asking 'What's the temperature in Paris?'",
            "stock": "📈 I can provide stock information! Try asking about Apple (AAPL) stock.",
            "github": "🐙 I can search GitHub repositories! Try asking about 'react github repos'.",
            "calculator": "🧮 I'm a calculator! Try: 2+2*3 or any math expression.",
        }
        
        for key, text in responses.items():
            if any(term in query.lower() for term in key.split()):
                return text
        
        # Default response
        return f"Done processing your request about: {query}"


# Singleton instance
_default_interface = ChatInterface(
    memory_file="/home/turbo/Workspaces/JARVIS-CLUSTER/data/chat_memory.json",
    network_available=True,
)


def get_chat_interface() -> ChatInterface:
    """Get the default chat interface instance."""
    return _default_interface
