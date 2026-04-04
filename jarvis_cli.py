#!/usr/bin/env python3
"""JARVIS CLUSTER - Command Line Interface for the full system."""

from __future__ import annotations

import argparse
import asyncio
import sys
from typing import Any

try:
    from src.network.requests import fetch, post, get_json
    from src.network.search import search_engine
    from src.network.knowledge import knowledge_base, tool_executor
    from src.vector_store.factory import create_vector_store
    from src.vector_store.config import VectorStoreConfig
    HAS_NETWORK = True
except ImportError as e:
    HAS_NETWORK = False
    print(f"[!] Network features unavailable: {e}")

# Import chat interface if available
try:
    from src.chat.interface import ChatInterface
    HAS_CHAT = True
except ImportError:
    HAS_CHAT = False


async def run_interactive_demo():
    """Run interactive demo with network + tools."""
    print("=" * 60)
    print(" 🚀 JARVIS CLUSTER - Interactive Mode")
    print("=" * 60)
    print()
    
    while True:
        try:
            user_input = input("\nJARVIS> ").strip()
            
            if not user_input:
                continue
            
            # Handle exit commands
            if user_input.lower() in ["quit", "exit", "q"]:
                print("👋 Goodbye! JARVIS will wait for your next command.")
                break
            
            if user_input.lower() == "help":
                print("""
Available Commands:
  help          - Show this help message
  search <query>   - Search web with DuckDuckGo or Wikipedia
  web_search <query>     - Perform web search across multiple sources
  tools         - List available external tools
  calculator <expr>    - Evaluate math expression
  weather <location>    - Get current weather (requires API key)
  stocks <symbol>       - Get stock data (requires Finnhub API key)
  github <repo>         - Search GitHub repositories
  knowledge     - Show configured knowledge sources
  status        - Show system status
  exit          - Exit the interactive mode
""")
                continue
            
            # Route commands
            if user_input.lower().startswith("search "):
                query = user_input[7:]
                print(f"\n🔍 Searching web: {query}\n")
                results = await search_engine.duckduckgo_search(query)
                if results:
                    for i, result in enumerate(results[:3], 1):
                        print(f"{i}. {result['title']}")
                        print(f"   URL: {result.get('url', 'N/A')}")
                        print(f"   Snippet: {result.get('snippet', 'N/A')}\n")
                else:
                    print("❌ No results found\n")
            
            elif user_input.lower().startswith("web_search "):
                query = user_input[11:]
                print(f"\n🔍 Web search (multiple sources):\n")
                
                # Try multiple search engines
                ddg_results = await search_engine.duckduckgo_search(query)
                wiki_results = await search_engine.wiki_search(query)
                
                all_results = []
                if ddg_results:
                    all_results.extend(ddg_results[:3])
                if wiki_results:
                    all_results.extend(wiki_results[:2])
                
                all_results = list(dict.fromkeys(all_results))  # Remove duplicates
                
                if all_results:
                    for i, result in enumerate(all_results[:5], 1):
                        source = "DDG" if "duckduckgo" in str(result.get("source", "")) else ("Wikipedia" if "wiki" in str(result) else "?")
                        print(f"{i}. [{source}] {result.get('title', 'N/A')}")
                else:
                    print("❌ No results found across sources\n")
            
            elif user_input.lower().startswith("tools"):
                sources = knowledge_base.get_available_sources()
                print(f"\nAvailable tools:\n")
                
                for source in sources:
                    config = knowledge_base._kb_sources[source]
                    if "enabled" in config and config["enabled"]:
                        print(f"  ✓ {source}")
                    else:
                        print(f"  ⚠ {source} (disabled)")
                
                print()
            
            elif user_input.lower().startswith("calculator"):
                expr = user_input[10:].strip()
                result = await tool_executor.calculator(expr)
                if result["success"]:
                    print(f"\n{expr} = {result['result']}\n")
                else:
                    print(f"\nError: {result.get('error', 'Unknown error')}\n")
            
            elif user_input.lower().startswith("weather"):
                location = user_input[7:].strip()
                result = await tool_executor.weather(location)
                if result["success"]:
                    temp_c = result.get("temperature_celsius", "N/A")
                    print(f"\n🌤️ Weather in {location}:\n   Temperature: {temp_c}°C\n")
                else:
                    print(f"\nError: {result.get('error', 'Unknown error')}\n")
            
            elif user_input.lower().startswith("stocks"):
                symbol = user_input[6:].strip()
                result = await tool_executor.stocks(symbol)
                if result["success"]:
                    price = result.get("price", "N/A")
                    print(f"\n📈 {symbol}:\n   Price: ${price}\n")
                else:
                    print(f"\nError: {result.get('error', 'Unknown error')}\n")
            
            elif user_input.lower().startswith("github"):
                repo = user_input[6:].strip()
                result = await tool_executor.github(repo)
                if result["success"] and result.get("repositories"):
                    for repo_info in result["repositories"][:3]:
                        print(f"  {repo_info['name']} by {repo_info['owner']} ({repo_info['full_name']})")
                        print(f"   Stars: {repo_info.get('stargazers_count', 'N/A')}\n")
                else:
                    print(f"\nError: {result.get('error', 'Unknown error')}\n")
            
            elif user_input.lower() == "knowledge":
                sources = knowledge_base.get_available_sources()
                print(f"\n🧠 Knowledge Sources:\n")
                
                for source in sources:
                    if source == "wikipedia":
                        print(f"  ✓ Wikipedia API (5 results per query)")
                    elif source == "duckduckgo":
                        print(f"  ✓ DuckDuckGo (10 results per query)")
                    elif source == "google":
                        print(f"  ✓ Google Custom Search (requires API key)")
                
                print()
            
            elif user_input.lower() == "status":
                print(f"\n🔧 System Status:\n")
                print(f"  Network: {'✅ Enabled' if HAS_NETWORK else '❌ Disabled'}")
                print(f"  Chat: {'✅ Enabled' if HAS_CHAT else '❌ Disabled'}")
                print(f"  Tools: {knowledge_base.get_available_sources()}")
                print()
            
            elif user_input.lower() == "exit":
                break
            
            else:
                print(f"\nUnknown command. Type 'help' for available commands.\n")
        
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye! JARVIS will wait for your next command.")
            break
        except Exception as e:
            print(f"\nError: {e}\n")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="JARVIS CLUSTER - Full system with network access + external tools"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Interactive mode
    interactive_parser = subparsers.add_parser("interactive", help="Run interactive demo")
    interactive_parser.set_defaults(func=run_interactive_demo)
    
    # Test network
    test_parser = subparsers.add_parser("test-network", help="Test network connectivity")
    test_parser.add_argument("--url", type=str, default="https://httpbin.org/status/200")
    test_parser.add_argument("--query", type=str, default="")
    test_parser.set_defaults(func=test_network)
    
    # List tools
    list_tools = subparsers.add_parser("list-tools", help="List available external tools")
    list_tools.set_defaults(func=list_available_tools)
    
    args = parser.parse_args()
    
    if args.command is None:
        run_interactive_demo()
    else:
        asyncio.run(args.func())


async def test_network(url: str, query: str):
    """Test network connectivity."""
    print(f"\nTesting network to {url}...")
    
    try:
        if query:
            result = await fetch(url, timeout=10.0)
            print(f"✅ Network works! Received {len(result)} bytes")
            
            if query and "search" in url.lower():
                # Try search engine
                results = await search_engine.duckduckgo_search(query)
                print(f"✅ Search working: Found {len(results or [])} results for '{query}'")
        else:
            result = await fetch(url, timeout=10.0)
            print(f"✅ Network works! Received {len(result)} bytes from test endpoint")
        
    except Exception as e:
        print(f"❌ Network error: {e}")


async def list_available_tools():
    """List all available external tools."""
    sources = knowledge_base.get_available_sources()
    
    print("\nAvailable External Tools:")
    print("=" * 40)
    
    for source in sources:
        config = knowledge_base._kb_sources[source]
        if "enabled" in config and config["enabled"]:
            tool_name = "duckduckgo" if source == "duckduckgo" else ("wikipedia" if source == "wikipedia" else source)
            print(f"  ✓ {tool_name}")
            if source == "duckduckgo":
                print(f"     - Search the web with DuckDuckGo (privacy-friendly)")
            elif source == "wikipedia":
                print(f"     - Get information from Wikipedia")
        else:
            print(f"  ⚠ {source} (disabled or API key required)")
    
    print()


if __name__ == "__main__":
    main()
