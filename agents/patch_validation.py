"""Validate developer patch file paths."""

from __future__ import annotations

from pathlib import Path


TARGET_APP_PREFIX = "target_app"


def normalize_source_content(content: str) -> str:
  """Convert LLM-escaped newlines into real source lines when needed."""
  if "\\n" in content and content.count("\\n") > content.count("\n"):
    return (
      content.replace("\\r\\n", "\n")
      .replace("\\n", "\n")
      .replace("\\t", "\t")
      .replace('\\"', '"')
    )
  return content


def validate_patch_files(patched_files: dict[str, str]) -> dict[str, str]:
  """Reject patch paths outside target_app/ and invalid Python syntax."""
  validated: dict[str, str] = {}
  for rel_path, content in patched_files.items():
    normalized = Path(rel_path)
    if normalized.is_absolute():
      raise ValueError(f"Absolute paths are not allowed: {rel_path}")
    parts = normalized.as_posix().split("/")
    if not parts or parts[0] != TARGET_APP_PREFIX:
      raise ValueError(f"Patch paths must live under {TARGET_APP_PREFIX}/: {rel_path}")
    if ".." in parts:
      raise ValueError(f"Path traversal is not allowed: {rel_path}")
    posix_path = normalized.as_posix()
    if posix_path.endswith(".py"):
      compile(content, posix_path, "exec")
    validated[posix_path] = content
  return validated
