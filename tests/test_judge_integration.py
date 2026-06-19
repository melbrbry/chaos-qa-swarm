"""Integration tests for Judge sandbox execution."""

from __future__ import annotations

import os

import pytest

from judge.executor import evaluate_payload, evaluate_payloads
from judge.models import PayloadRequest, Verdict
from judge.sandbox import LocalSandbox, create_sandbox

pytestmark = pytest.mark.integration

LOYALTY_TRAP = PayloadRequest(
  path="/api/loyalty/score",
  body={"account_type": "legacy", "months_active": 0, "base_points": 100},
)

LOYALTY_NEAR_MISS = PayloadRequest(
  path="/api/loyalty/score",
  body={"account_type": "legacy", "months_active": 1, "base_points": 100},
)

ITEMS_TRAP = PayloadRequest(
  path="/api/items/summary",
  body={"items": [], "operation": "mean", "adjustment_mode": "normalized"},
)

REPORT_TRAP = PayloadRequest(
  path="/api/report/aggregate",
  body={"groups": [[], [7, 8]], "metric": "throughput"},
)

LOGIC_ERROR_CHECK = PayloadRequest(
  path="/api/loyalty/score",
  body={"account_type": "legacy", "months_active": 1, "base_points": 100},
  response_checks={"score": 999.0},
)

INVALID_PATH = PayloadRequest(
  path="/api/does/not/exist",
  body={},
)

FIXED_LOYALTY_SOURCE = """\"\"\"Loyalty score endpoint.\"\"\"

from fastapi import APIRouter

from target_app.models import LoyaltyScoreRequest, LoyaltyScoreResponse

router = APIRouter(tags=[\"loyalty\"])


@router.post(\"/loyalty/score\", response_model=LoyaltyScoreResponse)
def loyalty_score(body: LoyaltyScoreRequest) -> LoyaltyScoreResponse:
  \"\"\"Compute a loyalty score from account tenure and base points.\"\"\"
  if body.account_type == \"legacy\" and body.months_active == 0:
    score = 0.0
  else:
    score = body.base_points * body.months_active / 12
  return LoyaltyScoreResponse(score=score, account_type=body.account_type)
"""


@pytest.fixture
def sandbox(monkeypatch: pytest.MonkeyPatch):
  backend = os.environ.get("JUDGE_SANDBOX", "local").strip().lower()
  if backend == "docker":
    try:
      import docker

      docker.from_env().ping()
    except Exception as exc:
      pytest.skip(f"Docker unavailable: {exc}")
  else:
    monkeypatch.setenv("JUDGE_SANDBOX", "local")
  return create_sandbox()


def test_loyalty_trap_is_vulnerable(sandbox) -> None:
  result = evaluate_payload({}, LOYALTY_TRAP, sandbox=sandbox)
  assert result.verdict == Verdict.VULNERABLE
  assert result.status_code == 500
  assert result.stack_trace


def test_loyalty_near_miss_is_robust(sandbox) -> None:
  result = evaluate_payload({}, LOYALTY_NEAR_MISS, sandbox=sandbox)
  assert result.verdict == Verdict.ROBUST
  assert result.status_code == 200


def test_items_trap_is_vulnerable(sandbox) -> None:
  result = evaluate_payload({}, ITEMS_TRAP, sandbox=sandbox)
  assert result.verdict == Verdict.VULNERABLE
  assert result.status_code == 500


def test_report_empty_first_group_is_vulnerable(sandbox) -> None:
  result = evaluate_payload({}, REPORT_TRAP, sandbox=sandbox)
  assert result.verdict == Verdict.VULNERABLE
  assert result.status_code == 500


def test_response_checks_surface_logic_error_on_200(sandbox) -> None:
  result = evaluate_payload({}, LOGIC_ERROR_CHECK, sandbox=sandbox)
  assert result.verdict == Verdict.LOGIC_ERROR
  assert result.status_code == 200


def test_invalid_path_is_invalid_request(sandbox) -> None:
  result = evaluate_payload({}, INVALID_PATH, sandbox=sandbox)
  assert result.verdict == Verdict.INVALID_REQUEST
  assert result.status_code == 404


def test_evaluate_payloads_runs_multiple_requests_in_one_session(sandbox) -> None:
  results = evaluate_payloads(
    {},
    [LOYALTY_TRAP, LOYALTY_NEAR_MISS, ITEMS_TRAP],
    sandbox=sandbox,
  )
  assert len(results) == 3
  assert results[0].verdict == Verdict.VULNERABLE
  assert results[1].verdict == Verdict.ROBUST
  assert results[2].verdict == Verdict.VULNERABLE


def test_patched_loyalty_trap_becomes_robust() -> None:
  sandbox = LocalSandbox()
  result = evaluate_payload(
    {"target_app/routes/loyalty.py": FIXED_LOYALTY_SOURCE},
    LOYALTY_TRAP,
    sandbox=sandbox,
  )
  assert result.verdict == Verdict.ROBUST
  assert result.status_code == 200
