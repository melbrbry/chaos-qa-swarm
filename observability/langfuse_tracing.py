"""Langfuse tracing helpers for the chaos QA swarm."""

from __future__ import annotations

import os
import uuid
from typing import Any

DEFAULT_LANGFUSE_HOST = "https://cloud.langfuse.com"

_handler = None


def is_tracing_enabled() -> bool:
  """Return True when Langfuse credentials are configured and not explicitly disabled."""
  if os.environ.get("LANGFUSE_ENABLED", "1").strip().lower() in {"0", "false", "no"}:
    return False
  return bool(os.environ.get("LANGFUSE_PUBLIC_KEY") and os.environ.get("LANGFUSE_SECRET_KEY"))


def _ensure_langfuse_env() -> None:
  os.environ.setdefault("LANGFUSE_HOST", DEFAULT_LANGFUSE_HOST)


def get_langfuse_handler():
  """Return a singleton LangChain CallbackHandler when tracing is enabled."""
  global _handler
  if not is_tracing_enabled():
    return None
  if _handler is None:
    _ensure_langfuse_env()
    from langfuse.langchain import CallbackHandler

    _handler = CallbackHandler()
  return _handler


def graph_invoke_config(
  *,
  session_id: str | None = None,
  tags: list[str] | None = None,
  metadata: dict[str, Any] | None = None,
  callbacks: bool = True,
) -> dict[str, Any]:
  """Build LangGraph invoke config with optional Langfuse callbacks."""
  config: dict[str, Any] = {}
  invoke_metadata = dict(metadata or {})
  if session_id:
    invoke_metadata["langfuse_session_id"] = session_id
  if tags:
    invoke_metadata["langfuse_tags"] = tags
  if invoke_metadata:
    config["metadata"] = invoke_metadata

  if callbacks:
    handler = get_langfuse_handler()
    if handler is not None:
      config["callbacks"] = [handler]
  return config


def flush_tracing() -> None:
  """Flush pending Langfuse events (for short-lived CLI processes)."""
  if not is_tracing_enabled():
    return
  from langfuse import get_client

  get_client().flush()


def get_trace_url_hint() -> str | None:
  """Return a human-readable Langfuse UI hint when tracing is active."""
  if not is_tracing_enabled():
    return None
  host = os.environ.get("LANGFUSE_HOST", DEFAULT_LANGFUSE_HOST).rstrip("/")
  return f"{host}/trace"


def new_session_id() -> str:
  """Generate a unique session id for a swarm run."""
  return str(uuid.uuid4())


def update_observation_metadata(metadata: dict[str, Any]) -> None:
  """Attach metadata to the current Langfuse observation when tracing is enabled."""
  if not is_tracing_enabled():
    return
  try:
    from langfuse import get_client

    get_client().update_current_observation(metadata=metadata)
  except Exception:
    pass


def observe(name: str | None = None):
  """Return Langfuse @observe decorator or a no-op passthrough."""
  if is_tracing_enabled():
    from langfuse import observe as langfuse_observe

    return langfuse_observe(name=name)

  def passthrough(func):
    return func

  return passthrough
