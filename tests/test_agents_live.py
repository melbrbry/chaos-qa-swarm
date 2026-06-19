"""Optional live Groq agent tests."""

import os

import pytest

from agents.chaos_agent import generate_attacks, probe_attacks


@pytest.mark.llm
def test_live_generate_attacks_and_probe() -> None:
  if not os.environ.get("GROQ_API_KEY"):
    pytest.skip("GROQ_API_KEY not set")

  strategy = generate_attacks()
  assert 1 <= len(strategy.attacks) <= 3
  for attack in strategy.attacks:
    assert attack.hypothesis
    assert attack.payload.path.startswith("/api/")

  results = probe_attacks(strategy)
  assert len(results) == len(strategy.attacks)
