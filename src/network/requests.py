"""External API calls with retry logic + timeout handling."""

from __future__ import annotations

import aiohttp
import asyncio
import logging
import time
from typing import Any

logger = logging.getLogger("jarvis.network")


class RequestError(Exception):
    """Custom exception for network errors."""
    pass


async def fetch(
    url: str,
    timeout: float = 30.0,
    max_retries: int = 3,
) -> str | None:
    """Fetch URL with retry logic + exponential backoff."""
    async with aiohttp.ClientSession() as session:
        for attempt in range(max_retries):
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as resp:
                    if resp.status == 200:
                        return await resp.text()
                    elif resp.status >= 500:
                        await asyncio.sleep(min(2 ** attempt, 30))
                        continue
                    raise RequestError(f"HTTP {resp.status}")
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                if attempt == max_retries - 1:
                    logger.error(f"Final fetch failed for {url}: {e}")
                    return None
                delay = min(2 ** attempt, 30)
                logger.warning(f"Fetch to {url} failed (attempt {attempt + 1}/{max_retries}): {e}. Retrying in {delay}s...")
                await asyncio.sleep(delay)
    
    return None


async def post(
    url: str,
    json_data: dict | None = None,
    timeout: float = 30.0,
    max_retries: int = 3,
) -> Any | None:
    """POST to URL with retry logic + exponential backoff."""
    async with aiohttp.ClientSession() as session:
        for attempt in range(max_retries):
            try:
                async with session.post(url, json=json_data or {}, timeout=aiohttp.ClientTimeout(total=timeout)) as resp:
                    if resp.status == 200 or resp.status == 201:
                        return await resp.json()
                    elif resp.status >= 500:
                        await asyncio.sleep(min(2 ** attempt, 30))
                        continue
                    raise RequestError(f"HTTP {resp.status}: {await resp.text()}")
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                if attempt == max_retries - 1:
                    logger.error(f"Final POST failed for {url}: {e}")
                    return None
                delay = min(2 ** attempt, 30)
                logger.warning(f"POST to {url} failed (attempt {attempt + 1}/{max_retries}): {e}. Retrying in {delay}s...")
                await asyncio.sleep(delay)
    
    return None


async def get_json(
    url: str,
    timeout: float = 30.0,
    max_retries: int = 3,
) -> Any | None:
    """GET JSON from URL with retry logic + exponential backoff."""
    async with aiohttp.ClientSession() as session:
        for attempt in range(max_retries):
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as resp:
                    if resp.status == 200 or resp.status == 201:
                        return await resp.json()
                    elif resp.status >= 500:
                        await asyncio.sleep(min(2 ** attempt, 30))
                        continue
                    raise RequestError(f"HTTP {resp.status}: {await resp.text()}")
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                if attempt == max_retries - 1:
                    logger.error(f"Final GET failed for {url}: {e}")
                    return None
                delay = min(2 ** attempt, 30)
                logger.warning(f"GET from {url} failed (attempt {attempt + 1}/{max_retries}): {e}. Retrying in {delay}s...")
                await asyncio.sleep(delay)
    
    return None


async def stream(
    url: str,
    event_handler,
    timeout: float = 30.0,
) -> Any | None:
    """Stream SSE events from URL."""
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as resp:
                if resp.status != 200:
                    raise RequestError(f"HTTP {resp.status}")
                
                async for line in resp.content.iter_text():
                    if not line.strip():
                        continue
                    
                    event = line.split(":", 1)
                    if len(event) == 2:
                        event_type, data = event
                        event_handler({"type": event_type.strip(), "data": data.strip()})
        
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.error(f"Stream failed for {url}: {e}")
    
    return None


async def with_retry(
    coro_func,
    max_retries: int = 3,
    retry_on_exception=(asyncio.TimeoutError, aiohttp.ClientError),
    timeout: float = 30.0,
) -> Any:
    """Generic retry decorator for async functions."""
    async def wrapper(*args, **kwargs):
        for attempt in range(max_retries):
            try:
                return await coro_func(*args, **kwargs)
            except retry_on_exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"Final call to {coro_func.__name__} failed: {e}")
                    raise RequestError(str(e))
                
                delay = min(2 ** attempt, 30)
                logger.warning(
                    f"Call to {coro_func.__name__} failed (attempt {attempt + 1}/{max_retries}): {e}. "
                    f"Retrying in {delay}s..."
                )
                await asyncio.sleep(delay)
        
        return None
    
    return wrapper
