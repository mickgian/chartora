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

QUBIT_EXTRACTION_PROMPT = (
    "You are an expert on quantum computing hardware.\n\n"
    "Given the company name and recent news headlines below,"
    " determine the latest known qubit count for this"
    " company's most advanced quantum processor.\n\n"
    "Rules:\n"
    "- Only report qubits if a headline explicitly mentions"
    " a qubit count or processor milestone.\n"
    "- If no headline mentions qubits, return null.\n"
    "- For D-Wave, report the number of qubits in their"
    " latest quantum annealer.\n"
    "- For gate-based systems, report logical or physical"
    " qubits as stated.\n\n"
    "Respond with ONLY a JSON object:\n"
    '{{"qubit_count": <integer or null>,'
    ' "source_headline": "<headline or null>"}}'
    "\n\nCompany: {company}\n\nHeadlines:\n{headlines}"
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

    async def _call_claude(
        self, prompt: str, max_tokens: int = 150
    ) -> dict[str, Any] | None:
        """Send a prompt to the Claude API and return raw response."""
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
                    "max_tokens": max_tokens,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                },
            )
            response.raise_for_status()
            result: dict[str, Any] = response.json()
            return result
        except Exception:
            logger.exception(
                "Claude API call failed: %s", prompt[:80]
            )
            return None

    async def analyze(self, text: str) -> tuple[str, float] | None:
        """Analyze sentiment of a single text.

        Returns:
            A tuple of (sentiment_label, confidence_score), or None on error.
        """
        data = await self._call_claude(
            SENTIMENT_PROMPT.format(text=text), max_tokens=100
        )
        if data is None:
            return None
        return self._parse_response(data)

    async def analyze_batch(
        self, texts: list[str]
    ) -> list[tuple[str, float] | None]:
        """Analyze sentiment of multiple texts sequentially."""
        results: list[tuple[str, float] | None] = []
        for text in texts:
            result = await self.analyze(text)
            results.append(result)
        return results

    async def extract_qubit_count(
        self,
        company_name: str,
        headlines: list[str],
    ) -> int | None:
        """Extract qubit count from news headlines via Claude.

        Returns:
            The qubit count as an integer, or None if not found.
        """
        headline_text = "\n".join(
            f"- {h}" for h in headlines[:20]
        )
        prompt = QUBIT_EXTRACTION_PROMPT.format(
            company=company_name, headlines=headline_text
        )
        data = await self._call_claude(prompt, max_tokens=150)
        if data is None:
            return None
        return self._parse_qubit_response(data)

    @staticmethod
    def _parse_qubit_response(
        data: dict[str, Any],
    ) -> int | None:
        """Parse Claude response for qubit count extraction."""
        try:
            content = data.get("content", [])
            if not content:
                return None
            text = content[0].get("text", "").strip()
            if text.startswith("```"):
                lines = text.split("\n")
                text = "\n".join(lines[1:-1])
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1:
                text = text[start : end + 1]
            parsed = json.loads(text)
            count = parsed.get("qubit_count")
            if count is None:
                return None
            count = int(count)
            return count if count > 0 else None
        except (
            json.JSONDecodeError,
            KeyError,
            IndexError,
            TypeError,
            ValueError,
        ):
            logger.warning("Could not parse qubit extraction response")
            return None

    @staticmethod
    def _parse_response(data: dict[str, Any]) -> tuple[str, float] | None:
        """Parse Claude API response into sentiment label and confidence."""
        try:
            content = data.get("content", [])
            if not content:
                logger.warning("Empty content in sentiment response")
                return None

            text = content[0].get("text", "")
            # Extract JSON from response (handle potential markdown wrapping)
            text = text.strip()
            if text.startswith("```"):
                lines = text.split("\n")
                text = "\n".join(lines[1:-1])

            # Try to extract JSON object if surrounded by other text
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1:
                text = text[start : end + 1]

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
            content = data.get("content")
            raw = content[0].get("text", "") if content else ""
            logger.warning(
                "Could not parse sentiment response: %s", raw[:200]
            )
            return None
