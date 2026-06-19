"""Convert agent models to Judge request types."""

from __future__ import annotations

from agents.models import AttackVector, ChaosStrategy
from judge.models import PayloadRequest


def attack_to_request(vector: AttackVector) -> PayloadRequest:
  """Map an attack vector to a Judge payload request."""
  return PayloadRequest(
    method=vector.payload.method,
    path=vector.payload.path,
    body=vector.payload.body,
  )


def strategy_to_requests(strategy: ChaosStrategy) -> list[PayloadRequest]:
  """Convert all attacks in a strategy to Judge requests."""
  return [attack_to_request(attack) for attack in strategy.attacks]
