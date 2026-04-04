"""Vector store aggregator - combines multiple vector stores for search."""

from __future__ import annotations

import logging
from typing import Any, Optional

logger = logging.getLogger("jarvis.vector")


class VectorStoreAggregator:
    """Aggregates results from multiple vector store backends."""
    
    def __init__(self, config=None):
        self._config = config or type('Config', (), {})()
        self._stores: dict[str, Any] = {}
        self._weights: dict[str, float] = {
            "chroma": 0.6,
            "sqlite": 0.25,
            "pinecone": 0.15,
        }
    
    def add_store(
        self,
        store_name: str,
        store: Any,
        weight: float = None,
    ) -> None:
        """Add a vector store with optional weight."""
        self._stores[store_name] = store
        if weight is not None:
            self._weights[store_name] = weight
    
    def clear_stores(self) -> None:
        """Remove all registered stores."""
        self._stores.clear()
    
    async def search(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """Search across all enabled vector stores and aggregate results."""
        all_results: list[dict[str, Any]] = []
        
        for store_name, store in self._stores.items():
            try:
                # Calculate effective top_k based on weight
                effective_k = int(top_k * (self._weights.get(store_name, 1.0) / 1.0))
                
                results = await search_async(
                    query=query,
                    store=store,
                    k=effective_k if effective_k > 0 else top_k,
                )
                
                for result in results:
                    result["_weight"] = self._weights.get(store_name, 1.0)
                    all_results.append(result)
            except Exception as e:
                logger.warning(f"Search failed on store {store_name}: {e}")
        
        # Sort by distance (ascending) and deduplicate by URL
        all_results.sort(key=lambda x: x.get("distance", 1.0))
        
        seen_urls = set()
        deduplicated = []
        for result in all_results[:top_k * 2]:
            url = result.get("metadata", {}).get("url") or ""
            content = result.get("content", "")
            
            if url and url not in seen_urls:
                seen_urls.add(url)
                deduplicated.append(result)
            elif content and len(deduplicated) < top_k * 2:
                deduplicated.append({**result, "_source": "inline"})
        
        return deduplicated[:top_k]


async def search_async(
    query: str,
    store: Any,
    k: int = 5,
) -> list[dict[str, Any]]:
    """Generic async search interface."""
    if hasattr(store, "search"):
        return await store.search(query=query, top_k=k)
    
    # Fallback to inline parsing
    from src.vector_store.sqlite import SQLiteVectorStore
    
    store = SQLiteVectorStore.from_query(
        query=query,
        collection_name="knowledge_base",
        db_path="/home/turbo/Workspaces/JARVIS-CLUSTER/data/vqdb.db"
    )
    
    return []

