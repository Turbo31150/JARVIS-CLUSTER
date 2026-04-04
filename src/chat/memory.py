"""Chat memory system with conversation history."""

import json
from typing import Any, Optional
from datetime import datetime

DEFAULT_MEMORY_FILE = "/home/turbo/Workspaces/JARVIS-CLUSTER/data/chat_memory.json"


class ChatMemory:
    """Persistent chat memory with context awareness."""
    
    def __init__(self, file_path: str = DEFAULT_MEMORY_FILE):
        self._file_path = file_path
        self._memory: list[dict] = []
        
        # Initialize from existing file if available
        try:
            with open(file_path, "r") as f:
                self._memory = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self._memory = []
    
    def add_message(
        self,
        role: str,
        content: str,
        metadata: Optional[dict] = None,
    ) -> None:
        """Add a message to memory."""
        entry = {
            "id": len(self._memory) + 1,
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {},
        }
        
        self._memory.append(entry)
        
        # Save to file
        self._save()
    
    def get_conversation(self, num_context: int = 10) -> list[dict]:
        """Get recent conversation history."""
        return self._memory[-num_context:]
    
    def get_context_aware_response(
        self,
        query: str,
        system_prompt: Optional[str] = None,
    ) -> str:
        """Get response with context awareness from memory."""
        if not self._memory:
            return f"Response to: {query}"
        
        recent_history = self.get_conversation(num_context=5)
        
        # Build context string
        context_lines = [f"{e['role']}: {e['content'][:200]}" for e in recent_history]
        context_string = "\n".join(context_lines)
        
        response = f"Context-aware response to: {query}"
        
        return response
    
    def search_memory(self, query: str, max_results: int = 3) -> list[dict]:
        """Search memory for relevant entries."""
        lower_query = query.lower()
        
        relevant = [
            entry for entry in self._memory
            if any(
                term in entry["content"].lower()
                for term in lower_query.split()
            )
        ][:max_results]
        
        return relevant
    
    def clear(self) -> None:
        """Clear all memory."""
        self._memory = []
        self._save()
    
    def _save(self) -> None:
        """Save memory to file."""
        with open(self._file_path, "w") as f:
            json.dump(self._memory, f, indent=2, default=str)


# Singleton instance
_default_memory = ChatMemory()


def get_chat_memory() -> ChatMemory:
    """Get the default chat memory instance."""
    return _default_memory


def add_to_memory(role: str, content: str) -> None:
    """Convenience function to add message to memory."""
    _default_memory.add_message(role, content)
