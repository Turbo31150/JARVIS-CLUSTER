"""ChromaDB vector store implementation for semantic search."""

from __future__ import annotations

import logging
import chromadb
from typing import Any

logger = logging.getLogger("jarvis.vector")


class ChromaVectorStore:
    """ChromaDB-based vector store with similarity search + metadata filtering."""
    
    def __init__(
        self,
        collection_name: str = "knowledge_base",
        embedding_function=None,
        persistent_path: str = None,
    ):
        """Initialize ChromaDB collection."""
        if not embedding_function:
            import torch
            from sentence_transformers import SentenceTransformer
        
        # Default to CPU embeddings if no GPU available
            model_name = "all-MiniLM-L6-v2"  # Lightweight, fast embeddings
            self._embedding_model = SentenceTransformer(model_name)
            self._embedding_function = lambda text: self._embedding_model.encode(
                [text], convert_to_numpy=True, normalize_L2=True
            )[0].tolist()
        else:
            self._embedding_function = embedding_function
        
        if persistent_path:
            client = chromadb.PersistentClient(path=persistent_path)
        else:
            client = chromadb.EphemeralClient()
        
        collection_exists = client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
            embedding_function=self._embedding_function if hasattr(self, '_embedding_function') else None,
        )
        
        self._client = client
        self._collection = collection_exists
    
    async def add_documents(
        self,
        ids: list[str],
        documents: list[str],
        metadatas: list[dict] | None = None,
    ) -> bool:
        """Add documents to collection."""
        embeddings = [self._embedding_function(doc) for doc in documents]
        
        try:
            self._collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas or [],
                embeddings=embeddings,
            )
            return True
        except Exception as e:
            logger.error(f"Failed to add documents to ChromaDB: {e}")
            return False
    
    async def search(
        self,
        query: str,
        top_k: int = 5,
        filter: dict | None = None,
    ) -> list[dict[str, Any]]:
        """Perform semantic similarity search."""
        query_embedding = self._embedding_function(query)
        
        try:
            results = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=filter,
            )
            
            if not results or not results.get("documents"):
                return []
            
            documents = results["documents"][0]
            metadatas = results.get("metadatas", [{} for _ in range(len(documents))])
            distances = results.get("distances", [1.0 for _ in range(len(documents))])
            
            # Zip and return as list of dicts
            return [
                {
                    "content": doc,
                    "metadata": meta,
                    "distance": float(dist),
                }
                for doc, meta, dist in zip(
                    documents or [],
                    metadatas or [],
                    distances or [],
                )
            ]
        except Exception as e:
            logger.error(f"Failed to search ChromaDB: {e}")
            return []
    
    async def get_by_id(self, doc_id: str) -> dict[str, Any] | None:
        """Get document by ID."""
        try:
            docs = self._collection.get(ids=[doc_id])
            if docs and "documents" in docs:
                return {
                    "content": docs["documents"][0],
                    "metadata": docs.get("metadatas", [{}])[0] if docs.get("metadatas") else {},
                    "id": doc_id,
                }
        except Exception as e:
            logger.error(f"Failed to get document by ID from ChromaDB: {e}")
        return None
    
    def get_collection(self) -> Any:
        """Return the underlying ChromaDB collection for advanced operations."""
        return self._collection
    
    async def delete_by_id(self, doc_id: str) -> bool:
        """Delete document by ID."""
        try:
            self._collection.delete(ids=[doc_id])
            return True
        except Exception as e:
            logger.error(f"Failed to delete document from ChromaDB: {e}")
            return False


# Singleton for testing
chroma_store = ChromaVectorStore()
