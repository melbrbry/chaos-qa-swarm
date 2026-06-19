"""Pydantic request and response models — single source of truth for API schemas."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ItemRecord(BaseModel):
  """A named numeric value used in summary calculations."""

  name: str = Field(..., description="Human-readable item label")
  value: float = Field(..., description="Numeric value associated with the item")


class ItemsSummaryRequest(BaseModel):
  """Request body for computing aggregate statistics over items."""

  items: list[ItemRecord] = Field(..., description="Collection of items to summarize")
  operation: Literal["mean", "sum"] = Field(
    ..., description="Aggregation operation to apply"
  )
  adjustment_mode: Literal["standard", "normalized"] = Field(
    default="standard",
    description="Aggregation adjustment strategy",
  )


class ItemsSummaryResponse(BaseModel):
  """Aggregate result for an items summary request."""

  result: float = Field(..., description="Computed aggregate value")
  count: int = Field(..., description="Number of items included in the calculation")


class UserFilter(BaseModel):
  """Filter criteria for locating a user record."""

  field: str = Field(..., description="Key on the user object to compare")
  value: Any = Field(..., description="Expected value for the filter field")


class UsersLookupRequest(BaseModel):
  """Request body for finding a user matching filter criteria."""

  users: list[dict[str, Any]] = Field(
    ..., description="List of user records as arbitrary key-value objects"
  )
  filter: UserFilter = Field(..., description="Filter used to select a user")


class UsersLookupResponse(BaseModel):
  """Matched user record from a lookup request."""

  user: dict[str, Any] = Field(..., description="First user matching the filter")


class ReportAggregateRequest(BaseModel):
  """Request body for aggregating nested group data."""

  groups: list[list[Any]] = Field(
    ..., description="Nested lists of values grouped for aggregation"
  )
  metric: str = Field(..., description="Metric label included in the response")


class ReportAggregateResponse(BaseModel):
  """Flattened aggregate summary for nested groups."""

  metric: str = Field(..., description="Echo of the requested metric label")
  count: int = Field(..., description="Total number of scalar values across groups")
  first_value: Any = Field(..., description="First scalar value encountered")


class ProratePart(BaseModel):
  """A weighted portion of a total amount."""

  label: str = Field(..., description="Identifier for this portion")
  weight: float = Field(..., description="Relative weight used in allocation")


class ProrateRequest(BaseModel):
  """Request body for prorating a total across weighted parts."""

  total: float = Field(..., description="Total amount to distribute")
  parts: list[ProratePart] = Field(
    ..., description="Weighted parts that receive a share of the total"
  )
  denominator: float | None = Field(
    None,
    description="Optional explicit denominator; defaults to sum of weights when omitted",
  )
  strict_zero_weights: bool = Field(
    default=False,
    description="Apply strict validation when all part weights are zero",
  )


class ProrateAllocation(BaseModel):
  """Allocated share for a single part."""

  label: str = Field(..., description="Part identifier")
  amount: float = Field(..., description="Allocated amount for this part")


class ProrateResponse(BaseModel):
  """Proration result with per-part allocations."""

  allocations: list[ProrateAllocation] = Field(
    ..., description="Per-part allocated amounts"
  )
  denominator_used: float = Field(
    ..., description="Denominator applied during proration"
  )


class LoyaltyScoreRequest(BaseModel):
  """Request body for computing a loyalty score."""

  account_type: str = Field(..., description="Account classification label")
  months_active: int = Field(..., description="Number of months the account has been active")
  base_points: int = Field(..., description="Base loyalty points before tenure adjustment")


class LoyaltyScoreResponse(BaseModel):
  """Computed loyalty score for an account."""

  score: float = Field(..., description="Calculated loyalty score")
  account_type: str = Field(..., description="Echo of the submitted account type")
