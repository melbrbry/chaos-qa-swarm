"""Pydantic models for agent structured outputs."""

from __future__ import annotations

import json
from typing import Annotated, Any

from pydantic import BaseModel, Field, WithJsonSchema, field_validator

from agents.config import get_attack_max


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

  method: str = "POST"
  path: str
  body: Annotated[
    dict[str, Any],
    Field(default_factory=dict),
    WithJsonSchema(
      {
        "type": "string",
        "description": "JSON-encoded HTTP request body object",
      }
    ),
  ]

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

  analysis_notes: str = ""
  attacks: list[AttackVector] = Field(min_length=1)

  @field_validator("attacks")
  @classmethod
  def validate_attack_count(cls, attacks: list[AttackVector]) -> list[AttackVector]:
    max_attacks = get_attack_max()
    if len(attacks) > max_attacks:
      raise ValueError(f"At most {max_attacks} attacks allowed, got {len(attacks)}")
    return attacks


class DeveloperPatch(BaseModel):
  """Patch proposal from the developer agent."""

  thought_process: str
  patched_files: Annotated[
    dict[str, str],
    WithJsonSchema(
      {
        "type": "string",
        "description": (
          "JSON object mapping target_app/ relative paths to full updated file contents"
        ),
      }
    ),
  ]

  @field_validator("patched_files", mode="before")
  @classmethod
  def parse_patched_files(cls, value: Any) -> dict[str, str]:
    parsed = _parse_json_object(value)
    return {str(key): str(content) for key, content in parsed.items()}
