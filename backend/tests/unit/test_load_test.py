"""Unit tests for load test utilities."""

from scripts.load_test import LoadTestReport, percentile


class TestPercentile:
    def test_empty_list(self):
        assert percentile([], 95.0) == 0.0

    def test_single_value(self):
        assert percentile([5.0], 50.0) == 5.0

    def test_p50_of_sorted_list(self):
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = percentile(data, 50.0)
        assert result == 3.0

    def test_p95_of_list(self):
        data = list(range(1, 101))
        result = percentile([float(x) for x in data], 95.0)
        assert result >= 95.0

    def test_p99_of_list(self):
        data = list(range(1, 101))
        result = percentile([float(x) for x in data], 99.0)
        assert result >= 99.0


class TestLoadTestReport:
    def test_report_fields(self):
        report = LoadTestReport(
            total_requests=100,
            total_time_seconds=10.0,
            avg_response_ms=50.0,
            p95_response_ms=120.0,
            p99_response_ms=200.0,
            requests_per_second=10.0,
            error_count=2,
            error_rate=0.02,
        )
        assert report.total_requests == 100
        assert report.error_rate == 0.02
