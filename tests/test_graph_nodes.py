"""Unit tests for swarm graph nodes."""

from unittest.mock import patch

from agents.models import AttackPayload, AttackVector, ChaosStrategy, DeveloperPatch
from graph.nodes import (
  _overlay_base,
  analyze_and_generate_attacks,
  generate_patch_node,
  run_judge_probe,
)
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


def test_overlay_base_prefers_candidate_source_files() -> None:
  state = SwarmState(
    source_files={"target_app/routes/loyalty.py": "accepted"},
    candidate_source_files={"target_app/routes/items.py": "candidate"},
  )
  overlay = _overlay_base(state)
  assert overlay == {"target_app/routes/items.py": "candidate"}


def test_generate_patch_node_builds_on_candidate_overlay() -> None:
  failure = EvaluationResult(
    verdict=Verdict.VULNERABLE,
    status_code=500,
    request=PayloadRequest(path="/api/loyalty/score", body={}),
  )
  state = SwarmState(
    candidate_source_files={"target_app/routes/items.py": "# items fix"},
    active_failure=failure,
    patch_iteration=1,
  )
  loyalty_patch = DeveloperPatch(
    thought_process="fix loyalty",
    patched_files={"target_app/routes/loyalty.py": "# loyalty fix"},
  )
  with patch("graph.nodes.agent_generate_patch", return_value=loyalty_patch) as mock_patch:
    updates = generate_patch_node(state)
  mock_patch.assert_called_once()
  assert mock_patch.call_args.kwargs["source_files"] == {
    "target_app/routes/items.py": "# items fix",
  }
  assert "target_app/routes/items.py" in updates["candidate_source_files"]
  assert updates["candidate_source_files"]["target_app/routes/loyalty.py"] == "# loyalty fix"
