"""Unit tests for source overlay behavior."""

from pathlib import Path

import pytest

from judge.source_overlay import overlay_source

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_partial_overlay_replaces_one_file() -> None:
  overlay_root = overlay_source(
    {"target_app/routes/loyalty.py": '"""patched"""\n'},
    baseline_root=REPO_ROOT / "target_app",
  )
  try:
    loyalty_path = overlay_root / "target_app" / "routes" / "loyalty.py"
    items_path = overlay_root / "target_app" / "routes" / "items.py"
    assert loyalty_path.read_text(encoding="utf-8") == '"""patched"""\n'
    assert items_path.exists()
  finally:
    import shutil

    shutil.rmtree(overlay_root, ignore_errors=True)


def test_path_traversal_rejected() -> None:
  with pytest.raises(ValueError, match="escapes overlay root|must live under target_app"):
    overlay_source({"../etc/passwd": "nope"})


def test_empty_overlay_copies_baseline() -> None:
  overlay_root = overlay_source({}, baseline_root=REPO_ROOT / "target_app")
  try:
    assert (overlay_root / "target_app" / "main.py").exists()
  finally:
    import shutil

    shutil.rmtree(overlay_root, ignore_errors=True)
