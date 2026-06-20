"""LangGraph state for the chaos QA swarm loop."""

from __future__ import annotations

from enum import Enum
from typing import TypedDict

from agents.models import ChaosStrategy, DeveloperPatch, PatchRejectionContext
from judge.models import EvaluationResult, PayloadRequest


class RunStatus(str, Enum):
  RUNNING = "running"
  SUCCESS = "success"
  STUCK = "stuck"
  CAPPED = "capped"


class SwarmState(TypedDict, total=False):
  source_files: dict[str, str]
  candidate_source_files: dict[str, str]
  strategy: ChaosStrategy | None
  attack_requests: list[PayloadRequest]
  probe_results: list[EvaluationResult]
  verify_results: list[EvaluationResult]
  active_failure: EvaluationResult | None
  original_failure: EvaluationResult | None
  last_patch: DeveloperPatch | None
  rejection_context: PatchRejectionContext | None
  patch_iteration: int
  exploration_round: int
  status: RunStatus
  message: str


def initial_state() -> SwarmState:
  return SwarmState(
    source_files={},
    candidate_source_files={},
    strategy=None,
    attack_requests=[],
    probe_results=[],
    verify_results=[],
    active_failure=None,
    original_failure=None,
    last_patch=None,
    rejection_context=None,
    patch_iteration=0,
    exploration_round=0,
    status=RunStatus.RUNNING,
    message="",
  )
