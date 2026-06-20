"""Developer agent — generate minimal patches from crash reports."""

from __future__ import annotations

import json
from typing import Any

from agents.endpoints import load_endpoint_catalog
from agents.llm import build_chat_model, invoke_structured
from agents.models import DeveloperPatch, DeveloperPatchOutput, PatchRejectionContext
from agents.patch_validation import validate_patch_files
from agents.prompts import DEVELOPER_SYSTEM_PROMPT
from agents.source_bundle import build_source_context, load_source_files
from judge.models import PayloadRequest

__all__ = ["generate_patch", "validate_patch_files"]


def _format_source_files(source_files: dict[str, str]) -> str:
  if not source_files:
    return "(no prior patches — baseline source below)"
  sections = []
  for rel_path, content in sorted(source_files.items()):
    sections.append(f"## {rel_path}\n\n```python\n{content}\n```")
  return "\n\n".join(sections)


def _format_rejection_context(rejection: PatchRejectionContext) -> str:
  sections = [
    "## Previous Patch Rejected",
    "",
    f"Patch attempt {rejection.patch_attempt} of {rejection.max_patch_attempts}.",
    "",
    f"Prior thought_process: {rejection.rejected_patch.thought_process}",
    "",
    "### Rejected patched_files",
  ]
  for path, content in sorted(rejection.rejected_patch.patched_files.items()):
    sections.append(f"#### {path}\n\n```python\n{content}\n```")
  sections.extend(
    [
      "",
      f"### Verify failure ({rejection.failure_kind})",
      "",
      f"Request: {rejection.failing_result.request.method} {rejection.failing_result.request.path}",
      f"Verdict: {rejection.failing_result.verdict.value}",
      f"Status code: {rejection.failing_result.status_code}",
    ]
  )
  if rejection.expected_checks is not None:
    sections.append(
      f"Expected checks: ```json\n{json.dumps(rejection.expected_checks, indent=2)}\n```"
    )
  if rejection.actual_response is not None:
    sections.append(
      f"Actual response: ```json\n{json.dumps(rejection.actual_response, indent=2)}\n```"
    )
  if rejection.failing_result.stack_trace:
    sections.append(f"Stack trace:\n```\n{rejection.failing_result.stack_trace}\n```")
  elif rejection.failing_result.response_body:
    sections.append(f"Response body:\n```\n{rejection.failing_result.response_body}\n```")
  if rejection.other_failures:
    sections.extend(["", "### Other verify failures", ""])
    sections.extend(f"- {item}" for item in rejection.other_failures)
  sections.append("")
  sections.append("Revise the patch to fix this failure while handling the original attack below.")
  return "\n".join(sections)


def generate_patch(
  *,
  source_files: dict[str, str],
  failed_request: PayloadRequest,
  stack_trace: str,
  rejection_context: PatchRejectionContext | None = None,
  llm=None,
  config: Any = None,
) -> DeveloperPatch:
  """Generate a minimal patch for the crash described by payload and stack trace."""
  baseline_context = build_source_context()
  overlay_context = _format_source_files(source_files)
  catalog = load_endpoint_catalog()
  human_prompt = (
    "# Current Patched Files\n\n"
    f"{overlay_context}\n\n"
    "# Baseline Source\n\n"
    f"{baseline_context}\n\n"
  )
  if rejection_context is not None:
    human_prompt += f"{_format_rejection_context(rejection_context)}\n\n"
  human_prompt += (
    "## Failed Payload\n\n"
    f"```json\n{json.dumps(failed_request.model_dump(), indent=2)}\n```\n\n"
    "## Stack Trace\n\n"
    f"```\n{stack_trace}\n```\n\n"
    "## Endpoints\n\n"
    f"```json\n{catalog}\n```"
  )
  model = llm or build_chat_model()
  prompt = human_prompt
  last_error: Exception | None = None
  for attempt in range(2):
    try:
      output = invoke_structured(
        model,
        DeveloperPatchOutput,
        system_prompt=DEVELOPER_SYSTEM_PROMPT,
        human_prompt=prompt,
        config=config,
      )
      patch = DeveloperPatch.from_output(output)
      patch.patched_files = validate_patch_files(patch.patched_files)
      return patch
    except SyntaxError as exc:
      last_error = exc
      prompt = (
        f"{human_prompt}\n\n## Patch Rejected\n\n"
        f"The previous patched_files content was invalid Python: {exc}. "
        "Return syntactically valid source with real newlines and preserve required "
        "module exports such as `router`."
      )
  assert last_error is not None
  raise last_error


def merge_source_files(
  baseline_source_files: dict[str, str] | None,
  patch: DeveloperPatch,
) -> dict[str, str]:
  """Merge baseline source with validated patch files."""
  merged = dict(baseline_source_files or load_source_files())
  merged.update(patch.patched_files)
  return merged
