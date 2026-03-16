"""Unit tests for the Claude sentiment analysis adapter."""

import httpx
import pytest

from src.infrastructure.sentiment import ClaudeSentimentAnalyzer


@pytest.fixture
def adapter():
    return ClaudeSentimentAnalyzer(api_key="test-api-key")


class TestParseResponse:
    def test_parses_bullish_response(self):
        data = {"content": [{"text": '{"sentiment": "bullish", "confidence": 0.92}'}]}
        sentiment, confidence = ClaudeSentimentAnalyzer._parse_response(data)
        assert sentiment == "bullish"
        assert confidence == 0.92

    def test_parses_bearish_response(self):
        data = {"content": [{"text": '{"sentiment": "bearish", "confidence": 0.78}'}]}
        sentiment, confidence = ClaudeSentimentAnalyzer._parse_response(data)
        assert sentiment == "bearish"
        assert confidence == 0.78

    def test_parses_neutral_response(self):
        data = {"content": [{"text": '{"sentiment": "neutral", "confidence": 0.55}'}]}
        sentiment, confidence = ClaudeSentimentAnalyzer._parse_response(data)
        assert sentiment == "neutral"
        assert confidence == 0.55

    def test_handles_markdown_wrapped_json(self):
        data = {
            "content": [
                {"text": '```json\n{"sentiment": "bullish", "confidence": 0.85}\n```'}
            ]
        }
        sentiment, confidence = ClaudeSentimentAnalyzer._parse_response(data)
        assert sentiment == "bullish"
        assert confidence == 0.85

    def test_handles_empty_content(self):
        data = {"content": []}
        result = ClaudeSentimentAnalyzer._parse_response(data)
        assert result is None

    def test_handles_missing_content(self):
        data = {}
        result = ClaudeSentimentAnalyzer._parse_response(data)
        assert result is None

    def test_handles_invalid_json(self):
        data = {"content": [{"text": "This is not JSON at all no braces"}]}
        result = ClaudeSentimentAnalyzer._parse_response(data)
        assert result is None

    def test_extracts_json_from_surrounding_text(self):
        data = {
            "content": [
                {
                    "text": "Here is my analysis: "
                    '{"sentiment": "bullish", "confidence": 0.75}'
                    " hope that helps!"
                }
            ]
        }
        sentiment, confidence = ClaudeSentimentAnalyzer._parse_response(data)
        assert sentiment == "bullish"
        assert confidence == 0.75

    def test_handles_invalid_sentiment_label(self):
        data = {
            "content": [{"text": '{"sentiment": "very_positive", "confidence": 0.9}'}]
        }
        sentiment, _confidence = ClaudeSentimentAnalyzer._parse_response(data)
        assert sentiment == "neutral"

    def test_clamps_confidence_above_1(self):
        data = {"content": [{"text": '{"sentiment": "bullish", "confidence": 1.5}'}]}
        _, confidence = ClaudeSentimentAnalyzer._parse_response(data)
        assert confidence == 1.0

    def test_clamps_confidence_below_0(self):
        data = {"content": [{"text": '{"sentiment": "bearish", "confidence": -0.5}'}]}
        _, confidence = ClaudeSentimentAnalyzer._parse_response(data)
        assert confidence == 0.0


class TestAnalyze:
    @pytest.mark.asyncio
    async def test_analyze_success(self):
        mock_response = httpx.Response(
            200,
            json={
                "content": [{"text": '{"sentiment": "bullish", "confidence": 0.88}'}]
            },
            request=httpx.Request("POST", "https://api.anthropic.com/v1/messages"),
        )
        mock_client = httpx.AsyncClient(
            transport=httpx.MockTransport(lambda req: mock_response)
        )
        analyzer = ClaudeSentimentAnalyzer(api_key="test-key", http_client=mock_client)

        sentiment, confidence = await analyzer.analyze(
            "IonQ reports record revenue growth"
        )

        assert sentiment == "bullish"
        assert confidence == 0.88

    @pytest.mark.asyncio
    async def test_analyze_api_error_returns_none(self):
        mock_response = httpx.Response(
            500,
            json={"error": "Internal Server Error"},
            request=httpx.Request("POST", "https://api.anthropic.com/v1/messages"),
        )
        mock_client = httpx.AsyncClient(
            transport=httpx.MockTransport(lambda req: mock_response)
        )
        analyzer = ClaudeSentimentAnalyzer(api_key="test-key", http_client=mock_client)

        result = await analyzer.analyze("Some text")
        assert result is None

    @pytest.mark.asyncio
    async def test_analyze_network_error_returns_none(self):
        async def raise_error(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("Connection failed")

        mock_client = httpx.AsyncClient(transport=httpx.MockTransport(raise_error))
        analyzer = ClaudeSentimentAnalyzer(api_key="test-key", http_client=mock_client)

        result = await analyzer.analyze("Some text")
        assert result is None


class TestAnalyzeBatch:
    @pytest.mark.asyncio
    async def test_analyze_batch(self):
        responses = iter(
            [
                '{"sentiment": "bullish", "confidence": 0.9}',
                '{"sentiment": "bearish", "confidence": 0.7}',
                '{"sentiment": "neutral", "confidence": 0.5}',
            ]
        )

        def transport(request: httpx.Request) -> httpx.Response:
            text = next(responses)
            return httpx.Response(
                200,
                json={"content": [{"text": text}]},
                request=request,
            )

        mock_client = httpx.AsyncClient(transport=httpx.MockTransport(transport))
        analyzer = ClaudeSentimentAnalyzer(api_key="test-key", http_client=mock_client)

        results = await analyzer.analyze_batch(
            ["Good news", "Bad news", "Neutral news"]
        )

        assert len(results) == 3
        assert results[0] == ("bullish", 0.9)
        assert results[1] == ("bearish", 0.7)
        assert results[2] == ("neutral", 0.5)


class TestParseQubitResponse:
    def test_parses_valid_qubit_count(self):
        data = {
            "content": [
                {
                    "text": '{"qubit_count": 1121, '
                    '"source_headline": "IBM unveils 1121-qubit processor"}'
                }
            ]
        }
        result = ClaudeSentimentAnalyzer._parse_qubit_response(data)
        assert result == 1121

    def test_returns_none_when_null(self):
        data = {"content": [{"text": '{"qubit_count": null, "source_headline": null}'}]}
        result = ClaudeSentimentAnalyzer._parse_qubit_response(data)
        assert result is None

    def test_returns_none_for_zero(self):
        data = {"content": [{"text": '{"qubit_count": 0, "source_headline": null}'}]}
        result = ClaudeSentimentAnalyzer._parse_qubit_response(data)
        assert result is None

    def test_handles_surrounding_text(self):
        data = {
            "content": [
                {
                    "text": "Here is the result: "
                    '{"qubit_count": 84, "source_headline": "Rigetti 84-qubit"}'
                    " based on the headlines."
                }
            ]
        }
        result = ClaudeSentimentAnalyzer._parse_qubit_response(data)
        assert result == 84

    def test_handles_empty_content(self):
        data = {"content": []}
        result = ClaudeSentimentAnalyzer._parse_qubit_response(data)
        assert result is None

    def test_handles_invalid_json(self):
        data = {"content": [{"text": "I cannot determine the qubit count"}]}
        result = ClaudeSentimentAnalyzer._parse_qubit_response(data)
        assert result is None

    def test_handles_markdown_wrapped(self):
        data = {
            "content": [
                {
                    "text": "```json\n"
                    '{"qubit_count": 5000, "source_headline": "D-Wave"}\n'
                    "```"
                }
            ]
        }
        result = ClaudeSentimentAnalyzer._parse_qubit_response(data)
        assert result == 5000


class TestExtractQubitCount:
    @pytest.mark.asyncio
    async def test_extract_qubit_count_success(self):
        mock_response = httpx.Response(
            200,
            json={
                "content": [
                    {"text": '{"qubit_count": 1121, "source_headline": "IBM Condor"}'}
                ]
            },
            request=httpx.Request("POST", "https://api.anthropic.com/v1/messages"),
        )
        mock_client = httpx.AsyncClient(
            transport=httpx.MockTransport(lambda req: mock_response)
        )
        analyzer = ClaudeSentimentAnalyzer(api_key="test-key", http_client=mock_client)

        result = await analyzer.extract_qubit_count(
            "IBM", ["IBM unveils 1121-qubit Condor processor"]
        )
        assert result == 1121

    @pytest.mark.asyncio
    async def test_extract_qubit_count_no_mention(self):
        mock_response = httpx.Response(
            200,
            json={
                "content": [{"text": '{"qubit_count": null, "source_headline": null}'}]
            },
            request=httpx.Request("POST", "https://api.anthropic.com/v1/messages"),
        )
        mock_client = httpx.AsyncClient(
            transport=httpx.MockTransport(lambda req: mock_response)
        )
        analyzer = ClaudeSentimentAnalyzer(api_key="test-key", http_client=mock_client)

        result = await analyzer.extract_qubit_count(
            "IBM", ["IBM reports quarterly earnings"]
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_extract_qubit_count_api_error(self):
        mock_response = httpx.Response(
            500,
            json={"error": "Server error"},
            request=httpx.Request("POST", "https://api.anthropic.com/v1/messages"),
        )
        mock_client = httpx.AsyncClient(
            transport=httpx.MockTransport(lambda req: mock_response)
        )
        analyzer = ClaudeSentimentAnalyzer(api_key="test-key", http_client=mock_client)

        result = await analyzer.extract_qubit_count("IBM", ["Some headline"])
        assert result is None
