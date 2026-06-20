"""LangGraph node functions for the swarm loop."""

from __future__ import annotations

from agents.chaos_agent import generate_attacks
from agents.converters import strategy_to_requests
from agents.developer_agent import generate_patch as agent_generate_patch
from agents.developer_agent import merge_source_files
from graph.config import get_max_exploration_rounds, get_max_patch_iterations
from graph.state import RunStatus, SwarmState
from graph.verify_helpers import (
  build_other_failure_summaries,
  build_rejection_context,
  is_failure,
  make_startup_failure,
  pick_primary_failure,
  split_verify_results,
)
from judge.baseline import baseline_requests
from judge.executor import evaluate_payloads
from judge.models import EvaluationResult


def _first_failure(results: list) -> object | None:
  for result in results:
    if is_failure(result):
      return result
  return None


def analyze_and_generate_attacks(state: SwarmState) -> SwarmState:
  strategy = generate_attacks(source_files=state.get("source_files") or None)
  return SwarmState(
    strategy=strategy,
    attack_requests=strategy_to_requests(strategy),
    patch_iteration=0,
    rejection_context=None,
    status=RunStatus.RUNNING,
    message=f"Generated {len(strategy.attacks)} attack(s)",
  )


def run_judge_probe(state: SwarmState) -> SwarmState:
  source_files = state.get("source_files") or {}
  attack_requests = state.get("attack_requests") or []
  probe_results = evaluate_payloads(source_files, attack_requests)
  active_failure = _first_failure(probe_results)
  updates: SwarmState = SwarmState(
    probe_results=probe_results,
    active_failure=active_failure,
  )
  if active_failure is None:
    round_num = state.get("exploration_round", 0)
    updates["status"] = RunStatus.SUCCESS
    updates["message"] = f"No exploitable attacks in exploration round {round_num}"
  else:
    updates["original_failure"] = active_failure
    updates["rejection_context"] = None
  return updates


def generate_patch_node(state: SwarmState) -> SwarmState:
  patch_iteration = state.get("patch_iteration", 0) + 1
  active_failure = state.get("active_failure")
  if active_failure is None:
    raise RuntimeError("generate_patch_node called without active_failure")

  stack_trace = active_failure.stack_trace or active_failure.response_body or ""
  patch = agent_generate_patch(
    source_files=state.get("source_files") or {},
    failed_request=active_failure.request,
    stack_trace=stack_trace,
    rejection_context=state.get("rejection_context"),
  )
  candidate_source_files = merge_source_files(state.get("source_files"), patch)
  return SwarmState(
    patch_iteration=patch_iteration,
    last_patch=patch,
    candidate_source_files=candidate_source_files,
    message=f"Generated patch attempt {patch_iteration}",
  )


def run_judge_verify(state: SwarmState) -> SwarmState:
  candidate_source_files = state.get("candidate_source_files") or {}
  attack_requests = state.get("attack_requests") or []
  requests = baseline_requests() + attack_requests

  try:
    verify_results = evaluate_payloads(candidate_source_files, requests)
  except RuntimeError as exc:
    failing_result = make_startup_failure(str(exc))
    last_patch = state.get("last_patch")
    if last_patch is None:
      raise
    rejection = build_rejection_context(
      patch_attempt=state.get("patch_iteration", 1),
      rejected_patch=last_patch,
      candidate_source_files=candidate_source_files,
      failing_result=failing_result,
      failure_kind="startup",
      other_failures=[],
    )
    return SwarmState(
      verify_results=[],
      active_failure=failing_result,
      rejection_context=rejection,
      status=RunStatus.RUNNING,
      message="Candidate overlay failed to start",
    )

  baseline_results, attack_results = split_verify_results(verify_results)
  failures = [result for result in verify_results if is_failure(result)]
  if not failures:
    exploration_round = state.get("exploration_round", 0) + 1
    updates: SwarmState = SwarmState(
      verify_results=verify_results,
      source_files=candidate_source_files,
      candidate_source_files={},
      active_failure=None,
      original_failure=None,
      rejection_context=None,
      exploration_round=exploration_round,
      status=RunStatus.RUNNING,
      message=f"Patch accepted after exploration round {exploration_round}",
    )
    if exploration_round >= get_max_exploration_rounds():
      updates["status"] = RunStatus.CAPPED
      updates["message"] = (
        f"Remediation complete; exploration cap ({exploration_round}) reached"
      )
    return updates

  primary, failure_kind = pick_primary_failure(baseline_results, attack_results)
  if primary is None:
    primary = failures[0]
    failure_kind = "attack"

  last_patch = state.get("last_patch")
  if last_patch is None:
    raise RuntimeError("run_judge_verify failed without last_patch")

  other_failures = build_other_failure_summaries(baseline_results, attack_results, primary)
  rejection = build_rejection_context(
    patch_attempt=state.get("patch_iteration", 1),
    rejected_patch=last_patch,
    candidate_source_files=candidate_source_files,
    failing_result=primary,
    failure_kind=failure_kind,  # type: ignore[arg-type]
    other_failures=other_failures,
  )
  updates = SwarmState(
    verify_results=verify_results,
    active_failure=primary,
    rejection_context=rejection,
    status=RunStatus.RUNNING,
    message=f"Patch rejected ({failure_kind} failure)",
  )
  if state.get("patch_iteration", 0) >= get_max_patch_iterations():
    updates["status"] = RunStatus.STUCK
    updates["message"] = (
      f"Patch attempts exhausted ({state.get('patch_iteration', 0)})"
    )
  return updates
