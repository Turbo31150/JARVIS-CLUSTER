"""Knowledge base + external tools integration."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("jarvis.knowledge")


class KnowledgeBase:
    """External knowledge retrieval with multiple sources."""
    
    def __init__(self):
        self._kb_sources: dict[str, dict[str, Any]] = {}
        self._initialize_default_sources()
    
    def _initialize_default_sources(self) -> None:
        """Initialize default knowledge sources from environment config."""
        import os
        
        # Check for environment variables and initialize sources
        tools_config = {
            "calculator": {
                "enabled": True,
                "type": "python_exec",
                "max_execution_time_s": 10,
            },
            "code_executor": {
                "enabled": os.getenv("ENABLE_CODE_EXECUTOR") == "true" or True,
                "sandbox": True,
                "timeout_s": 30,
            },
            "weather": {
                "enabled": bool(os.getenv("WEATHER_API_KEY")),
                "api_key": os.getenv("WEATHER_API_KEY", ""),
                "default_provider": "open_meteo",
            },
            "stocks": {
                "enabled": bool(os.getenv("FINNHUB_API_KEY")),
                "api_key": os.getenv("FINNHUB_API_KEY", ""),
                "symbols": [],
            },
            "github": {
                "enabled": bool(os.getenv("GITHUB_TOKEN")),
                "token": os.getenv("GITHUB_TOKEN", ""),
                "rate_limit_calls": True,
            },
        }
        
        # Parse comma-separated tools from env if provided
        tools_env = os.getenv("ENABLED_TOOLS", "")
        if tools_env:
            enabled_tools = [t.strip() for t in tools_env.split(",")]
            for tool_name, tool_config in tools_config.items():
                if tool_name in enabled_tools and not tool_config["enabled"]:
                    tool_config["enabled"] = True
        
        self._kb_sources = {
            "wikipedia": {"type": "external", "api": search_engine.wiki_search},
            "duckduckgo": {"type": "external", "api": search_engine.duckduckgo_search},
            "google": {"type": "external", "api": search_engine.google_search} if tools_config["code_executor"]["enabled"] else None,
        }
        
        for tool_name, tool_config in tools_config.items():
            if tool_config.get("enabled"):
                self._kb_sources[tool_name] = {
                    "type": "external",
                    "config": tool_config,
                }
    
    async def retrieve(
        self,
        query: str,
        sources: list[str] | None = None,
        max_results: int = 10,
    ) -> dict[str, Any]:
        """Retrieve information from configured knowledge sources."""
        if not sources:
            # Use all enabled sources
            sources = [name for name in self._kb_sources.keys() if self._kb_sources[name]["enabled"]]
        
        results: dict[str, list[dict]] = {}
        combined_results: list[dict] = []
        
        for source_name in sources:
            source_config = self._kb_sources.get(source_name)
            if not source_config or not source_config["enabled"]:
                continue
            
            try:
                result_list = await source_config["api"](query)
                if result_list:
                    results[source_name] = result_list
                    combined_results.extend(result_list)
            except Exception as e:
                logger.warning(f"Knowledge source {source_name} failed for query '{query[:50]}...': {e}")
        
        # Remove duplicates and return top results
        seen_urls = set()
        deduplicated = []
        for result in combined_results[:max_results * 2]:  # Get more than requested, then dedupe
            url = result.get("url", "")
            if url not in seen_urls:
                seen_urls.add(url)
                deduplicated.append(result)
        
        return {
            "query": query,
            "sources_used": list(results.keys()),
            "results_count": len(deduplicated),
            "results": deduplicated[:max_results],
        }
    
    def get_available_sources(self) -> list[str]:
        """Return list of available knowledge sources."""
        return [name for name, config in self._kb_sources.items() if config.get("enabled")]


# Singleton instance
knowledge_base = KnowledgeBase()
