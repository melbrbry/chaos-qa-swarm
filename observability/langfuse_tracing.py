"""Langfuse tracing helpers for the chaos QA swarm."""

from __future__ import annotations

import os
import uuid
from typing import Any

import httpx

DEFAULT_LANGFUSE_HOST = "https://cloud.langfuse.com"

_handler = None
_last_auth_error: str | None = None


def langfuse_base_url() -> str:
  """Return configured Langfuse API base URL."""
  return (
    os.environ.get("LANGFUSE_BASE_URL")
    or os.environ.get("LANGFUSE_HOST")
    or DEFAULT_LANGFUSE_HOST
  ).rstrip("/")


def is_tracing_enabled() -> bool:
  """Return True when Langfuse credentials are configured and not explicitly disabled."""
  if os.environ.get("LANGFUSE_ENABLED", "1").strip().lower() in {"0", "false", "no"}:
    return False
  return bool(os.environ.get("LANGFUSE_PUBLIC_KEY") and os.environ.get("LANGFUSE_SECRET_KEY"))


def validate_langfuse_credentials() -> bool:
  """Return True when Langfuse API credentials authenticate successfully."""
  global _last_auth_error
  _last_auth_error = None
  if not is_tracing_enabled():
    return False
  _ensure_langfuse_env()
  public_key = os.environ.get("LANGFUSE_PUBLIC_KEY", "").strip()
  secret_key = os.environ.get("LANGFUSE_SECRET_KEY", "").strip()
  base_url = langfuse_base_url()
  try:
    response = httpx.get(
      f"{base_url}/api/public/projects",
      auth=(public_key, secret_key),
      timeout=10.0,
    )
  except httpx.HTTPError as exc:
    _last_auth_error = f"Could not reach Langfuse at {base_url}: {exc}"
    return False

  if response.status_code == 200:
    return True

  detail = response.text.strip()
  if len(detail) > 200:
    detail = detail[:200] + "..."
  _last_auth_error = (
    f"Langfuse API rejected credentials (HTTP {response.status_code}) at {base_url}. "
    f"{detail or 'Create new project API keys in the Langfuse UI.'}"
  )
  return False


def get_last_auth_error() -> str | None:
  """Return the most recent Langfuse credential validation error."""
  return _last_auth_error


def ensure_tracing_ready(*, quiet: bool = False) -> bool:
  """Disable tracing when credentials are missing or invalid. Returns tracing active state."""
  if not is_tracing_enabled():
    return False
  if validate_langfuse_credentials():
    return True
  os.environ["LANGFUSE_ENABLED"] = "0"
  global _handler
  _handler = None
  if not quiet:
    detail = get_last_auth_error() or (
      "Verify LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, and LANGFUSE_HOST "
      f"({langfuse_base_url()})."
    )
    print(f"Langfuse tracing disabled: {detail}")
  return False


def _ensure_langfuse_env() -> None:
  base_url = langfuse_base_url()
  os.environ.setdefault("LANGFUSE_HOST", base_url)
  os.environ.setdefault("LANGFUSE_BASE_URL", base_url)


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
  host = langfuse_base_url()
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
