"""Unit tests for agent Pydantic models."""

import pytest

from agents.models import AttackPayload, AttackVector, ChaosStrategy, DeveloperPatch


def _sample_attack() -> AttackVector:
  return AttackVector(
    vulnerable_line_number=14,
    hypothesis="Division by zero when months_active is zero",
    payload=AttackPayload(
      path="/api/loyalty/score",
      body={"account_type": "legacy", "months_active": 0, "base_points": 100},
    ),
  )


def test_chaos_strategy_accepts_single_attack() -> None:
  strategy = ChaosStrategy(attacks=[_sample_attack()])
  assert len(strategy.attacks) == 1


def test_chaos_strategy_accepts_three_attacks() -> None:
  attacks = [_sample_attack() for _ in range(3)]
  strategy = ChaosStrategy(attacks=attacks)
  assert len(strategy.attacks) == 3


def test_chaos_strategy_rejects_empty_attacks() -> None:
  with pytest.raises(ValueError):
    ChaosStrategy(attacks=[])


def test_chaos_strategy_rejects_more_than_max(monkeypatch: pytest.MonkeyPatch) -> None:
  monkeypatch.setenv("CHAOS_ATTACK_MAX", "3")
  attacks = [_sample_attack() for _ in range(4)]
  with pytest.raises(ValueError, match="At most 3 attacks"):
    ChaosStrategy(attacks=attacks)


def test_developer_patch_model() -> None:
  patch = DeveloperPatch(
    thought_process="Guard division",
    patched_files={"target_app/routes/loyalty.py": "# patched"},
  )
  assert patch.patched_files["target_app/routes/loyalty.py"] == "# patched"


def test_attack_payload_parses_json_string_body() -> None:
  payload = AttackPayload.model_validate(
    {
      "path": "/api/loyalty/score",
      "body": '{"account_type": "legacy", "months_active": 0}',
    }
  )
  assert payload.body["account_type"] == "legacy"
  assert payload.method == "POST"


def test_attack_payload_json_schema_requires_all_properties() -> None:
  schema = AttackPayload.model_json_schema()
  properties = set(schema["properties"])
  required = set(schema["required"])
  assert properties == required


def test_chaos_strategy_json_schema_requires_all_properties() -> None:
  schema = ChaosStrategy.model_json_schema()
  properties = set(schema["properties"])
  required = set(schema["required"])
  assert properties == required


def test_developer_patch_parses_json_string_files() -> None:
  patch = DeveloperPatch.model_validate(
    {
      "thought_process": "fix",
      "patched_files": '{"target_app/routes/loyalty.py": "# patched"}',
    }
  )
  assert patch.patched_files["target_app/routes/loyalty.py"] == "# patched"
