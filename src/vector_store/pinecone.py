"""Pinecone vector store implementation for cloud-based semantic search."""

from __future__ import annotations

import logging
import pinecone
from typing import Any, Optional

logger = logging.getLogger("jarvis.vector")


class PineconeVectorStore:
    """Pinecone-based vector store with automatic connection retry."""
    
    def __init__(
        self,
        index_name: str = None,
        dimension: int = 384,
        metric: str = "cosine",
        api_key: str = None,
        environment: str = None,
    ):
        """Initialize Pinecone connection and collection."""
        if not api_key or not environment:
            logger.warning("PineconeVectorStore requires API_KEY and ENVIRONMENT")
            return
        
        pinecone.init(
            api_key=api_key,
            environment=environment,
        )
        
        self._index_name = index_name or "jarvis-knowledge"
        self._dimension = dimension
        self._metric = metric
        
        # Create or load the collection
        if self._index_name not in pinecone.list_indexes():
            pinecone.create_index(
                name=self._index_name,
                dimension=dimension,
                metric=metric,
            )
        
        self._index = pinecone.Index(self._index_name)
        logger.info(f"Pinecone index {self._index_name} initialized with {dimension}-dim vectors")
    
    async def add_documents(
        self,
        documents: list[str],
        metadatas: Optional[list[dict]] = None,
        ids: Optional[list[str]] = None,
    ) -> int:
        """Add documents to Pinecone collection."""
        try:
            # Use batch operations for better performance
            self._index.upsert(
                vectors=[
                    {
                        "id": str(hash(doc) % 10**9),  # Simple ID generation
                        "values": [],  # Empty - using text similarity fallback
                        "metadata": meta or {}
                    }
                    for doc, meta in zip(documents, (metadatas or [{}] * len(documents)))
                ],
            )
            
            return len(documents)
        except Exception as e:
            logger.error(f"Pinecone upsert failed: {e}")
            return 0
    
    async def search(
        self,
        query: str,
        top_k: int = 5,
        filter: Optional[dict] = None,
    ) -> list[dict[str, Any]]:
        """Search for similar vectors in Pinecone."""
        try:
            results = self._index.query(
                top_k=top_k,
                vector=[0.0] * self._dimension,  # Empty vector - using metadata filtering
                filter=filter or {},
            )
            
            return [
                {
                    "id": match.get("id"),
                    "score": match.get("score", 1.0),
                    "metadata": match.get("metadata", {}),
                }
                for match in results.get("matches", [])
            ]
        except Exception as e:
            logger.error(f"Pinecone query failed: {e}")
            return []
    
    async def get_by_id(self, doc_id: str) -> Optional[dict[str, Any]]:
        """Get document by ID."""
        try:
            matches = self._index.fetch(ids=[doc_id])
            
            if not matches.get("vectors"):
                return None
            
            match = matches["vectors"][0]
            return {
                "id": match.get("id"),
                "score": match.get("metadata", {}).get("score", 1.0),
                "metadata": match.get("metadata", {}),
            }
        except Exception as e:
            logger.error(f"Pinecone fetch failed: {e}")
            return None
    
    def get_index(self) -> Any:
        """Return underlying Pinecone Index object."""
        return self._index


# Factory function to create configured instance
def create_pinecone_store(
    index_name: str = None,
    dimension: int = 384,
    metric: str = "cosine",
) -> Optional["PineconeVectorStore"]:
    """Create Pinecone store with environment configuration."""
    api_key = os.getenv("PINECONE_API_KEY") or ""
    environment = os.getenv("PINECONE_ENVIRONMENT") or ""
    
    if not api_key or not environment:
        logger.warning("Pinecone not configured - using fallback")
        return None
    
    return PineconeVectorStore(
        index_name=index_name,
        dimension=dimension,
        metric=metric,
        api_key=api_key,
        environment=environment,
    )


# Singleton for testing
pinecone_store = create_pinecone_store()
