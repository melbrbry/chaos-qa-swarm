#!/usr/bin/env python3
"""Export OpenAPI and per-endpoint JSON Schema files from Pydantic models."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from target_app.main import app
from target_app.models import (
  ItemsSummaryRequest,
  LoyaltyScoreRequest,
  ProrateRequest,
  ReportAggregateRequest,
  UsersLookupRequest,
)

ROOT = Path(__file__).resolve().parent.parent
SCHEMAS_DIR = ROOT / "schemas"
ENDPOINTS_DIR = SCHEMAS_DIR / "endpoints"

ENDPOINT_SPECS: list[dict[str, Any]] = [
  {
    "file": "items_summary.json",
    "method": "POST",
    "path": "/api/items/summary",
    "summary": "Compute mean or sum over numeric items",
    "request_model": ItemsSummaryRequest,
    "example_valid_payload": {
      "items": [
        {"name": "alpha", "value": 10.0},
        {"name": "beta", "value": 20.0},
        {"name": "gamma", "value": 30.0},
      ],
      "operation": "mean",
    },
  },
  {
    "file": "users_lookup.json",
    "method": "POST",
    "path": "/api/users/lookup",
    "summary": "Return the first user matching filter criteria",
    "request_model": UsersLookupRequest,
    "example_valid_payload": {
      "users": [
        {"id": 1, "role": "admin", "name": "Ada"},
        {"id": 2, "role": "viewer", "name": "Grace"},
      ],
      "filter": {"field": "role", "value": "admin"},
    },
  },
  {
    "file": "report_aggregate.json",
    "method": "POST",
    "path": "/api/report/aggregate",
    "summary": "Flatten nested groups and return aggregate metadata",
    "request_model": ReportAggregateRequest,
    "example_valid_payload": {
      "groups": [[1, 2], [3, 4, 5]],
      "metric": "throughput",
    },
  },
  {
    "file": "prorate.json",
    "method": "POST",
    "path": "/api/prorate",
    "summary": "Distribute a total across weighted parts",
    "request_model": ProrateRequest,
    "example_valid_payload": {
      "total": 100.0,
      "parts": [
        {"label": "team_a", "weight": 1.0},
        {"label": "team_b", "weight": 3.0},
      ],
      "denominator": 4.0,
    },
  },
  {
    "file": "loyalty_score.json",
    "method": "POST",
    "path": "/api/loyalty/score",
    "summary": "Compute loyalty score from account tenure and base points",
    "request_model": LoyaltyScoreRequest,
    "example_valid_payload": {
      "account_type": "standard",
      "months_active": 12,
      "base_points": 100,
    },
  },
]


def export_openapi() -> None:
  SCHEMAS_DIR.mkdir(parents=True, exist_ok=True)
  openapi_path = SCHEMAS_DIR / "api_openapi.json"
  openapi_path.write_text(
    json.dumps(app.openapi(), indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
  )
  print(f"Wrote {openapi_path}")


def export_endpoint_schemas() -> None:
  ENDPOINTS_DIR.mkdir(parents=True, exist_ok=True)
  for spec in ENDPOINT_SPECS:
    request_model = spec["request_model"]
    payload = {
      "endpoint": {
        "method": spec["method"],
        "path": spec["path"],
        "summary": spec["summary"],
      },
      "request_schema": request_model.model_json_schema(),
      "example_valid_payload": spec["example_valid_payload"],
    }
    output_path = ENDPOINTS_DIR / spec["file"]
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {output_path}")


def main() -> None:
  export_openapi()
  export_endpoint_schemas()


if __name__ == "__main__":
  main()
