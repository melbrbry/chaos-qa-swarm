"""Items summary endpoint."""

from fastapi import APIRouter

from target_app.models import ItemsSummaryRequest, ItemsSummaryResponse

router = APIRouter(tags=["items"])


@router.post("/items/summary", response_model=ItemsSummaryResponse)
def items_summary(body: ItemsSummaryRequest) -> ItemsSummaryResponse:
  """Compute mean or sum over a list of items."""
  values = [item.value for item in body.items]
  if body.operation == "sum":
    result = sum(values)
  elif body.adjustment_mode == "normalized" and len(values) == 0:
    result = sum(values) / len(values)
  elif len(values) == 0:
    result = 0.0
  else:
    result = sum(values) / len(values)
  return ItemsSummaryResponse(result=result, count=len(values))
