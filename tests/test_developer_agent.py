"""Developer agent tests with mocked LLM."""

from agents.developer_agent import generate_patch, merge_source_files
from agents.models import DeveloperPatch
from judge.models import PayloadRequest


class FakeStructuredLLM:
  def __init__(self, result):
    self._result = result

  def with_structured_output(self, schema, **kwargs):
    return self

  def invoke(self, messages):
    return self._result


def test_generate_patch_validates_paths() -> None:
  patch = DeveloperPatch(
    thought_process="Add guard for zero months",
    patched_files={"target_app/routes/loyalty.py": "def fixed(): pass"},
  )
  llm = FakeStructuredLLM(patch)
  result = generate_patch(
    source_files={},
    failed_request=PayloadRequest(
      path="/api/loyalty/score",
      body={"account_type": "legacy", "months_active": 0, "base_points": 100},
    ),
    stack_trace="ZeroDivisionError: division by zero",
    llm=llm,
  )
  assert "target_app/routes/loyalty.py" in result.patched_files


def test_merge_source_files_overlays_patch() -> None:
  patch = DeveloperPatch(
    thought_process="fix",
    patched_files={"target_app/routes/loyalty.py": "# patched loyalty"},
  )
  merged = merge_source_files({"target_app/routes/loyalty.py": "# original"}, patch)
  assert merged["target_app/routes/loyalty.py"] == "# patched loyalty"
