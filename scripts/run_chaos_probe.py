#!/usr/bin/env python3
"""Run chaos agent attacks through the Judge (optional auto-patch)."""

from __future__ import annotations

import argparse
import sys

from agents.env_loader import load_project_env
from agents.chaos_agent import generate_attacks, probe_attacks
from agents.developer_agent import generate_patch, merge_source_files
from judge.executor import evaluate_payload
from judge.models import Verdict


def main() -> int:
  parser = argparse.ArgumentParser(description="White-box chaos probe")
  parser.add_argument(
    "--patch",
    action="store_true",
    help="Generate a developer patch for the first vulnerable result and re-evaluate",
  )
  args = parser.parse_args()

  load_project_env()

  print("Generating attacks from source...")
  strategy = generate_attacks()
  print(f"Analysis: {strategy.analysis_notes or '(none)'}")
  print(f"Attacks: {len(strategy.attacks)}")

  for index, attack in enumerate(strategy.attacks, start=1):
    print(f"\n[{index}] line {attack.vulnerable_line_number}: {attack.hypothesis}")
    print(f"    {attack.payload.method} {attack.payload.path}")
    print(f"    body={attack.payload.body}")

  print("\nRunning Judge...")
  results = probe_attacks(strategy)

  print(f"\n{'#':<3} {'Verdict':<16} {'Status':<8} Path")
  print("-" * 70)
  for index, result in enumerate(results, start=1):
    attack = strategy.attacks[index - 1]
    print(
      f"{index:<3} {result.verdict.value:<16} {str(result.status_code):<8} "
      f"{result.request.path} — {attack.hypothesis[:60]}"
    )

  if not args.patch:
    vulnerable = [r for r in results if r.verdict in (Verdict.VULNERABLE, Verdict.LOGIC_ERROR)]
    return 0 if vulnerable else 1

  failure = next(
    (r for r in results if r.verdict in (Verdict.VULNERABLE, Verdict.LOGIC_ERROR)),
    None,
  )
  if failure is None:
    print("\nNo vulnerable results to patch.")
    return 0

  print("\nGenerating developer patch...")
  patch = generate_patch(
    source_files={},
    failed_request=failure.request,
    stack_trace=failure.stack_trace or failure.response_body,
  )
  merged = merge_source_files({}, patch)
  print(f"Patch files: {list(patch.patched_files.keys())}")

  print("\nRe-evaluating failed payload against patched source...")
  reeval = evaluate_payload(merged, failure.request)
  print(f"Re-eval verdict: {reeval.verdict.value} (status {reeval.status_code})")
  return 0 if reeval.verdict == Verdict.ROBUST else 1


if __name__ == "__main__":
  sys.exit(main())
