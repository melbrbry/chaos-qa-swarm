"""Pydantic models for Judge requests and results."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Verdict(str, Enum):
  """Classification of a payload evaluation outcome."""

  ROBUST = "robust"
  VULNERABLE = "vulnerable"
  LOGIC_ERROR = "logic_error"
  INVALID_REQUEST = "invalid_request"


class PayloadRequest(BaseModel):
  """HTTP request to execute against the sandboxed target app."""

  method: str = "POST"
  path: str
  body: dict[str, Any] = Field(default_factory=dict)
  response_checks: dict[str, Any] | None = None


class EvaluationResult(BaseModel):
  """Outcome of evaluating a single payload in the sandbox."""

  verdict: Verdict
  status_code: int | None = None
  response_body: str = ""
  response_json: dict[str, Any] | None = None
  stdout: str = ""
  stderr: str = ""
  stack_trace: str | None = None
  crashed: bool = False
  request: PayloadRequest
  duration_ms: int = 0
