"""Merge patched source files onto the baseline target_app tree."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BASELINE = REPO_ROOT / "target_app"
TARGET_APP_PREFIX = "target_app"


def _resolve_overlay_path(rel_path: str, overlay_root: Path) -> Path:
  normalized = Path(rel_path)
  if normalized.is_absolute():
    raise ValueError(f"Absolute paths are not allowed: {rel_path}")

  candidate = (overlay_root / normalized).resolve()
  overlay_root_resolved = overlay_root.resolve()
  if candidate == overlay_root_resolved or overlay_root_resolved not in candidate.parents:
    raise ValueError(f"Path escapes overlay root: {rel_path}")

  rel_parts = candidate.relative_to(overlay_root_resolved).parts
  if not rel_parts or rel_parts[0] != TARGET_APP_PREFIX:
    raise ValueError(f"Overlay paths must live under {TARGET_APP_PREFIX}/: {rel_path}")

  return candidate


def overlay_source(
  source_files: dict[str, str],
  baseline_root: Path | None = None,
) -> Path:
  """Copy baseline target_app to a temp dir and apply source_files overlays."""
  baseline = baseline_root or DEFAULT_BASELINE
  if not baseline.is_dir():
    raise FileNotFoundError(f"Baseline target_app not found: {baseline}")

  temp_root = Path(tempfile.mkdtemp(prefix="judge-overlay-"))
  shutil.copytree(baseline, temp_root / TARGET_APP_PREFIX)

  for rel_path, content in source_files.items():
    target_path = _resolve_overlay_path(rel_path, temp_root)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(content, encoding="utf-8")

  return temp_root
