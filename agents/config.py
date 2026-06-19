"""Environment configuration for agents."""

from __future__ import annotations

import os

DEFAULT_MODEL = "openai/gpt-oss-120b"
DEFAULT_ATTACK_MAX = 3
DEFAULT_REASONING_EFFORT = "high"


def get_groq_api_key() -> str | None:
  return os.environ.get("GROQ_API_KEY")


def get_model_name() -> str:
  return os.environ.get("CHAOS_QA_MODEL", DEFAULT_MODEL)


def get_reasoning_effort() -> str:
  return os.environ.get("CHAOS_REASONING_EFFORT", DEFAULT_REASONING_EFFORT)


def get_attack_max() -> int:
  raw = os.environ.get("CHAOS_ATTACK_MAX", str(DEFAULT_ATTACK_MAX))
  try:
    value = int(raw)
  except ValueError as exc:
    raise ValueError(f"CHAOS_ATTACK_MAX must be an integer, got {raw!r}") from exc
  if value < 1:
    raise ValueError("CHAOS_ATTACK_MAX must be at least 1")
  return value
