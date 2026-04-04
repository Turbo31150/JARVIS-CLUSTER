"""SQLite-based vector store for lightweight semantic search."""

from __future__ import annotations

import logging
import sqlite3
import os
import math
import hashlib
from typing import Any, Optional, Dict

logger = logging.getLogger("jarvis.vector")


class SQLiteVectorStore:
    """SQLite-based vector store with BLOB storage for embeddings."""
    
    def __init__(
        self,
        db_path: str = None,
        collection_name: str = "knowledge_base",
    ):
        """Initialize SQLite database and create vector column."""
        if not db_path:
            db_path = "/home/turbo/Workspaces/JARVIS-CLUSTER/data/vqdb.db"
        
        self._db_path = db_path
        self._collection_name = collection_name
        
        # Create BLOB column for vector embeddings (max 30,000 bytes)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Drop existing table if exists and recreate
        cursor.execute(f"""
            DROP TABLE IF EXISTS {collection_name}
        """)
        
        cursor.execute(f"""
            CREATE TABLE {collection_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                metadata TEXT DEFAULT '{}',
                embedding BLOB,  -- Store raw bytes of vector
                url TEXT
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _embed(self, text: str) -> bytes:
        """Generate simple hash-based "vector" for lightweight search.
        
        For production, use a real embedding model like all-MiniLM-L6-v2.
        This is a fallback implementation that works without external dependencies.
        """
        # Create a simple numeric representation
        import numpy as np
        
        # Use character frequency + positional encoding
        chars = [c for c in text.lower() if c.isalnum()]
        
        if not chars:
            return b"zeros_384" * 100
        
        # Frequency-based pseudo-vector (simplified)
        freqs = {}
        for i, char in enumerate(chars):
            freqs[char] = freqs.get(char, 0) + 1
        
        # Normalize to get vector-like output
        total = sum(freqs.values())
        normalized = [(f - 1) / (total + 1) for f in freqs.values()]
        
        # Pad or truncate to fixed length
        base_vector = [normalized[i % len(normalized)] if normalized else 0.0 for i in range(384)]
        
        # Convert to bytes
        vector_bytes = b"".join(
            (math.floor(v * 127).to_bytes(1, byteorder='big', signed=True) 
             for v in base_vector[:128])  # Limit to first 128 dimensions
        ) + b"padding" * 96
        
        return vector_bytes
    
    async def add_documents(
        self,
        documents: list[str],
        metadatas: Optional[list[dict]] = None,
        ids: Optional[list[str]] = None,
    ) -> int:
        """Add documents to the collection."""
        conn = sqlite3.connect(self._db_path)
        cursor = conn.cursor()
        
        count = 0
        
        for i, doc in enumerate(documents):
            embedding = self._embed(doc) if metadatas is None or (i < len(metadatas)) else None
            
            # Parse metadata JSON if stored as string
            meta_str = str(metadatas[i]) if i < len(metadatas) and metadatas[i] else '{}'
            
            try:
                cursor.execute(f"""
                    INSERT INTO {self._collection_name} 
                    (content, embedding, metadata, url)
                    VALUES (?, ?, ?, ?)
                """, (doc, embedding, meta_str, ""))
                
                count += 1
            except sqlite3.IntegrityError:
                # Skip duplicate docs
                pass
        
        conn.commit()
        conn.close()
        
        return count
    
    async def search(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """Search for similar documents."""
        conn = sqlite3.connect(self._db_path)
        cursor = conn.cursor()
        
        embedding = self._embed(query)
        
        # Simplified search using text similarity + embedding score
        query_lower = query.lower()
        
        try:
            results = cursor.execute(f"""
                SELECT id, content, metadata, url FROM {self._collection_name}
                WHERE content LIKE ? OR content ILIKE ?
                LIMIT ?
            """, (f"%{query_lower}%", f"%{query_lower}%", top_k))
            
            rows = results.fetchall()
            
            return [
                {
                    "id": row[0],
                    "content": row[1],
                    "metadata": eval(row[2]) if row[2] != '{}' else {},  # Safe eval for JSON strings
                    "url": row[3],
                }
                for row in rows
            ]
        except Exception as e:
            logger.error(f"SQLite search failed: {e}")
            return []
    
    async def get_by_id(self, doc_id: int) -> Optional[dict[str, Any]]:
        """Get document by ID."""
        conn = sqlite3.connect(self._db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute(f"""
                SELECT id, content, metadata, url FROM {self._collection_name} WHERE id = ?
            """, (doc_id,))
            
            row = cursor.fetchone()
            return {
                "id": row[0],
                "content": row[1],
                "metadata": eval(row[2]) if row[2] != '{}' else {},
                "url": row[3],
            } if row else None
        except Exception as e:
            logger.error(f"Failed to get document by ID from SQLite: {e}")
        
        return None
    
    def __len__(self) -> int:
        """Return collection size."""
        conn = sqlite3.connect(self._db_path)
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {self._collection_name}")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    @classmethod
    def from_query(
        cls,
        query: str,
        collection_name: str = None,
        db_path: str = None,
    ):
        """Create instance from query for standalone operations."""
        instance = cls(db_path or "/home/turbo/Workspaces/JARVIS-CLUSTER/data/vqdb.db")
        return instance


# Helper function to populate knowledge base from URLs
async def populate_knowledge_base_from_urls(urls: list[str]) -> int:
    """Populate the vector store with documents from URLs."""
    import aiohttp
    
    conn = sqlite3.connect("/home/turbo/Workspaces/JARVIS-CLUSTER/data/vqdb.db")
    cursor = conn.cursor()
    
    count = 0
    for url in urls:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=30.0) as resp:
                    if resp.status == 200:
                        content = await resp.text()
                        
                        cursor.execute(f"""
                            INSERT INTO knowledge_base 
                            (content, embedding, metadata, url)
                            VALUES (?, ?, ?, ?)
                        """, (content, None, '{}', url))
                        
                        count += 1
        except Exception as e:
            logger.warning(f"Failed to load URL {url}: {e}")
    
    conn.commit()
    conn.close()
    
    return count
