"""Shared LangChain Groq helpers."""

from __future__ import annotations

from typing import Any, TypeVar

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from pydantic import BaseModel

from agents.config import get_groq_api_key, get_model_name, get_reasoning_effort

T = TypeVar("T", bound=BaseModel)


def build_chat_model(*, temperature: float = 0) -> ChatGroq:
  api_key = get_groq_api_key()
  if not api_key:
    raise RuntimeError("GROQ_API_KEY is not set")
  return ChatGroq(
    model=get_model_name(),
    temperature=temperature,
    groq_api_key=api_key,
    reasoning_effort=get_reasoning_effort(),
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
  structured_llm = llm.with_structured_output(
    schema,
    method="json_schema",
    strict=True,
  )
  invoke_kwargs: dict[str, Any] = {}
  if config is not None:
    invoke_kwargs["config"] = config
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
