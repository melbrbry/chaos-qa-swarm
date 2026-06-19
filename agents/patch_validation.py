"""Validate developer patch file paths."""

from __future__ import annotations

from pathlib import Path

TARGET_APP_PREFIX = "target_app"


def validate_patch_files(patched_files: dict[str, str]) -> dict[str, str]:
  """Reject patch paths outside target_app/."""
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
    validated[normalized.as_posix()] = content
  return validated
