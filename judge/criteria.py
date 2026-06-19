"""Verdict classification and stack trace extraction."""

from __future__ import annotations

import json
import re
from typing import Any

from judge.models import Verdict

TRACEBACK_START = re.compile(r"^Traceback \(most recent call last\):", re.MULTILINE)


def check_response(
  response_json: dict[str, Any] | None,
  response_checks: dict[str, Any] | None,
) -> bool:
  """Return True when all response_checks pass against response_json."""
  if not response_checks:
    return True
  if response_json is None:
    return False
  for key, expected in response_checks.items():
    if response_json.get(key) != expected:
      return False
  return True


def classify_result(
  status_code: int | None,
  *,
  crashed: bool,
  response_json: dict[str, Any] | None,
  response_checks: dict[str, Any] | None,
  timed_out: bool = False,
) -> Verdict:
  """Classify an HTTP outcome into a verdict."""
  if crashed:
    return Verdict.VULNERABLE
  if timed_out or status_code is None:
    return Verdict.INVALID_REQUEST if timed_out else Verdict.VULNERABLE
  if status_code >= 500:
    return Verdict.VULNERABLE
  if status_code in (400, 422):
    return Verdict.ROBUST
  if status_code == 404:
    return Verdict.INVALID_REQUEST
  if status_code == 200:
    if response_checks and not check_response(response_json, response_checks):
      return Verdict.LOGIC_ERROR
    return Verdict.ROBUST
  return Verdict.ROBUST


def extract_stack_trace(
  stderr: str,
  response_body: str = "",
) -> str | None:
  """Extract a stack trace from sandbox logs or a 500 response body."""
  if stderr:
    match = TRACEBACK_START.search(stderr)
    if match:
      return stderr[match.start() :].strip()

  if response_body:
    try:
      payload = json.loads(response_body)
    except json.JSONDecodeError:
      payload = None
    if isinstance(payload, dict):
      detail = payload.get("detail")
      if isinstance(detail, str) and detail.strip():
        return detail.strip()

  combined = "\n".join(part for part in (stderr, response_body) if part).strip()
  if not combined:
    return None
  lines = combined.splitlines()
  return "\n".join(lines[-50:]).strip() or None
