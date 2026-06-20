#!/usr/bin/env python3
"""Run the Phase 4 LangGraph chaos QA swarm."""

from __future__ import annotations

import argparse
import sys

from graph.graph import build_graph
from graph.state import RunStatus, initial_state


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


def main() -> int:
  parser = argparse.ArgumentParser(description="Run chaos QA swarm LangGraph loop")
  args = parser.parse_args()

  app = build_graph()
  state = initial_state()
  final_state = app.invoke(state)

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

  if status == RunStatus.SUCCESS:
    return 0
  if status == RunStatus.CAPPED:
    return 0
  return 1


if __name__ == "__main__":
  sys.exit(main())
