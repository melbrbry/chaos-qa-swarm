"""White-box chaos agent — semantic attack generation."""

from __future__ import annotations

from pathlib import Path

from agents.config import get_attack_max
from agents.converters import strategy_to_requests
from agents.endpoints import load_endpoint_catalog
from agents.llm import build_chat_model, invoke_structured
from agents.models import ChaosStrategy
from agents.prompts import CHAOS_SYSTEM_PROMPT
from agents.source_bundle import (
  build_source_context,
  build_source_context_from_files,
  load_source_files,
)
from judge.executor import evaluate_payloads
from judge.models import EvaluationResult


def generate_attacks(
  source_root: Path | None = None,
  *,
  source_files: dict[str, str] | None = None,
  llm=None,
) -> ChaosStrategy:
  """Analyze source code and return 1 to N high-confidence attacks."""
  if source_files:
    merged = dict(load_source_files())
    merged.update(source_files)
    bundle = build_source_context_from_files(merged)
  else:
    bundle = build_source_context(source_root)
  catalog = load_endpoint_catalog()
  human_prompt = f"# Source Code\n\n{bundle}\n\n## Endpoints\n\n```json\n{catalog}\n```"
  system_prompt = CHAOS_SYSTEM_PROMPT.format(attack_max=get_attack_max())
  model = llm or build_chat_model()
  return invoke_structured(
    model,
    ChaosStrategy,
    system_prompt=system_prompt,
    human_prompt=human_prompt,
  )


def probe_attacks(
  strategy: ChaosStrategy,
  source_files: dict[str, str] | None = None,
) -> list[EvaluationResult]:
  """Run all attacks from a strategy through the Judge."""
  return evaluate_payloads(source_files or {}, strategy_to_requests(strategy))
