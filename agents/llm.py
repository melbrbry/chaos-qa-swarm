"""Shared LangChain Groq helpers."""

from __future__ import annotations

from typing import Any, TypeVar

from groq import BadRequestError
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from pydantic import BaseModel

from agents.config import get_groq_api_key, get_model_name, get_reasoning_effort

T = TypeVar("T", bound=BaseModel)


def _reasoning_fallbacks(primary: str) -> list[str]:
  order = ["high", "medium", "low"]
  if primary not in order:
    return [primary]
  start = order.index(primary)
  return order[start:]


def _is_json_validate_failed(exc: BadRequestError) -> bool:
  body = getattr(exc, "body", None)
  if isinstance(body, dict):
    error = body.get("error", {})
    if isinstance(error, dict) and error.get("code") == "json_validate_failed":
      return True
  return "json_validate_failed" in str(exc)


def build_chat_model(*, temperature: float = 0, reasoning_effort: str | None = None) -> ChatGroq:
  api_key = get_groq_api_key()
  if not api_key:
    raise RuntimeError("GROQ_API_KEY is not set")
  return ChatGroq(
    model=get_model_name(),
    temperature=temperature,
    groq_api_key=api_key,
    reasoning_effort=reasoning_effort or get_reasoning_effort(),
  )


def invoke_structured(
  llm: BaseChatModel,
  schema: type[T],
  *,
  system_prompt: str,
  human_prompt: str,
  config: Any = None,
) -> T:
  """Invoke LLM with Groq strict JSON schema structured output."""
  primary_effort = get_reasoning_effort()
  last_error: BadRequestError | None = None
  fallbacks = _reasoning_fallbacks(primary_effort)
  for index, effort in enumerate(fallbacks):
    if index == 0 and llm is not None:
      active_llm = llm
    else:
      active_llm = build_chat_model(reasoning_effort=effort)

    structured_llm = active_llm.with_structured_output(
      schema,
      method="json_schema",
      strict=True,
    )
    invoke_kwargs: dict[str, Any] = {}
    if config is not None:
      invoke_kwargs["config"] = config

    try:
      result = structured_llm.invoke(
        [
          SystemMessage(content=system_prompt),
          HumanMessage(content=human_prompt),
        ],
        **invoke_kwargs,
      )
      if isinstance(result, schema):
        return result
      return schema.model_validate(result)
    except BadRequestError as exc:
      last_error = exc
      if not _is_json_validate_failed(exc):
        raise

  assert last_error is not None
  raise last_error
