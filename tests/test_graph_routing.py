"""Unit tests for swarm graph routing."""

from graph.routing import route_after_probe, route_after_verify
from graph.state import RunStatus, SwarmState
from judge.models import EvaluationResult, PayloadRequest, Verdict


def _failure() -> EvaluationResult:
  return EvaluationResult(
    verdict=Verdict.VULNERABLE,
    status_code=500,
    request=PayloadRequest(path="/api/loyalty/score", body={}),
  )


def test_route_after_probe_success() -> None:
  assert route_after_probe(SwarmState(active_failure=None)) == "end"


def test_route_after_probe_to_developer() -> None:
  assert route_after_probe(SwarmState(active_failure=_failure())) == "developer"


def test_route_after_verify_to_chaos() -> None:
  state = SwarmState(status=RunStatus.RUNNING, rejection_context=None, patch_iteration=1)
  assert route_after_verify(state) == "chaos"


def test_route_after_verify_to_developer() -> None:
  state = SwarmState(
    status=RunStatus.RUNNING,
    rejection_context={"patch_attempt": 1},
    patch_iteration=1,
  )
  assert route_after_verify(state) == "developer"


def test_route_after_verify_stuck() -> None:
  state = SwarmState(status=RunStatus.STUCK)
  assert route_after_verify(state) == "end"


def test_route_after_verify_capped() -> None:
  state = SwarmState(status=RunStatus.CAPPED)
  assert route_after_verify(state) == "end"
