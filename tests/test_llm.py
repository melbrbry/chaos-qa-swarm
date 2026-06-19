"""Unit tests for strict structured LLM invocation."""

from unittest.mock import MagicMock

from agents.llm import invoke_structured
from agents.models import AttackPayload, AttackVector, ChaosStrategy


def test_invoke_structured_uses_groq_strict_json_schema() -> None:
  strategy = ChaosStrategy(
    analysis_notes="notes",
    attacks=[
      AttackVector(
        vulnerable_line_number=1,
        hypothesis="test",
        payload=AttackPayload(path="/api/a", body={"x": 1}),
      )
    ],
  )
  structured_runnable = MagicMock()
  structured_runnable.invoke.return_value = strategy
  llm = MagicMock()
  llm.with_structured_output.return_value = structured_runnable

  result = invoke_structured(
    llm,
    ChaosStrategy,
    system_prompt="system",
    human_prompt="human",
  )

  llm.with_structured_output.assert_called_once_with(
    ChaosStrategy,
    method="json_schema",
    strict=True,
  )
  assert result == strategy
