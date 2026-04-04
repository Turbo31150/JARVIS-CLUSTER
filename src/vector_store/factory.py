"""Vector store factory for configuration-based instantiation."""

from __future__ import annotations

import logging
from typing import Any, Optional, Union

logger = logging.getLogger("jarvis.factory")


def create_vector_store(
    store_type: str = "chroma",
    collection_name: str = None,
) -> Union["ChromaVectorStore", "PineconeVectorStore"]:
    """Factory function to create vector store instances based on configuration."""
    
    from src.vector_store.chroma import ChromaVectorStore
    from src.network.knowledge import knowledge_base
    
    if store_type.lower() == "chromadb":
        return ChromaVectorStore(
            collection_name=collection_name or "jarvis_knowledge_base",
            persistent_path="/home/turbo/Workspaces/JARVIS-CLUSTER/vector_store/chroma",
        )
    
    elif store_type.lower() == "pinecone":
        from src.vector_store.pinecone import PineconeVectorStore
        
        pinecone_config = {
            "api_key": os.getenv("PINECONE_API_KEY", ""),
            "environment": os.getenv("PINECONE_ENVIRONMENT", ""),
            "index_name": os.getenv("PINECONE_INDEX_NAME", "jarvis-knowledge"),
        }
        
        if pinecone_config["api_key"] and pinecone_config["environment"]:
            return PineconeVectorStore(
                index=pincone_config["index_name"],
                dimension=384,  # All-MiniLM-L6-v2 outputs 384-dim vectors
                metric="cosine",
            )
        else:
            logger.warning("Pinecone not configured (missing API key or environment)")
            return None
    
    elif store_type.lower() == "sqlite":
        from src.vector_store.sqlite import SQLiteVectorStore
        
        return SQLiteVectorStore(
            db_path="/home/turbo/Workspaces/JARVIS-CLUSTER/data/vqdb.db",
            collection_name="knowledge_base",
        )
    
    else:
        logger.error(f"Unknown vector store type: {store_type}")
        return ChromaVectorStore()  # Default fallback


def get_knowledge_store(config) -> Optional[Any]:
    """Get configured knowledge store based on environment settings."""
    from src.vector_store.config import VectorStoreConfig
    
    config = config or VectorStoreConfig()
    
    # Check Pinecone first (most powerful for semantic search)
    if config.get_pinecone_config().get("enabled"):
        return create_vector_store(store_type="pinecone")
    
    # Fall back to ChromaDB
    return create_vector_store(store_type="chromadb")


# Default knowledge store instance
default_knowledge_store = get_knowledge_store()
