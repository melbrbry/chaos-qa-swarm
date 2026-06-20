"""Conditional routing for the swarm LangGraph."""

from __future__ import annotations

from typing import Literal

from graph.config import get_max_patch_iterations
from graph.state import RunStatus, SwarmState

RouteAfterProbe = Literal["developer", "end"]
RouteAfterVerify = Literal["developer", "chaos", "end"]


def route_after_probe(state: SwarmState) -> RouteAfterProbe:
  if state.get("active_failure") is None:
    return "end"
  return "developer"


def route_after_verify(state: SwarmState) -> RouteAfterVerify:
  status = state.get("status", RunStatus.RUNNING)
  if status == RunStatus.STUCK:
    return "end"
  if status == RunStatus.CAPPED:
    return "end"
  if state.get("rejection_context") is not None:
    if state.get("patch_iteration", 0) >= get_max_patch_iterations():
      return "end"
    return "developer"
  return "chaos"
