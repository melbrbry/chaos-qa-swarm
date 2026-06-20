"""Unit tests for developer patch path validation."""

import pytest

from agents.patch_validation import normalize_source_content, validate_patch_files


def test_validate_patch_files_accepts_target_app_paths() -> None:
  validated = validate_patch_files(
    {"target_app/routes/loyalty.py": "router = None\n"}
  )
  assert validated == {"target_app/routes/loyalty.py": "router = None\n"}


def test_validate_patch_files_rejects_outside_target_app() -> None:
  with pytest.raises(ValueError, match="target_app"):
    validate_patch_files({"judge/models.py": "bad"})


def test_validate_patch_files_rejects_path_traversal() -> None:
  with pytest.raises(ValueError, match="traversal"):
    validate_patch_files({"target_app/../etc/passwd": "bad"})


def test_validate_patch_files_rejects_absolute_paths() -> None:
  with pytest.raises(ValueError, match="Absolute"):
    validate_patch_files({"/target_app/routes/loyalty.py": "bad"})


def test_normalize_source_content_unescapes_literal_newlines() -> None:
  raw = "def f():\\n    return 1\\n"
  assert normalize_source_content(raw) == "def f():\n    return 1\n"


def test_validate_patch_files_rejects_invalid_python() -> None:
  with pytest.raises(SyntaxError):
    validate_patch_files({"target_app/routes/items.py": "def broken(: pass"})
