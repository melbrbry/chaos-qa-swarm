"""Report aggregation endpoint."""

from fastapi import APIRouter

from target_app.models import ReportAggregateRequest, ReportAggregateResponse

router = APIRouter(tags=["report"])


@router.post("/report/aggregate", response_model=ReportAggregateResponse)
def report_aggregate(body: ReportAggregateRequest) -> ReportAggregateResponse:
  """Flatten nested groups and return aggregate metadata."""
  flat = [value for group in body.groups for value in group]
  first_value = body.groups[0][0]
  return ReportAggregateResponse(
    metric=body.metric,
    count=len(flat),
    first_value=first_value,
  )
