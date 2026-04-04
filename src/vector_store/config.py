"""Vector store configuration."""

import os
from typing import Any, Optional


class VectorStoreConfig:
    """Configuration for all vector store implementations."""
    
    def __init__(self):
        # ChromaDB settings
        self._chromadb_persistent_path = os.getenv(
            "CHROMADB_PERSISTENT_PATH", 
            "/home/turbo/Workspaces/JARVIS-CLUSTER/vector_store/chroma"
        )
        
        self._chromadb_collection_name = os.getenv(
            "CHROMADB_COLLECTION_NAME",
            "jarvis_knowledge_base"
        )
        
        # Embedding model settings
        self._embedding_model = os.getenv(
            "EMBEDDING_MODEL",
            "all-MiniLM-L6-v2"  # Fast, lightweight embeddings
        )
        
        # Pinecone settings
        self._pinecone_api_key = os.getenv("PINECONE_API_KEY", "")
        self._pinecone_environment = os.getenv("PINECONE_ENVIRONMENT", "")
        self._pinecone_index_name = os.getenv(
            "PINECONE_INDEX_NAME", 
            "jarvis-knowledge"
        )
        
        # SQLite vector store settings
        self._sqlite_db_path = os.getenv(
            "VQDB_DATABASE_PATH",
            "/home/turbo/Workspaces/JARVIS-CLUSTER/data/vqdb.db"
        )
    
    def get_chroma_config(self) -> dict[str, Any]:
        """Return ChromaDB configuration."""
        return {
            "path": self._chromadb_persistent_path,
            "collection_name": self._chromadb_collection_name,
            "embedding_model": self._embedding_model,
        }
    
    def get_pinecone_config(self) -> dict[str, Any]:
        """Return Pinecone configuration."""
        if not self._pinecone_api_key or not self._pinecone_environment:
            return {"enabled": False, "reason": "Missing Pinecone credentials"}
        
        return {
            "api_key": self._pinecone_api_key,
            "environment": self._pinecone_environment,
            "index_name": self._pinecone_index_name,
        }
    
    def get_sqlite_config(self) -> dict[str, Any]:
        """Return SQLite configuration."""
        return {
            "db_path": self._sqlite_db_path,
        }


# Singleton instance
vector_store_config = VectorStoreConfig()
