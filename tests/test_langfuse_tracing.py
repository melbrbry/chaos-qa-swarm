"""Unit tests for Langfuse tracing helpers."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from observability import langfuse_tracing


@pytest.fixture(autouse=True)
def _clear_langfuse_env(monkeypatch):
  for key in (
    "LANGFUSE_PUBLIC_KEY",
    "LANGFUSE_SECRET_KEY",
    "LANGFUSE_HOST",
    "LANGFUSE_ENABLED",
  ):
    monkeypatch.delenv(key, raising=False)
  langfuse_tracing._handler = None


def test_is_tracing_enabled_false_without_keys() -> None:
  assert langfuse_tracing.is_tracing_enabled() is False


def test_is_tracing_enabled_respects_explicit_disable(monkeypatch) -> None:
  monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
  monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")
  monkeypatch.setenv("LANGFUSE_ENABLED", "0")
  assert langfuse_tracing.is_tracing_enabled() is False


def test_get_langfuse_handler_returns_none_when_disabled() -> None:
  assert langfuse_tracing.get_langfuse_handler() is None


def test_graph_invoke_config_has_no_callbacks_when_disabled() -> None:
  config = langfuse_tracing.graph_invoke_config(
    session_id="session-1",
    tags=["chaos-qa-swarm"],
  )
  assert "callbacks" not in config
  assert config["metadata"]["langfuse_session_id"] == "session-1"
  assert config["metadata"]["langfuse_tags"] == ["chaos-qa-swarm"]


def test_graph_invoke_config_attaches_handler_when_enabled(monkeypatch) -> None:
  monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
  monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")
  handler = MagicMock()
  with patch("observability.langfuse_tracing.get_langfuse_handler", return_value=handler):
    config = langfuse_tracing.graph_invoke_config(callbacks=True)
  assert config["callbacks"] == [handler]


def test_graph_invoke_config_can_skip_callbacks(monkeypatch) -> None:
  monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
  monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")
  config = langfuse_tracing.graph_invoke_config(callbacks=False)
  assert "callbacks" not in config


def test_flush_tracing_noop_when_disabled() -> None:
  langfuse_tracing.flush_tracing()


def test_observe_passthrough_when_disabled() -> None:
  @langfuse_tracing.observe(name="unit-test")
  def sample(value: int) -> int:
    return value + 1

  assert sample(1) == 2


def test_build_graph_without_tracing(monkeypatch) -> None:
  monkeypatch.setenv("LANGFUSE_ENABLED", "0")
  from graph.graph import build_graph

  app = build_graph(enable_tracing=False)
  assert app is not None
