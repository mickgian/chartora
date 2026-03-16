"""Sentiment analysis adapter using the Claude API.

Implements the SentimentAnalyzer interface for scoring news articles.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from src.domain.interfaces.data_sources import SentimentAnalyzer

logger = logging.getLogger(__name__)

CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"
CLAUDE_MODEL = "claude-haiku-4-5-20251001"

SENTIMENT_PROMPT = (
    "Analyze the sentiment of the following text about"
    " a quantum computing company from an investor's"
    " perspective.\n\n"
    'Classify the sentiment as exactly one of: "bullish",'
    ' "bearish", or "neutral".\n'
    "Also provide a confidence score between 0.0 and 1.0."
    "\n\n"
    "Respond with ONLY a JSON object in this exact format:"
    "\n"
    '{{"sentiment": "<bullish|bearish|neutral>",'
    ' "confidence": <0.0-1.0>}}'
    "\n\nText to analyze:\n{text}"
)


class ClaudeSentimentAnalyzer(SentimentAnalyzer):
    """Analyzes news sentiment using the Claude API."""

    def __init__(
        self,
        api_key: str,
        http_client: httpx.AsyncClient | None = None,
        model: str = CLAUDE_MODEL,
        timeout: float = 30.0,
    ) -> None:
        self._api_key = api_key
        self._client = http_client
        self._model = model
        self._timeout = timeout

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create an HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self._timeout)
        return self._client

    async def analyze(self, text: str) -> tuple[str, float] | None:
        """Analyze sentiment of a single text.

        Returns:
            A tuple of (sentiment_label, confidence_score), or None on error.
        """
        try:
            client = await self._get_client()
            response = await client.post(
                CLAUDE_API_URL,
                headers={
                    "x-api-key": self._api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": self._model,
                    "max_tokens": 100,
                    "messages": [
                        {
                            "role": "user",
                            "content": SENTIMENT_PROMPT.format(text=text),
                        }
                    ],
                },
            )
            response.raise_for_status()
            data = response.json()
            return self._parse_response(data)
        except Exception:
            logger.exception("Error analyzing sentiment for: %s", text[:80])
            return None

    async def analyze_batch(
        self, texts: list[str]
    ) -> list[tuple[str, float] | None]:
        """Analyze sentiment of multiple texts sequentially."""
        results: list[tuple[str, float] | None] = []
        for text in texts:
            result = await self.analyze(text)
            results.append(result)
        return results

    @staticmethod
    def _parse_response(data: dict[str, Any]) -> tuple[str, float]:
        """Parse Claude API response into sentiment label and confidence."""
        try:
            content = data.get("content", [])
            if not content:
                return ("neutral", 0.5)

            text = content[0].get("text", "")
            # Extract JSON from response (handle potential markdown wrapping)
            text = text.strip()
            if text.startswith("```"):
                lines = text.split("\n")
                text = "\n".join(lines[1:-1])

            parsed = json.loads(text)
            sentiment = parsed.get("sentiment", "neutral").lower()
            confidence = float(parsed.get("confidence", 0.5))

            # Validate sentiment label
            if sentiment not in ("bullish", "bearish", "neutral"):
                sentiment = "neutral"

            # Clamp confidence to [0, 1]
            confidence = max(0.0, min(1.0, confidence))

            return (sentiment, confidence)
        except (json.JSONDecodeError, KeyError, IndexError, TypeError):
            logger.warning("Could not parse sentiment response")
            return ("neutral", 0.5)
