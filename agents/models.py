"""Pydantic models for agent structured outputs."""

from __future__ import annotations

import json
from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field, WithJsonSchema, field_validator, model_validator

from agents.config import get_attack_max
from agents.patch_validation import normalize_source_content
from judge.models import EvaluationResult


def _parse_json_object(value: Any) -> dict[str, Any]:
  if isinstance(value, str):
    if not value.strip():
      return {}
    parsed = json.loads(value)
    if not isinstance(parsed, dict):
      raise ValueError("Expected a JSON object")
    return parsed
  if isinstance(value, dict):
    return value
  raise ValueError("Expected a JSON object or JSON string")


class AttackPayload(BaseModel):
  """HTTP payload targeting a specific API route."""

  method: str
  path: str
  body: Annotated[
    dict[str, Any],
    Field(...),
    WithJsonSchema(
      {
        "type": "string",
        "description": "JSON-encoded HTTP request body object",
      }
    ),
  ]

  @model_validator(mode="before")
  @classmethod
  def apply_defaults(cls, data: Any) -> Any:
    if isinstance(data, dict):
      if not data.get("method"):
        data = {**data, "method": "POST"}
      if "body" not in data or data["body"] is None:
        data = {**data, "body": {}}
    return data

  @field_validator("body", mode="before")
  @classmethod
  def parse_body(cls, value: Any) -> dict[str, Any]:
    return _parse_json_object(value)


class AttackVector(BaseModel):
  """Single hypothesized attack with reasoning before payload."""

  vulnerable_line_number: int
  hypothesis: str
  payload: AttackPayload


class ChaosStrategy(BaseModel):
  """Collection of high-confidence attacks from white-box analysis."""

  analysis_notes: str
  attacks: list[AttackVector] = Field(min_length=1)

  @model_validator(mode="before")
  @classmethod
  def apply_defaults(cls, data: Any) -> Any:
    if isinstance(data, dict) and "analysis_notes" not in data:
      data = {**data, "analysis_notes": ""}
    return data

  @field_validator("attacks")
  @classmethod
  def validate_attack_count(cls, attacks: list[AttackVector]) -> list[AttackVector]:
    max_attacks = get_attack_max()
    if len(attacks) > max_attacks:
      raise ValueError(f"At most {max_attacks} attacks allowed, got {len(attacks)}")
    return attacks


class PatchedFileEntry(BaseModel):
  """Single patched file returned by the developer LLM."""

  path: str
  content: str

  @field_validator("content", mode="before")
  @classmethod
  def normalize_content(cls, value: Any) -> str:
    return normalize_source_content(str(value))


class DeveloperPatchOutput(BaseModel):
  """Structured LLM output for developer patches (Groq strict-safe)."""

  thought_process: str
  patched_files: list[PatchedFileEntry] = Field(min_length=1)


class DeveloperPatch(BaseModel):
  """Patch proposal from the developer agent."""

  thought_process: str
  patched_files: dict[str, str]

  @classmethod
  def from_output(cls, output: DeveloperPatchOutput) -> DeveloperPatch:
    return cls(
      thought_process=output.thought_process,
      patched_files={entry.path: entry.content for entry in output.patched_files},
    )

  @field_validator("patched_files", mode="before")
  @classmethod
  def parse_patched_files(cls, value: Any) -> dict[str, str]:
    if isinstance(value, list):
      parsed: dict[str, str] = {}
      for entry in value:
        if isinstance(entry, dict):
          parsed[str(entry["path"])] = normalize_source_content(str(entry["content"]))
        else:
          parsed[str(entry.path)] = entry.content
      return parsed
    parsed = _parse_json_object(value)
    return {
      str(key): normalize_source_content(str(content))
      for key, content in parsed.items()
    }


class PatchRejectionContext(BaseModel):
  """Feedback when a candidate patch fails judge_verify."""

  patch_attempt: int
  max_patch_attempts: int
  rejected_patch: DeveloperPatch
  candidate_files: list[str]
  failure_kind: Literal["attack", "baseline", "startup"]
  failing_result: EvaluationResult
  expected_checks: dict[str, Any] | None = None
  actual_response: dict[str, Any] | None = None
  other_failures: list[str] = Field(default_factory=list)
