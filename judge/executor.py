"""Orchestrate sandbox sessions and payload evaluation."""

from __future__ import annotations

import json
import shutil
import time
from typing import Any

import httpx

from judge.criteria import classify_result, extract_stack_trace
from judge.models import EvaluationResult, PayloadRequest, Verdict
from judge.sandbox import Sandbox, create_sandbox
from judge.source_overlay import overlay_source

REQUEST_TIMEOUT_S = 10.0


def _parse_response_json(response_body: str) -> dict[str, Any] | None:
  if not response_body:
    return None
  try:
    payload = json.loads(response_body)
  except json.JSONDecodeError:
    return None
  return payload if isinstance(payload, dict) else None


def _execute_request(
  base_url: str,
  request: PayloadRequest,
) -> tuple[int | None, str, bool, bool]:
  url = f"{base_url.rstrip('/')}{request.path}"
  try:
    with httpx.Client(timeout=REQUEST_TIMEOUT_S) as client:
      response = client.request(request.method.upper(), url, json=request.body)
      return response.status_code, response.text, False, False
  except httpx.TimeoutException:
    return None, "", True, False
  except httpx.HTTPError:
    return None, "", False, True


def evaluate_payloads(
  source_files: dict[str, str],
  requests: list[PayloadRequest],
  *,
  sandbox: Sandbox | None = None,
) -> list[EvaluationResult]:
  """Boot sandbox once, evaluate all requests, then tear down."""
  if not requests:
    return []

  overlay_root = overlay_source(source_files)
  active_sandbox = sandbox or create_sandbox()
  results: list[EvaluationResult] = []

  try:
    base_url = active_sandbox.start(overlay_root)
    for request in requests:
      started = time.monotonic()
      status_code, response_body, timed_out, connection_error = _execute_request(
        base_url, request
      )
      crashed = not active_sandbox.is_running()
      response_json = _parse_response_json(response_body)
      if connection_error and not crashed and not timed_out:
        timed_out = True
      verdict = classify_result(
        status_code,
        crashed=crashed,
        response_json=response_json,
        response_checks=request.response_checks,
        timed_out=timed_out,
      )
      stdout, stderr = active_sandbox.logs()
      stack_trace = None
      if verdict == Verdict.VULNERABLE:
        stack_trace = extract_stack_trace(stderr, response_body)
      duration_ms = int((time.monotonic() - started) * 1000)
      results.append(
        EvaluationResult(
          verdict=verdict,
          status_code=status_code,
          response_body=response_body,
          response_json=response_json,
          stdout=stdout,
          stderr=stderr,
          stack_trace=stack_trace,
          crashed=crashed,
          request=request,
          duration_ms=duration_ms,
        )
      )
  finally:
    active_sandbox.stop()
    shutil.rmtree(overlay_root, ignore_errors=True)

  return results


def evaluate_payload(
  source_files: dict[str, str],
  request: PayloadRequest,
  **kwargs: Any,
) -> EvaluationResult:
  """Evaluate a single payload (convenience wrapper)."""
  return evaluate_payloads(source_files, [request], **kwargs)[0]
