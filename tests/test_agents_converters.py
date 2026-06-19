"""Unit tests for attack vector converters."""

from agents.converters import attack_to_request, strategy_to_requests
from agents.models import AttackPayload, AttackVector, ChaosStrategy


def test_attack_to_request() -> None:
  vector = AttackVector(
    vulnerable_line_number=10,
    hypothesis="KeyError on missing field",
    payload=AttackPayload(
      method="POST",
      path="/api/items/bulk",
      body={"items": []},
    ),
  )
  request = attack_to_request(vector)
  assert request.method == "POST"
  assert request.path == "/api/items/bulk"
  assert request.body == {"items": []}


def test_strategy_to_requests() -> None:
  strategy = ChaosStrategy(
    attacks=[
      AttackVector(
        vulnerable_line_number=1,
        hypothesis="first",
        payload=AttackPayload(path="/api/a", body={"x": 1}),
      ),
      AttackVector(
        vulnerable_line_number=2,
        hypothesis="second",
        payload=AttackPayload(path="/api/b", body={"y": 2}),
      ),
    ]
  )
  requests = strategy_to_requests(strategy)
  assert len(requests) == 2
  assert requests[0].path == "/api/a"
  assert requests[1].path == "/api/b"
