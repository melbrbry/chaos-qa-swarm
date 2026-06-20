"""Unit tests for swarm graph nodes."""

from unittest.mock import patch

from agents.models import AttackPayload, AttackVector, ChaosStrategy, DeveloperPatch
from graph.nodes import analyze_and_generate_attacks, run_judge_probe
from graph.state import RunStatus, SwarmState, initial_state
from judge.models import EvaluationResult, PayloadRequest, Verdict


def _strategy(path: str = "/api/loyalty/score") -> ChaosStrategy:
  return ChaosStrategy(
    attacks=[
      AttackVector(
        vulnerable_line_number=1,
        hypothesis="test",
        payload=AttackPayload(path=path, body={"x": 1}),
      )
    ]
  )


def test_analyze_and_generate_attacks() -> None:
  strategy = _strategy()
  with patch("graph.nodes.generate_attacks", return_value=strategy):
    updates = analyze_and_generate_attacks(initial_state())
  assert updates["strategy"] == strategy
  assert len(updates["attack_requests"]) == 1
  assert updates["patch_iteration"] == 0


def test_run_judge_probe_no_failures() -> None:
  robust = EvaluationResult(
    verdict=Verdict.ROBUST,
    status_code=200,
    request=PayloadRequest(path="/api/a", body={}),
  )
  state = SwarmState(
    source_files={},
    attack_requests=[PayloadRequest(path="/api/a", body={})],
    exploration_round=0,
  )
  with patch("graph.nodes.evaluate_payloads", return_value=[robust]):
    updates = run_judge_probe(state)
  assert updates["active_failure"] is None
  assert updates["status"] == RunStatus.SUCCESS


def test_run_judge_probe_sets_original_failure() -> None:
  failure = EvaluationResult(
    verdict=Verdict.VULNERABLE,
    status_code=500,
    request=PayloadRequest(path="/api/a", body={}),
  )
  state = SwarmState(
    source_files={},
    attack_requests=[PayloadRequest(path="/api/a", body={})],
  )
  with patch("graph.nodes.evaluate_payloads", return_value=[failure]):
    updates = run_judge_probe(state)
  assert updates["active_failure"] == failure
  assert updates["original_failure"] == failure
