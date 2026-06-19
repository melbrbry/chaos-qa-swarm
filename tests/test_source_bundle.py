"""Unit tests for source bundling."""

from agents.endpoints import load_endpoint_catalog
from agents.source_bundle import build_source_context, load_source_files


def test_load_source_files_includes_route_modules() -> None:
  files = load_source_files()
  assert "target_app/routes/loyalty.py" in files
  assert "target_app/routes/report.py" in files
  assert "target_app/main.py" in files


def test_build_source_context_includes_headers() -> None:
  context = build_source_context()
  assert "## target_app/routes/loyalty.py" in context
  assert "```python" in context


def test_endpoint_catalog_lists_all_routes() -> None:
  catalog = load_endpoint_catalog()
  assert "/api/loyalty/score" in catalog
  assert "/api/report/aggregate" in catalog
  assert "POST" in catalog
