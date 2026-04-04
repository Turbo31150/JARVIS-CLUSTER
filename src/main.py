"""Main entry point for JARVIS CLUSTER."""

from __future__ import annotations

import asyncio
import sys
from typing import Optional


async def main() -> None:
    """Run the main JARVIS system loop."""
    print("=" * 60)
    print(" 🤖 JARVIS CLUSTER - AI Assistant System")
    print("=" * 60)
    print()
    
    # Try to import optional modules gracefully
    try:
        from src.network.requests import fetch, post
        from src.network.search import search_engine
        from src.knowledge_base.retriever import knowledge_retriever
        from src.tools.calculator import Calculator
        from src.tools.code_executor import CodeExecutor
        print("✅ Network layer loaded")
    except ImportError as e:
        print(f"⚠️  Optional network features unavailable: {e}")
    
    try:
        from src.vector_store.chroma import ChromaVectorStore
        from src.vector_store.factory import create_vector_store
        print("✅ Vector store loaded")
    except ImportError as e:
        print(f"⚠️  Optional vector store features unavailable: {e}")
    
    try:
        from src.agent.planner import AgentPlanner
        planner = AgentPlanner()
        print("✅ Agent planner loaded")
    except ImportError as e:
        print(f"⚠️  Optional agent features unavailable: {e}")
    
    # Initialize core components
    search_engine: Optional[object] = None
    retriever: Optional[object] = None
    calculator: Optional[Calculator] = None
    executor: Optional[CodeExecutor] = None
    
    if "SearchEngine" in globals():
        search_engine = SearchEngine()
    
    if "knowledge_retriever" in globals():
        retriever = knowledge_retriever
    
    calc = Calculator()
    
    # Initialize vector store (SQLite by default)
    try:
        from src.vector_store.sqlite import SQLiteVectorStore
        vector_store = SQLiteVectorStore(
            db_path="/home/turbo/Workspaces/JARVIS-CLUSTER/data/vqdb.db",
            collection_name="knowledge_base"
        )
        print("✅ Vector store initialized (SQLite)")
    except Exception as e:
        print(f"⚠️  Could not initialize vector store: {e}")
    
    while True:
        try:
            user_input = input("\nJARVIS> ").strip()
            
            if not user_input:
                continue
            
            # Handle exit commands
            if user_input.lower() in ["quit", "exit", "q"]:
                print("👋 Goodbye!")
                break
            
            # Route to appropriate component
            if user_input.lower().startswith("search"):
                query = user_input[7:].strip()
                if search_engine:
                    results = await search_engine.duckduckgo_search(query)
                    if results:
                        for r in results[:3]:
                            print(f"🔗 {r.get('title', '')}")
                            print(f"   URL: {r.get('url', 'N/A')}")
                            print(f"   Snippet: {r.get('snippet', '')}\n")
                else:
                    print("Network search not available. Install dependencies.\n")
            
            elif user_input.lower().startswith("calculator"):
                expr = user_input[10:].strip()
                result = await calc.evaluate(expr)
                if result["success"]:
                    print(f"✅ {expr} = {result['result']}\n")
                else:
                    print(f"❌ Error: {result.get('error', 'Unknown error')}\n")
            
            elif user_input.lower() == "status":
                print("\n🔧 System Status:\n")
                from src.tools.calculator import Calculator
                test = Calculator()
                print(f"  Calculator: {'✅ Working' if calc else '❌ Not available'}")
                print(f"  Network: {'✅ Available' if search_engine else '⚠️  Optional'}")
                
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}\n")


def entry_point() -> None:
    """Entry point for Python interpreter."""
    asyncio.run(main())


if __name__ == "__main__":
    entry_point()
