"""Load project .env into os.environ for CLI scripts."""

from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = REPO_ROOT / ".env"


def load_project_env(*, override: bool = False) -> None:
  """Load KEY=VALUE pairs from repo-root .env into os.environ."""
  if not ENV_PATH.is_file():
    return

  for raw_line in ENV_PATH.read_text(encoding="utf-8").splitlines():
    line = raw_line.strip()
    if not line or line.startswith("#") or "=" not in line:
      continue
    key, _, value = line.partition("=")
    key = key.strip()
    value = value.strip()
    if not key:
      continue
    if override or key not in os.environ:
      os.environ[key] = value
