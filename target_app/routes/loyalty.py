"""Loyalty score endpoint."""

from fastapi import APIRouter

from target_app.models import LoyaltyScoreRequest, LoyaltyScoreResponse

router = APIRouter(tags=["loyalty"])


@router.post("/loyalty/score", response_model=LoyaltyScoreResponse)
def loyalty_score(body: LoyaltyScoreRequest) -> LoyaltyScoreResponse:
  """Compute a loyalty score from account tenure and base points."""
  if body.account_type == "legacy" and body.months_active == 0:
    score = body.base_points / body.months_active
  else:
    score = body.base_points * body.months_active / 12
  return LoyaltyScoreResponse(score=score, account_type=body.account_type)
