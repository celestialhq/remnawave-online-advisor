from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp

from app.config import Settings

logger = logging.getLogger(__name__)


class ApiClientError(RuntimeError):
    """Raised when the nodes API cannot be read successfully."""


class NodesApiClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._timeout = aiohttp.ClientTimeout(total=settings.API_TIMEOUT_SECONDS)

    async def fetch_nodes(self) -> list[dict[str, Any]]:
        url = f"{self._settings.API_BASE_URL}/api/nodes"
        headers = {"Authorization": self._settings.authorization_header}
        last_error: Exception | None = None

        for attempt in range(1, self._settings.API_RETRIES + 1):
            try:
                async with aiohttp.ClientSession(timeout=self._timeout, headers=headers) as session:
                    async with session.get(url) as response:
                        if response.status in {429, 500, 502, 503, 504}:
                            body = await response.text()
                            raise ApiClientError(f"Temporary API error {response.status}: {body[:300]}")
                        if response.status >= 400:
                            body = await response.text()
                            raise ApiClientError(f"API error {response.status}: {body[:300]}")

                        payload = await response.json(content_type=None)
                        nodes = payload.get("response")
                        if not isinstance(nodes, list):
                            raise ApiClientError("Invalid API response: field 'response' must be a list")
                        return [node for node in nodes if isinstance(node, dict)]

            except (aiohttp.ClientError, asyncio.TimeoutError, ApiClientError) as error:
                last_error = error
                is_last_attempt = attempt >= self._settings.API_RETRIES
                logger.warning("Nodes API request failed on attempt %s/%s: %s", attempt, self._settings.API_RETRIES, error)
                if is_last_attempt or not self._is_retryable(error):
                    break
                await asyncio.sleep(self._settings.API_RETRY_DELAY_SECONDS * attempt)

        raise ApiClientError(f"Nodes API request failed after retries: {last_error}") from last_error

    @staticmethod
    def _is_retryable(error: Exception) -> bool:
        message = str(error)
        if isinstance(error, ApiClientError):
            return "Temporary API error" in message
        return True
