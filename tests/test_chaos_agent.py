"""Chaos agent tests with mocked LLM."""

from unittest.mock import patch

from agents.chaos_agent import generate_attacks, probe_attacks
from agents.models import AttackPayload, AttackVector, ChaosStrategy
from judge.models import EvaluationResult, PayloadRequest, Verdict


class FakeStructuredLLM:
  def __init__(self, result):
    self._result = result

  def with_structured_output(self, schema, **kwargs):
    return self

  def invoke(self, messages):
    return self._result


def _sample_strategy() -> ChaosStrategy:
  return ChaosStrategy(
    analysis_notes="Found loyalty trap",
    attacks=[
      AttackVector(
        vulnerable_line_number=14,
        hypothesis="Zero months_active divides base_points",
        payload=AttackPayload(
          path="/api/loyalty/score",
          body={"account_type": "legacy", "months_active": 0, "base_points": 100},
        ),
      )
    ],
  )


def test_generate_attacks_with_mock_llm() -> None:
  strategy = _sample_strategy()
  llm = FakeStructuredLLM(strategy)
  result = generate_attacks(llm=llm)
  assert result.analysis_notes == "Found loyalty trap"
  assert len(result.attacks) == 1
  assert result.attacks[0].payload.path == "/api/loyalty/score"


def test_probe_attacks_calls_judge() -> None:
  strategy = _sample_strategy()
  mock_result = EvaluationResult(
    verdict=Verdict.VULNERABLE,
    status_code=500,
    request=PayloadRequest(path="/api/loyalty/score", body={}),
  )
  with patch("agents.chaos_agent.evaluate_payloads", return_value=[mock_result]) as mocked:
    results = probe_attacks(strategy)
  mocked.assert_called_once()
  assert len(results) == 1
  assert results[0].verdict == Verdict.VULNERABLE
