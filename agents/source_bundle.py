"""Load and format target_app source for LLM context."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE_ROOT = REPO_ROOT / "target_app"


def load_source_files(source_root: Path | None = None) -> dict[str, str]:
  """Return all Python files under target_app as relative path -> content."""
  root = source_root or DEFAULT_SOURCE_ROOT
  if not root.is_dir():
    raise FileNotFoundError(f"Source root not found: {root}")

  files: dict[str, str] = {}
  for path in sorted(root.rglob("*.py")):
    rel_path = path.relative_to(REPO_ROOT).as_posix()
    files[rel_path] = path.read_text(encoding="utf-8")
  return files


def build_source_context(source_root: Path | None = None) -> str:
  """Format source files with path headers for LLM consumption."""
  files = load_source_files(source_root)
  return build_source_context_from_files(files)


def build_source_context_from_files(source_files: dict[str, str]) -> str:
  """Format an overlay or explicit file map for LLM consumption."""
  sections = []
  for rel_path, content in sorted(source_files.items()):
    sections.append(f"## {rel_path}\n\n```python\n{content}\n```")
  return "\n\n".join(sections)
