"""Sandbox backends for isolated target app execution."""

from __future__ import annotations

import io
import logging
import os
import socket
import subprocess
import tarfile
import time
from pathlib import Path
from typing import Protocol

import httpx

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_IMAGE = "chaos-qa-swarm-target:latest"
DEFAULT_DOCKERFILE = REPO_ROOT / "docker" / "Dockerfile"
HEALTH_PATH = "/health"
HEALTH_TIMEOUT_S = 30.0
HEALTH_INTERVAL_S = 0.5
STOP_TIMEOUT_S = 5


class Sandbox(Protocol):
  """Protocol for sandbox backends."""

  def start(self, overlay_path: Path) -> str:
    """Start the target app and return its base URL."""

  def logs(self) -> tuple[str, str]:
    """Return stdout and stderr captured from the sandbox."""

  def is_running(self) -> bool:
    """Return False when the sandbox process/container has exited."""

  def stop(self) -> None:
    """Stop and clean up sandbox resources."""


def create_sandbox() -> Sandbox:
  """Create a sandbox backend from JUDGE_SANDBOX env var."""
  backend = os.environ.get("JUDGE_SANDBOX", "docker").strip().lower()
  if backend == "local":
    logger.warning(
      "LocalSandbox active — no container isolation. Use JUDGE_SANDBOX=docker for real runs."
    )
    return LocalSandbox()
  if backend == "docker":
    return DockerSandbox()
  raise ValueError(f"Unknown JUDGE_SANDBOX value: {backend!r}")


def _pick_free_port() -> int:
  with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.bind(("127.0.0.1", 0))
    return sock.getsockname()[1]


def _wait_for_health(base_url: str) -> None:
  deadline = time.monotonic() + HEALTH_TIMEOUT_S
  last_error: Exception | None = None
  with httpx.Client(timeout=2.0) as client:
    while time.monotonic() < deadline:
      try:
        response = client.get(f"{base_url}{HEALTH_PATH}")
        if response.status_code == 200:
          return
      except Exception as exc:  # noqa: BLE001 - poll until ready or timeout
        last_error = exc
      time.sleep(HEALTH_INTERVAL_S)
  message = f"Sandbox health check timed out for {base_url}{HEALTH_PATH}"
  if last_error is not None:
    message = f"{message}: {last_error}"
  raise TimeoutError(message)


def _overlay_tar_bytes(overlay_path: Path) -> bytes:
  buffer = io.BytesIO()
  with tarfile.open(fileobj=buffer, mode="w") as tar:
    tar.add(overlay_path / "target_app", arcname="target_app")
  return buffer.getvalue()


class DockerSandbox:
  """Run target_app inside a Docker container with injected source overlay."""

  def __init__(
    self,
    *,
    image: str = DEFAULT_IMAGE,
    dockerfile: Path = DEFAULT_DOCKERFILE,
  ) -> None:
    self._image = image
    self._dockerfile = dockerfile
    self._client = None
    self._container = None
    self._base_url: str | None = None
    self._stdout = ""
    self._stderr = ""
    self._image_built = False

  def _docker(self):
    if self._client is None:
      import docker

      self._client = docker.from_env()
    return self._client

  def _ensure_image(self) -> None:
    if self._image_built:
      return
    client = self._docker()
    try:
      client.images.get(self._image)
      self._image_built = True
      return
    except Exception:  # noqa: BLE001 - image missing, build below
      pass

    logger.info("Building Docker image %s", self._image)
    client.images.build(
      path=str(REPO_ROOT),
      dockerfile=str(self._dockerfile.relative_to(REPO_ROOT)),
      tag=self._image,
      rm=True,
    )
    self._image_built = True

  def start(self, overlay_path: Path) -> str:
    self._ensure_image()
    host_port = _pick_free_port()
    client = self._docker()
    self._container = client.containers.run(
      self._image,
      command=["sleep", "infinity"],
      detach=True,
      ports={"8000/tcp": host_port},
      auto_remove=False,
    )
    injected = self._container.put_archive("/app", _overlay_tar_bytes(overlay_path))
    if not injected:
      stdout, stderr = self.logs()
      self.stop()
      raise RuntimeError(
        f"Failed to inject overlay into container.\nstdout:\n{stdout}\nstderr:\n{stderr}"
      )

    import_check = self._container.exec_run(
      ["python", "-c", "import target_app.main"],
      environment={"PYTHONPATH": "/app"},
    )
    if import_check.exit_code != 0:
      stdout, stderr = self.logs()
      import_error = import_check.output.decode("utf-8", errors="replace")
      self.stop()
      raise RuntimeError(
        "Docker sandbox failed to import patched target_app.\n"
        f"import_check:\n{import_error}\nstdout:\n{stdout}\nstderr:\n{stderr}"
      )

    self._container.exec_run(
      [
        "uvicorn",
        "target_app.main:app",
        "--host",
        "0.0.0.0",
        "--port",
        "8000",
      ],
      detach=True,
      environment={"PYTHONPATH": "/app"},
    )
    self._base_url = f"http://127.0.0.1:{host_port}"
    try:
      _wait_for_health(self._base_url)
    except Exception:
      stdout, stderr = self.logs()
      self.stop()
      raise RuntimeError(
        f"Docker sandbox failed to become healthy.\nstdout:\n{stdout}\nstderr:\n{stderr}"
      ) from None
    return self._base_url

  def logs(self) -> tuple[str, str]:
    if self._container is None:
      return self._stdout, self._stderr
    raw = self._container.logs(stdout=True, stderr=True, tail=500)
    if isinstance(raw, bytes):
      text = raw.decode("utf-8", errors="replace")
    else:
      text = str(raw)
    self._stdout = text
    self._stderr = text
    return self._stdout, self._stderr

  def is_running(self) -> bool:
    if self._container is None:
      return False
    self._container.reload()
    return self._container.status == "running"

  def stop(self) -> None:
    if self._container is None:
      return
    try:
      self.logs()
      self._container.stop(timeout=STOP_TIMEOUT_S)
    except Exception:  # noqa: BLE001 - best-effort cleanup
      pass
    try:
      self._container.remove(force=True)
    except Exception:  # noqa: BLE001 - best-effort cleanup
      pass
    finally:
      self._container = None
      self._base_url = None


class LocalSandbox:
  """Run target_app as a local uvicorn subprocess (dev convenience only)."""

  def __init__(self) -> None:
    self._process: subprocess.Popen[str] | None = None
    self._base_url: str | None = None
    self._stdout = ""
    self._stderr = ""

  def start(self, overlay_path: Path) -> str:
    host_port = _pick_free_port()
    env = os.environ.copy()
    env["PYTHONPATH"] = str(overlay_path.resolve())

    self._process = subprocess.Popen(
      [
        "uvicorn",
        "target_app.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        str(host_port),
      ],
      cwd=str(overlay_path),
      env=env,
      stdout=subprocess.PIPE,
      stderr=subprocess.PIPE,
      text=True,
    )
    self._base_url = f"http://127.0.0.1:{host_port}"
    try:
      _wait_for_health(self._base_url)
    except Exception:
      self.stop()
      raise
    return self._base_url

  def logs(self) -> tuple[str, str]:
    if self._process is None:
      return self._stdout, self._stderr
    if self._process.poll() is not None:
      stdout, stderr = self._process.communicate(timeout=1)
      self._stdout = stdout or ""
      self._stderr = stderr or ""
    return self._stdout, self._stderr

  def is_running(self) -> bool:
    if self._process is None:
      return False
    return self._process.poll() is None

  def stop(self) -> None:
    if self._process is None:
      return
    if self._process.poll() is None:
      self._process.terminate()
      try:
        self._process.wait(timeout=STOP_TIMEOUT_S)
      except subprocess.TimeoutExpired:
        self._process.kill()
        self._process.wait(timeout=STOP_TIMEOUT_S)
    self.logs()
    self._process = None
    self._base_url = None
