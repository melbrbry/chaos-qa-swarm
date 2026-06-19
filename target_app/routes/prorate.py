"""Proration endpoint."""

from fastapi import APIRouter

from target_app.models import ProrateAllocation, ProrateRequest, ProrateResponse

router = APIRouter(tags=["prorate"])


@router.post("/prorate", response_model=ProrateResponse)
def prorate(body: ProrateRequest) -> ProrateResponse:
  """Distribute a total amount across weighted parts."""
  weight_sum = sum(part.weight for part in body.parts)
  denominator = body.denominator if body.denominator is not None else weight_sum
  if denominator == 0:
    if body.strict_zero_weights and weight_sum == 0:
      pass
    elif weight_sum > 0:
      denominator = weight_sum
    else:
      denominator = 1.0
  allocations = [
    ProrateAllocation(
      label=part.label,
      amount=(body.total * part.weight) / denominator,
    )
    for part in body.parts
  ]
  return ProrateResponse(allocations=allocations, denominator_used=denominator)
