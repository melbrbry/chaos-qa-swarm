"""Graph configuration for swarm orchestration."""

from __future__ import annotations

import os

DEFAULT_MAX_PATCH_ITERATIONS = 3
DEFAULT_MAX_EXPLORATION_ROUNDS = 3


def get_max_patch_iterations() -> int:
  raw = os.environ.get("CHAOS_MAX_PATCH_ITERATIONS", str(DEFAULT_MAX_PATCH_ITERATIONS))
  try:
    value = int(raw)
  except ValueError as exc:
    raise ValueError(f"CHAOS_MAX_PATCH_ITERATIONS must be an integer, got {raw!r}") from exc
  if value < 1:
    raise ValueError("CHAOS_MAX_PATCH_ITERATIONS must be at least 1")
  return value


def get_max_exploration_rounds() -> int:
  raw = os.environ.get("CHAOS_MAX_EXPLORATION_ROUNDS", str(DEFAULT_MAX_EXPLORATION_ROUNDS))
  try:
    value = int(raw)
  except ValueError as exc:
    raise ValueError(f"CHAOS_MAX_EXPLORATION_ROUNDS must be an integer, got {raw!r}") from exc
  if value < 1:
    raise ValueError("CHAOS_MAX_EXPLORATION_ROUNDS must be at least 1")
  return value
