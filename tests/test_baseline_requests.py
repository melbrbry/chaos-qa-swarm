"""Unit tests for baseline Judge requests."""

from judge.baseline import BASELINE_REQUESTS, baseline_requests


def test_baseline_requests_count() -> None:
  assert len(BASELINE_REQUESTS) == 10
  assert len(baseline_requests()) == 10


def test_baseline_includes_health_and_loyalty() -> None:
  paths = {request.path for request in BASELINE_REQUESTS}
  assert "/health" in paths
  assert "/api/loyalty/score" in paths


def test_health_request_uses_get() -> None:
  health = next(request for request in BASELINE_REQUESTS if request.path == "/health")
  assert health.method == "GET"
  assert health.response_checks == {"status": "ok"}
