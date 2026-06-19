"""Happy-path baseline regression tests."""

from fastapi.testclient import TestClient


def test_health_ok(client: TestClient) -> None:
  response = client.get("/health")
  assert response.status_code == 200
  assert response.json() == {"status": "ok"}


def test_items_summary_mean_happy(client: TestClient) -> None:
  payload = {
    "items": [
      {"name": "alpha", "value": 10.0},
      {"name": "beta", "value": 20.0},
      {"name": "gamma", "value": 30.0},
    ],
    "operation": "mean",
  }
  response = client.post("/api/items/summary", json=payload)
  assert response.status_code == 200
  body = response.json()
  assert body["result"] == 20.0
  assert body["count"] == 3


def test_items_summary_sum_happy(client: TestClient) -> None:
  payload = {
    "items": [
      {"name": "alpha", "value": 10.0},
      {"name": "beta", "value": 15.0},
    ],
    "operation": "sum",
  }
  response = client.post("/api/items/summary", json=payload)
  assert response.status_code == 200
  body = response.json()
  assert body["result"] == 25.0
  assert body["count"] == 2


def test_items_summary_empty_mean_standard_mode_ok(client: TestClient) -> None:
  payload = {"items": [], "operation": "mean", "adjustment_mode": "standard"}
  response = client.post("/api/items/summary", json=payload)
  assert response.status_code == 200
  assert response.json() == {"result": 0.0, "count": 0}


def test_users_lookup_happy(client: TestClient) -> None:
  payload = {
    "users": [
      {"id": 1, "role": "admin", "name": "Ada"},
      {"id": 2, "role": "viewer", "name": "Grace"},
    ],
    "filter": {"field": "role", "value": "admin"},
  }
  response = client.post("/api/users/lookup", json=payload)
  assert response.status_code == 200
  body = response.json()
  assert body["user"] == {"id": 1, "role": "admin", "name": "Ada"}


def test_report_aggregate_happy(client: TestClient) -> None:
  payload = {
    "groups": [[1, 2], [3, 4, 5]],
    "metric": "throughput",
  }
  response = client.post("/api/report/aggregate", json=payload)
  assert response.status_code == 200
  body = response.json()
  assert body["metric"] == "throughput"
  assert body["count"] == 5
  assert body["first_value"] == 1


def test_prorate_happy(client: TestClient) -> None:
  payload = {
    "total": 100.0,
    "parts": [
      {"label": "team_a", "weight": 1.0},
      {"label": "team_b", "weight": 3.0},
    ],
    "denominator": 4.0,
  }
  response = client.post("/api/prorate", json=payload)
  assert response.status_code == 200
  body = response.json()
  assert body["denominator_used"] == 4.0
  assert body["allocations"] == [
    {"label": "team_a", "amount": 25.0},
    {"label": "team_b", "amount": 75.0},
  ]


def test_prorate_zero_denominator_without_strict_flag_ok(client: TestClient) -> None:
  payload = {
    "total": 100.0,
    "parts": [
      {"label": "team_a", "weight": 1.0},
      {"label": "team_b", "weight": 3.0},
    ],
    "denominator": 0.0,
    "strict_zero_weights": False,
  }
  response = client.post("/api/prorate", json=payload)
  assert response.status_code == 200


def test_loyalty_score_happy(client: TestClient) -> None:
  payload = {
    "account_type": "standard",
    "months_active": 12,
    "base_points": 100,
  }
  response = client.post("/api/loyalty/score", json=payload)
  assert response.status_code == 200
  body = response.json()
  assert body["score"] == 100.0
  assert body["account_type"] == "standard"


def test_loyalty_score_legacy_near_miss_ok(client: TestClient) -> None:
  payload = {
    "account_type": "legacy",
    "months_active": 1,
    "base_points": 100,
  }
  response = client.post("/api/loyalty/score", json=payload)
  assert response.status_code == 200
  body = response.json()
  assert body["score"] == 100 * 1 / 12
