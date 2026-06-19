"""User lookup endpoint."""

from fastapi import APIRouter

from target_app.models import UsersLookupRequest, UsersLookupResponse

router = APIRouter(tags=["users"])


@router.post("/users/lookup", response_model=UsersLookupResponse)
def users_lookup(body: UsersLookupRequest) -> UsersLookupResponse:
  """Return the first user matching the provided filter."""
  for user in body.users:
    if user[body.filter.field] == body.filter.value:
      return UsersLookupResponse(user=user)

  return UsersLookupResponse(user=body.users[0])
