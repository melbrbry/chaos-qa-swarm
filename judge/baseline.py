"""Happy-path baseline requests for regression gating in the Judge sandbox."""

from __future__ import annotations

from judge.models import PayloadRequest

BASELINE_REQUESTS: list[PayloadRequest] = [
  PayloadRequest(
    method="GET",
    path="/health",
    response_checks={"status": "ok"},
  ),
  PayloadRequest(
    path="/api/items/summary",
    body={
      "items": [
        {"name": "alpha", "value": 10.0},
        {"name": "beta", "value": 20.0},
        {"name": "gamma", "value": 30.0},
      ],
      "operation": "mean",
    },
    response_checks={"result": 20.0, "count": 3},
  ),
  PayloadRequest(
    path="/api/items/summary",
    body={
      "items": [
        {"name": "alpha", "value": 10.0},
        {"name": "beta", "value": 15.0},
      ],
      "operation": "sum",
    },
    response_checks={"result": 25.0, "count": 2},
  ),
  PayloadRequest(
    path="/api/items/summary",
    body={"items": [], "operation": "mean", "adjustment_mode": "standard"},
    response_checks={"result": 0.0, "count": 0},
  ),
  PayloadRequest(
    path="/api/users/lookup",
    body={
      "users": [
        {"id": 1, "role": "admin", "name": "Ada"},
        {"id": 2, "role": "viewer", "name": "Grace"},
      ],
      "filter": {"field": "role", "value": "admin"},
    },
    response_checks={"user": {"id": 1, "role": "admin", "name": "Ada"}},
  ),
  PayloadRequest(
    path="/api/report/aggregate",
    body={"groups": [[1, 2], [3, 4, 5]], "metric": "throughput"},
    response_checks={"metric": "throughput", "count": 5, "first_value": 1},
  ),
  PayloadRequest(
    path="/api/prorate",
    body={
      "total": 100.0,
      "parts": [
        {"label": "team_a", "weight": 1.0},
        {"label": "team_b", "weight": 3.0},
      ],
      "denominator": 4.0,
    },
    response_checks={
      "denominator_used": 4.0,
      "allocations": [
        {"label": "team_a", "amount": 25.0},
        {"label": "team_b", "amount": 75.0},
      ],
    },
  ),
  PayloadRequest(
    path="/api/prorate",
    body={
      "total": 100.0,
      "parts": [
        {"label": "team_a", "weight": 1.0},
        {"label": "team_b", "weight": 3.0},
      ],
      "denominator": 0.0,
      "strict_zero_weights": False,
    },
  ),
  PayloadRequest(
    path="/api/loyalty/score",
    body={"account_type": "standard", "months_active": 12, "base_points": 100},
    response_checks={"score": 100.0, "account_type": "standard"},
  ),
  PayloadRequest(
    path="/api/loyalty/score",
    body={"account_type": "legacy", "months_active": 1, "base_points": 100},
    response_checks={"score": 100 / 12, "account_type": "legacy"},
  ),
]


def baseline_requests() -> list[PayloadRequest]:
  """Return a copy of baseline regression requests."""
  return list(BASELINE_REQUESTS)
