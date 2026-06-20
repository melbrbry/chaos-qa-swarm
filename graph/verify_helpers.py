"""Helpers for judge_verify failure analysis."""

from __future__ import annotations

from graph.config import get_max_patch_iterations
from judge.baseline import baseline_requests
from judge.models import EvaluationResult, PayloadRequest, Verdict

FAILURE_VERDICTS = {Verdict.VULNERABLE, Verdict.LOGIC_ERROR}


def is_failure(result: EvaluationResult) -> bool:
  return result.verdict in FAILURE_VERDICTS


def baseline_count() -> int:
  return len(baseline_requests())


def split_verify_results(
  results: list[EvaluationResult],
) -> tuple[list[EvaluationResult], list[EvaluationResult]]:
  split_at = baseline_count()
  return results[:split_at], results[split_at:]


def summarize_failure(result: EvaluationResult) -> str:
  return (
    f"{result.request.method} {result.request.path} "
    f"→ {result.verdict.value} (status {result.status_code})"
  )


def pick_primary_failure(
  baseline_results: list[EvaluationResult],
  attack_results: list[EvaluationResult],
) -> tuple[EvaluationResult | None, str]:
  for result in baseline_results:
    if is_failure(result):
      return result, "baseline"
  for result in attack_results:
    if is_failure(result):
      return result, "attack"
  return None, "attack"


def build_other_failure_summaries(
  baseline_results: list[EvaluationResult],
  attack_results: list[EvaluationResult],
  primary: EvaluationResult,
) -> list[str]:
  summaries = []
  for result in baseline_results + attack_results:
    if is_failure(result) and result is not primary:
      summaries.append(summarize_failure(result))
  return summaries


def make_startup_failure(error_message: str) -> EvaluationResult:
  request = PayloadRequest(path="/health", method="GET")
  return EvaluationResult(
    verdict=Verdict.VULNERABLE,
    status_code=None,
    response_body=error_message,
    stack_trace=error_message,
    request=request,
  )


def build_rejection_context(
  *,
  patch_attempt: int,
  rejected_patch,
  candidate_source_files: dict[str, str],
  failing_result: EvaluationResult,
  failure_kind: str,
  other_failures: list[str],
):
  from agents.models import PatchRejectionContext

  return PatchRejectionContext(
    patch_attempt=patch_attempt,
    max_patch_attempts=get_max_patch_iterations(),
    rejected_patch=rejected_patch,
    candidate_files=sorted(candidate_source_files.keys()),
    failure_kind=failure_kind,  # type: ignore[arg-type]
    failing_result=failing_result,
    expected_checks=failing_result.request.response_checks,
    actual_response=failing_result.response_json,
    other_failures=other_failures,
  )
