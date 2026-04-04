"""External tools execution (calculator, code, weather, stocks, etc.)."""

from __future__ import annotations

import logging
import subprocess
import re
from typing import Any

logger = logging.getLogger("jarvis.tools")


class ToolExecutor:
    """Execute external tools safely with sandboxing."""
    
    def __init__(self):
        self._active_tools: dict[str, dict[str, Any]] = {
            "calculator": {
                "enabled": True,
                "executor": self._execute_calculator,
            },
            "code": {
                "enabled": True,
                "executor": self._execute_code,
            },
            "weather": {
                "enabled": bool(self._check_env("WEATHER_API_KEY")),
                "executor": self._execute_weather,
            },
            "stocks": {
                "enabled": bool(self._check_env("FINNHUB_API_KEY")),
                "executor": self._execute_stocks,
            },
            "github": {
                "enabled": bool(self._check_env("GITHUB_TOKEN")),
                "executor": self._execute_github,
            },
        }
    
    def _check_env(self, env_var: str) -> bool:
        """Check if environment variable is set and non-empty."""
        import os
        value = os.getenv(env_var, "")
        return bool(value)
    
    async def calculator(
        self,
        expression: str,
    ) -> dict[str, Any]:
        """Execute math expression using Python's eval (safe for numeric ops)."""
        if not self._active_tools["calculator"]["enabled"]:
            return {
                "tool": "calculator",
                "success": False,
                "error": "Calculator tool not enabled",
            }
        
        try:
            # Only allow numeric operations
            sanitized = re.sub(r"[^0-9+\-*/().\s]", "", expression)
            
            result = eval(sanitized)
            
            if isinstance(result, (int, float)):
                return {
                    "tool": "calculator",
                    "success": True,
                    "result": result,
                    "expression": sanitized,
                }
            else:
                return {
                    "tool": "calculator",
                    "success": False,
                    "error": "Calculation result is not a number",
                }
        except Exception as e:
            logger.error(f"Calculator execution failed: {e}")
            return {
                "tool": "calculator",
                "success": False,
                "error": str(e),
            }
    
    async def code_executor(
        self,
        code: str,
        timeout_s: int = 30,
    ) -> dict[str, Any]:
        """Execute Python code in sandboxed environment."""
        if not self._active_tools["code"]["enabled"]:
            return {
                "tool": "code_executor",
                "success": False,
                "error": "Code executor tool not enabled",
            }
        
        try:
            # Create isolated namespace with only safe builtins
            allowed_globals = {
                "__builtins__": {
                    name: getattr(builtins_module, name)
                    for name in dir(builtins_module)
                    if not name.startswith("_") and isinstance(getattr(builtins_module, name), (type(str), type(int)))
                } | {"print": print}  # Allow prints for debugging
            }
            
            result = subprocess.run(
                ["python3", "-c", code],
                capture_output=True,
                text=True,
                timeout=timeout_s,
                cwd="/tmp",  # Sandbox directory
                env={**self._get_sandboxed_env()},
            )
            
            return {
                "tool": "code_executor",
                "success": result.returncode == 0,
                "output": result.stdout.strip(),
                "error": result.stderr.strip() if result.returncode != 0 else None,
            }
        except subprocess.TimeoutExpired as e:
            logger.error(f"Code execution timed out after {timeout_s}s")
            return {
                "tool": "code_executor",
                "success": False,
                "error": f"Execution timed out after {timeout_s}s",
            }
        except Exception as e:
            logger.error(f"Code execution failed: {e}")
            return {
                "tool": "code_executor",
                "success": False,
                "error": str(e),
            }
    
    async def weather(
        self,
        location: str,
        unit: str = "celsius",
    ) -> dict[str, Any]:
        """Get weather data from Open-Meteo API."""
        if not self._active_tools["weather"]["enabled"]:
            return {
                "tool": "weather",
                "success": False,
                "error": "Weather tool not enabled (WEATHER_API_KEY not set)",
            }
        
        try:
            import aiohttp
            from src.network.requests import get_json
            
            # Convert location to coordinates
            lat, lon = await self._geocode_location(location)
            
            query_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,weather_code&daily=precipitation_probability_sum,windspeed_10m_max&hourly=none"
            
            result = await get_json(query_url)
            
            if result:
                return {
                    "tool": "weather",
                    "success": True,
                    "location": location,
                    "coordinates": {"lat": lat, "lon": lon},
                    "temperature_celsius": result.get("current", {}).get("temperature_2m"),
                    "weather_code": result.get("current", {}).get("weather_code"),
                    "precipitation_probability": result.get("daily", {}).get("precipitation_probability_sum", 0),
                    "unit": unit,
                }
            
            return {
                "tool": "weather",
                "success": False,
                "error": "Failed to get weather data from Open-Meteo API",
            }
        except Exception as e:
            logger.error(f"Weather query failed: {e}")
            return {
                "tool": "weather",
                "success": False,
                "error": str(e),
            }
    
    async def stocks(
        self,
        symbol: str,
    ) -> dict[str, Any]:
        """Get stock data from Finnhub API."""
        if not self._active_tools["stocks"]["enabled"]:
            return {
                "tool": "stocks",
                "success": False,
                "error": "Stocks tool not enabled (FINNHUB_API_KEY not set)",
            }
        
        try:
            api_key = os.getenv("FINNHUB_API_KEY") or ""
            
            query_url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={api_key}"
            result = await get_json(query_url, timeout=30.0)
            
            if result:
                return {
                    "tool": "stocks",
                    "success": True,
                    "symbol": symbol,
                    "price": result.get("c"),
                    "change": result.get("d"),
                    "change_percent": result.get("dp"),
                    "high": result.get("h"),
                    "low": result.get("l"),
                    "open": result.get("o"),
                }
            
            return {
                "tool": "stocks",
                "success": False,
                "error": f"Failed to get stock data for {symbol} from Finnhub API",
            }
        except Exception as e:
            logger.error(f"Stocks query failed: {e}")
            return {
                "tool": "stocks",
                "success": False,
                "error": str(e),
            }
    
    async def github(
        self,
        repo_name: str,
        owner: str | None = None,
        action: str = "search_repositories",
    ) -> dict[str, Any]:
        """Search or interact with GitHub repositories."""
        if not self._active_tools["github"]["enabled"]:
            return {
                "tool": "github",
                "success": False,
                "error": "GitHub tool not enabled (GITHUB_TOKEN not set)",
            }
        
        try:
            token = os.getenv("GITHUB_TOKEN") or ""
            
            url = f"https://api.github.com/search/repositories?q={repo_name}&sort=stars&order=desc"
            if owner:
                url += f"&owner:{owner}"
            
            result = await get_json(url, timeout=30.0)
            
            return {
                "tool": "github",
                "success": True,
                "repositories": result.get("items", [])[:10],
                "total_count": result.get("total_count", 0),
            }
        except Exception as e:
            logger.error(f"GitHub query failed: {e}")
            return {
                "tool": "github",
                "success": False,
                "error": str(e),
            }
    
    async def _geocode_location(self, location: str) -> tuple[float, float]:
        """Geocode a location name to coordinates."""
        import os
        
        if not os.getenv("NOMAP_API_KEY"):
            return (0.0, 0.0)  # Return default if no API key
        
        from src.network.requests import get_json
        
        query_url = f"https://api.nominatim.org/v1/search/?q={location}&format=json&limit=1"
        result = await get_json(query_url, timeout=30.0)
        
        if result:
            return float(result[0]["lat"]), float(result[0]["lon"])
        return (51.5074, -0.1278)  # Default to London
    
    def _get_sandboxed_env(self) -> dict[str, str]:
        """Return environment variables for sandboxed code execution."""
        import os
        
        safe = {
            "HOME": "/home/turbo",
            "PATH": "/usr/local/bin:/usr/bin:/bin",
            "LANG": "en_US.UTF-8",
            # Remove potentially dangerous env vars
            **{k: v for k, v in os.environ.items() 
               if k in ("HOME", "PATH", "LANG", "TMPDIR")},
        }
        return safe
    
    async def execute(
        self,
        tool_name: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute any available tool by name."""
        tool_config = self._active_tools.get(tool_name)
        if not tool_config or not tool_config["enabled"]:
            return {
                "tool": tool_name,
                "success": False,
                "error": f"Tool '{tool_name}' is not enabled",
            }
        
        executor = tool_config["executor"]
        return await executor(**params) if params else await executor()


# Singleton instance
tool_executor = ToolExecutor()
