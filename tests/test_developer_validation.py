"""Unit tests for developer patch path validation."""

import pytest

from agents.patch_validation import validate_patch_files


def test_validate_patch_files_accepts_target_app_paths() -> None:
  validated = validate_patch_files(
    {"target_app/routes/loyalty.py": "patched content"}
  )
  assert validated == {"target_app/routes/loyalty.py": "patched content"}


def test_validate_patch_files_rejects_outside_target_app() -> None:
  with pytest.raises(ValueError, match="target_app"):
    validate_patch_files({"judge/models.py": "bad"})


def test_validate_patch_files_rejects_path_traversal() -> None:
  with pytest.raises(ValueError, match="traversal"):
    validate_patch_files({"target_app/../etc/passwd": "bad"})


def test_validate_patch_files_rejects_absolute_paths() -> None:
  with pytest.raises(ValueError, match="Absolute"):
    validate_patch_files({"/target_app/routes/loyalty.py": "bad"})
