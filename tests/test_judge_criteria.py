"""Unit tests for Judge verdict criteria."""

from judge.criteria import check_response, classify_result, extract_stack_trace
from judge.models import Verdict

SAMPLE_TRACEBACK = """
INFO: Started server process
Traceback (most recent call last):
  File "/app/target_app/routes/loyalty.py", line 14, in loyalty_score
    score = body.base_points / body.months_active
ZeroDivisionError: division by zero
"""


def test_classify_robust_200() -> None:
  assert classify_result(
    200,
    crashed=False,
    response_json={"score": 1.0},
    response_checks=None,
  ) == Verdict.ROBUST


def test_classify_robust_422() -> None:
  assert classify_result(
    422,
    crashed=False,
    response_json=None,
    response_checks=None,
  ) == Verdict.ROBUST


def test_classify_vulnerable_500() -> None:
  assert classify_result(
    500,
    crashed=False,
    response_json=None,
    response_checks=None,
  ) == Verdict.VULNERABLE


def test_classify_vulnerable_crashed() -> None:
  assert classify_result(
    None,
    crashed=True,
    response_json=None,
    response_checks=None,
  ) == Verdict.VULNERABLE


def test_classify_invalid_request_timeout() -> None:
  assert classify_result(
    None,
    crashed=False,
    response_json=None,
    response_checks=None,
    timed_out=True,
  ) == Verdict.INVALID_REQUEST


def test_classify_invalid_request_404() -> None:
  assert classify_result(
    404,
    crashed=False,
    response_json=None,
    response_checks=None,
  ) == Verdict.INVALID_REQUEST


def test_classify_logic_error_on_failed_checks() -> None:
  assert classify_result(
    200,
    crashed=False,
    response_json={"first_value": 0},
    response_checks={"first_value": 7},
  ) == Verdict.LOGIC_ERROR


def test_check_response_passes_when_checks_match() -> None:
  assert check_response({"first_value": 7, "count": 2}, {"first_value": 7}) is True


def test_check_response_fails_when_checks_mismatch() -> None:
  assert check_response({"first_value": 0}, {"first_value": 7}) is False


def test_extract_stack_trace_from_stderr() -> None:
  trace = extract_stack_trace(SAMPLE_TRACEBACK)
  assert trace is not None
  assert "ZeroDivisionError" in trace


def test_extract_stack_trace_from_json_detail() -> None:
  trace = extract_stack_trace("", '{"detail":"Traceback ... ZeroDivisionError"}')
  assert trace is not None
  assert "ZeroDivisionError" in trace
