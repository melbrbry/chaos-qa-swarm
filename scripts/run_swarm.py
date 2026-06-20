#!/usr/bin/env python3
"""Run the Phase 4 LangGraph chaos QA swarm."""

from __future__ import annotations

from agents.env_loader import load_project_env

load_project_env()

from observability.langfuse_tracing import ensure_tracing_ready

tracing_enabled = ensure_tracing_ready()

import argparse
import os
import sys

from graph.graph import build_graph
from graph.state import RunStatus, initial_state
from observability.langfuse_tracing import (
  flush_tracing,
  get_trace_url_hint,
  graph_invoke_config,
  new_session_id,
  observe,
  update_observation_metadata,
)


def _print_results(label: str, results) -> None:
  if not results:
    return
  print(f"\n{label}")
  print(f"{'Verdict':<16} {'Status':<8} Path")
  print("-" * 60)
  for result in results:
    print(
      f"{result.verdict.value:<16} {str(result.status_code):<8} "
      f"{result.request.method} {result.request.path}"
    )


@observe(name="chaos-qa-swarm-run")
def main() -> int:
  parser = argparse.ArgumentParser(description="Run chaos QA swarm LangGraph loop")
  parser.parse_args()

  session_id = new_session_id()
  app = build_graph(enable_tracing=tracing_enabled)
  state = initial_state()
  invoke_config = graph_invoke_config(
    session_id=session_id,
    tags=["chaos-qa-swarm", "phase-5"],
    metadata={"JUDGE_SANDBOX": os.environ.get("JUDGE_SANDBOX", "docker")},
    callbacks=not tracing_enabled,
  )
  final_state = app.invoke(state, config=invoke_config)

  strategy = final_state.get("strategy")
  if strategy is not None:
    print(f"Latest strategy: {len(strategy.attacks)} attack(s)")
    if strategy.analysis_notes:
      print(f"Analysis: {strategy.analysis_notes}")

  _print_results("Probe results", final_state.get("probe_results"))
  _print_results("Verify results", final_state.get("verify_results"))

  source_files = final_state.get("source_files") or {}
  if source_files:
    print(f"\nAccepted patch files: {sorted(source_files.keys())}")

  status = final_state.get("status", RunStatus.RUNNING)
  print(f"\nFinal status: {status.value}")
  print(f"Message: {final_state.get('message', '')}")
  print(f"Exploration rounds: {final_state.get('exploration_round', 0)}")
  print(f"Patch iterations (last inner loop): {final_state.get('patch_iteration', 0)}")

  update_observation_metadata(
    {
      "final_status": status.value,
      "exploration_round": final_state.get("exploration_round", 0),
      "patch_iteration": final_state.get("patch_iteration", 0),
      "JUDGE_SANDBOX": os.environ.get("JUDGE_SANDBOX", "docker"),
    }
  )

  trace_hint = get_trace_url_hint()
  if trace_hint:
    print(f"\nLangfuse trace: {trace_hint} (filter tag: chaos-qa-swarm, session: {session_id})")

  flush_tracing()

  if status == RunStatus.SUCCESS:
    return 0
  if status == RunStatus.CAPPED:
    return 0
  return 1


if __name__ == "__main__":
  sys.exit(main())
