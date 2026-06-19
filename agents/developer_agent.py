"""Developer agent — generate minimal patches from crash reports."""

from __future__ import annotations

import json

from agents.endpoints import load_endpoint_catalog
from agents.llm import build_chat_model, invoke_structured
from agents.models import DeveloperPatch
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


def generate_patch(
  *,
  source_files: dict[str, str],
  failed_request: PayloadRequest,
  stack_trace: str,
  llm=None,
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
    "## Failed Payload\n\n"
    f"```json\n{json.dumps(failed_request.model_dump(), indent=2)}\n```\n\n"
    "## Stack Trace\n\n"
    f"```\n{stack_trace}\n```\n\n"
    "## Endpoints\n\n"
    f"```json\n{catalog}\n```"
  )
  model = llm or build_chat_model()
  patch = invoke_structured(
    model,
    DeveloperPatch,
    system_prompt=DEVELOPER_SYSTEM_PROMPT,
    human_prompt=human_prompt,
  )
  patch.patched_files = validate_patch_files(patch.patched_files)
  return patch


def merge_source_files(
  baseline_source_files: dict[str, str] | None,
  patch: DeveloperPatch,
) -> dict[str, str]:
  """Merge baseline source with validated patch files."""
  merged = dict(baseline_source_files or load_source_files())
  merged.update(patch.patched_files)
  return merged
