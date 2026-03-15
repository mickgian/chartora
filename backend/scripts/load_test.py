"""Load testing script for Chartora API using asyncio + httpx."""

from __future__ import annotations

import argparse
import asyncio
import statistics
import time
from dataclasses import dataclass, field

import httpx

ENDPOINTS: list[str] = [
    "/health",
    "/api/v1/leaderboard",
    "/api/v1/companies/ionq",
    "/api/v1/rankings/patents",
]


@dataclass
class RequestResult:
    """Result of a single HTTP request."""

    endpoint: str
    status_code: int
    elapsed_ms: float
    error: str | None = None


@dataclass
class LoadTestReport:
    """Aggregated load test report."""

    total_requests: int
    total_time_seconds: float
    avg_response_ms: float
    p95_response_ms: float
    p99_response_ms: float
    requests_per_second: float
    error_count: int
    error_rate: float
    per_endpoint: dict[str, dict[str, float]] = field(default_factory=dict)


def percentile(data: list[float], pct: float) -> float:
    """Compute the given percentile from a sorted list of values."""
    if not data:
        return 0.0
    sorted_data = sorted(data)
    k = (len(sorted_data) - 1) * (pct / 100.0)
    f = int(k)
    c = f + 1
    if c >= len(sorted_data):
        return sorted_data[f]
    return sorted_data[f] + (k - f) * (sorted_data[c] - sorted_data[f])


async def make_request(
    client: httpx.AsyncClient,
    base_url: str,
    endpoint: str,
) -> RequestResult:
    """Send a single GET request and measure response time."""
    url = f"{base_url}{endpoint}"
    start = time.perf_counter()
    try:
        response = await client.get(url)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        return RequestResult(
            endpoint=endpoint,
            status_code=response.status_code,
            elapsed_ms=elapsed_ms,
        )
    except httpx.HTTPError as exc:
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        return RequestResult(
            endpoint=endpoint,
            status_code=0,
            elapsed_ms=elapsed_ms,
            error=str(exc),
        )


async def run_load_test(
    base_url: str,
    num_requests: int,
    concurrency: int,
) -> LoadTestReport:
    """Run the load test with the given parameters."""
    semaphore = asyncio.Semaphore(concurrency)
    results: list[RequestResult] = []

    async def bounded_request(
        client: httpx.AsyncClient,
        endpoint: str,
    ) -> RequestResult:
        async with semaphore:
            return await make_request(client, base_url, endpoint)

    # Distribute requests round-robin across endpoints
    tasks: list[asyncio.Task[RequestResult]] = []
    start_time = time.perf_counter()

    async with httpx.AsyncClient(timeout=30.0) as client:
        for i in range(num_requests):
            endpoint = ENDPOINTS[i % len(ENDPOINTS)]
            task = asyncio.create_task(bounded_request(client, endpoint))
            tasks.append(task)

        results = await asyncio.gather(*tasks)

    total_time = time.perf_counter() - start_time

    # Compute statistics
    all_times = [r.elapsed_ms for r in results]
    error_count = sum(1 for r in results if r.error is not None or r.status_code >= 400)

    # Per-endpoint stats
    per_endpoint: dict[str, dict[str, float]] = {}
    for endpoint in ENDPOINTS:
        endpoint_times = [r.elapsed_ms for r in results if r.endpoint == endpoint]
        if endpoint_times:
            per_endpoint[endpoint] = {
                "count": float(len(endpoint_times)),
                "avg_ms": statistics.mean(endpoint_times),
                "p95_ms": percentile(endpoint_times, 95.0),
                "p99_ms": percentile(endpoint_times, 99.0),
            }

    return LoadTestReport(
        total_requests=num_requests,
        total_time_seconds=total_time,
        avg_response_ms=statistics.mean(all_times) if all_times else 0.0,
        p95_response_ms=percentile(all_times, 95.0),
        p99_response_ms=percentile(all_times, 99.0),
        requests_per_second=num_requests / total_time if total_time > 0 else 0.0,
        error_count=error_count,
        error_rate=error_count / num_requests if num_requests > 0 else 0.0,
        per_endpoint=per_endpoint,
    )


def print_report(report: LoadTestReport) -> None:
    """Print a formatted load test report to stdout."""
    print("\n" + "=" * 60)
    print("  CHARTORA LOAD TEST REPORT")
    print("=" * 60)
    print(f"  Total requests:     {report.total_requests}")
    print(f"  Total time:         {report.total_time_seconds:.2f}s")
    print(f"  Requests/sec:       {report.requests_per_second:.1f}")
    print(f"  Avg response time:  {report.avg_response_ms:.1f}ms")
    print(f"  P95 response time:  {report.p95_response_ms:.1f}ms")
    print(f"  P99 response time:  {report.p99_response_ms:.1f}ms")
    print(f"  Errors:             {report.error_count} ({report.error_rate:.1%})")
    print("-" * 60)

    for endpoint, stats in report.per_endpoint.items():
        print(f"  {endpoint}")
        print(f"    Requests: {int(stats['count'])}  "
              f"Avg: {stats['avg_ms']:.1f}ms  "
              f"P95: {stats['p95_ms']:.1f}ms  "
              f"P99: {stats['p99_ms']:.1f}ms")

    print("=" * 60 + "\n")


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Chartora API Load Tester")
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="Base URL of the API (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--num-requests",
        type=int,
        default=100,
        help="Total number of requests to send (default: 100)",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=10,
        help="Number of concurrent requests (default: 10)",
    )
    return parser.parse_args()


def main() -> None:
    """Entry point for the load test script."""
    args = parse_args()
    print(f"Starting load test against {args.base_url}")
    print(f"  Requests: {args.num_requests}, Concurrency: {args.concurrency}")
    print(f"  Endpoints: {', '.join(ENDPOINTS)}")

    report = asyncio.run(
        run_load_test(
            base_url=args.base_url,
            num_requests=args.num_requests,
            concurrency=args.concurrency,
        )
    )
    print_report(report)


if __name__ == "__main__":
    main()
