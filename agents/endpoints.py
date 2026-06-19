"""Load endpoint routing catalog from schema exports."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ENDPOINTS_DIR = REPO_ROOT / "schemas" / "endpoints"


def load_endpoint_catalog(endpoints_dir: Path | None = None) -> str:
  """Return compact JSON list of method/path/summary for each endpoint."""
  directory = endpoints_dir or ENDPOINTS_DIR
  entries = []
  for path in sorted(directory.glob("*.json")):
    payload = json.loads(path.read_text(encoding="utf-8"))
    endpoint = payload.get("endpoint", {})
    entries.append(
      {
        "method": endpoint.get("method"),
        "path": endpoint.get("path"),
        "summary": endpoint.get("summary"),
      }
    )
  return json.dumps(entries, indent=2, sort_keys=True)
