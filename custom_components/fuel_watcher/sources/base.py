from __future__ import annotations
import aiohttp
import async_timeout
import logging

_LOGGER = logging.getLogger(__name__)


async def fetch_json(session: aiohttp.ClientSession, url: str, timeout: int = 10):
    """Fetch JSON from a URL with timeout and error handling."""
    try:
        with async_timeout.timeout(timeout):
            async with session.get(url) as resp:
                if resp.status != 200:
                    _LOGGER.error("HTTP %s for URL %s", resp.status, url)
                    return None
                return await resp.json()
    except Exception as e:
        _LOGGER.error("Error fetching URL %s: %s", url, e)
        return None
