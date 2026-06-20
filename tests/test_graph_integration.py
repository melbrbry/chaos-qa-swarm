"""Integration tests for the LangGraph swarm loop."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from agents.models import AttackPayload, AttackVector, ChaosStrategy, DeveloperPatch
from graph.graph import build_graph
from graph.state import RunStatus, initial_state

pytestmark = pytest.mark.integration

LOYALTY_TRAP_BODY = {
  "account_type": "legacy",
  "months_active": 0,
  "base_points": 100,
}

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


def _strategy(body: dict, hypothesis: str = "test") -> ChaosStrategy:
  return ChaosStrategy(
    attacks=[
      AttackVector(
        vulnerable_line_number=14,
        hypothesis=hypothesis,
        payload=AttackPayload(path="/api/loyalty/score", body=body),
      )
    ]
  )


@pytest.fixture(autouse=True)
def local_sandbox(monkeypatch: pytest.MonkeyPatch):
  monkeypatch.setenv("JUDGE_SANDBOX", "local")
  monkeypatch.setenv("CHAOS_MAX_EXPLORATION_ROUNDS", "3")
  monkeypatch.setenv("CHAOS_MAX_PATCH_ITERATIONS", "3")


def test_swarm_exploration_loop_reaches_success() -> None:
  trap_strategy = _strategy(LOYALTY_TRAP_BODY, hypothesis="loyalty trap")
  clean_strategy = _strategy(
    {"account_type": "legacy", "months_active": 1, "base_points": 100},
    hypothesis="near miss should be robust",
  )
  loyalty_patch = DeveloperPatch(
    thought_process="Guard zero months for legacy accounts",
    patched_files={"target_app/routes/loyalty.py": FIXED_LOYALTY_SOURCE},
  )

  with patch("graph.nodes.generate_attacks", side_effect=[trap_strategy, clean_strategy]):
    with patch("graph.nodes.agent_generate_patch", return_value=loyalty_patch):
      final_state = build_graph().invoke(initial_state())

  assert final_state["status"] == RunStatus.SUCCESS
  assert "target_app/routes/loyalty.py" in final_state["source_files"]
  assert final_state["exploration_round"] == 1
