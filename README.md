# Chaos QA Swarm

**White-Box Semantic Fuzzing** pipeline: a source-readable FastAPI target app, happy-path regression tests, a deterministic Judge sandbox, and LLM agents for attack generation and patching.

## White-Box vs Black-Box

| Approach | Input | How it finds bugs |
| --- | --- | --- |
| **Black-box fuzzing** | JSON Schema / OpenAPI | Mutates fields randomly against type constraints |
| **White-box (this project)** | `target_app/` source code | Reads logic branches, hypothesizes compound payloads that execute vulnerable paths |

Trap ground truth for maintainers lives in [`docs/VULNERABILITIES.md`](docs/VULNERABILITIES.md) — not in source comments or agent prompts.

## Setup

```bash
cd ~/Desktop/chaos-qa-swarm
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,judge,agents]"
cp .env.example .env   # set GROQ_API_KEY for agents
```

Run the app locally:

```bash
uvicorn target_app.main:app --reload --port 8000
```

- Health: `GET http://localhost:8000/health`
- OpenAPI: `http://localhost:8000/openapi.json`

## Phase 1 — Target App

- FastAPI app with 5 endpoints containing compound logical traps
- Happy-path baseline tests that must pass after any future patch
- Machine-readable JSON schemas under `schemas/` (API reference and Judge routing)

```bash
pytest tests/test_baseline_happy_path.py -v
```

## Phase 2 — Judge (Deterministic Sandbox)

The Judge executes payloads against an isolated copy of `target_app/` and classifies outcomes without an LLM.

| Verdict | Meaning |
| --- | --- |
| `robust` | Handled gracefully (200 with expected data, or 400/422 validation) |
| `vulnerable` | Crash, 500, or unhandled exception |
| `logic_error` | 200 but failed `response_checks` |
| `invalid_request` | Timeout, 404, or unreachable route |

Backends:

- **Docker** (default): real container isolation via `JUDGE_SANDBOX=docker`
- **Local** (dev): subprocess uvicorn via `JUDGE_SANDBOX=local` — no container isolation

Usage:

```python
from judge.executor import evaluate_payloads
from judge.models import PayloadRequest

results = evaluate_payloads(
    source_files={},
    requests=[
        PayloadRequest(
            path="/api/loyalty/score",
            body={"account_type": "legacy", "months_active": 0, "base_points": 100},
        ),
        PayloadRequest(
            path="/api/report/aggregate",
            body={"groups": [[], [7, 8]], "metric": "throughput"},
            response_checks={"first_value": 7},
        ),
    ],
)
for result in results:
    print(result.verdict, result.stack_trace)
```

Run Judge tests:

```bash
pytest tests/test_judge_criteria.py tests/test_source_overlay.py -v
JUDGE_SANDBOX=local pytest tests/test_judge_integration.py -v -m integration
JUDGE_SANDBOX=docker pytest tests/test_judge_integration.py -v -m integration
```

Patches are applied via `source_files: dict[str, str]` overlay (see `judge/source_overlay.py`).

## Phase 3 — White-Box Agents

LangChain + Groq agents read `target_app/` source (not `VULNERABILITIES.md`) and produce structured outputs validated with Groq **strict JSON schema** mode (`method="json_schema"`, `strict=True`).

| Agent | API | Output |
| --- | --- | --- |
| **Chaos** | `generate_attacks()` → `probe_attacks()` | 1–3 attacks per run (no padding) |
| **Developer** | `generate_patch(source_files, failed_request, stack_trace)` | `patched_files` overlay map |

Reasoning depth is set via the Groq API parameter `reasoning_effort` (default `high`), not in system prompts.

### Environment variables

| Variable | Default | Purpose |
| --- | --- | --- |
| `GROQ_API_KEY` | — | Groq API authentication (required for agents) |
| `CHAOS_QA_MODEL` | `openai/gpt-oss-120b` | Groq model ID |
| `CHAOS_REASONING_EFFORT` | `high` | Groq reasoning effort (`low` / `medium` / `high`) |
| `CHAOS_ATTACK_MAX` | `3` | Max attacks per chaos run |
| `JUDGE_SANDBOX` | `docker` | `local` or `docker` for probe / Judge runs |

### Programmatic usage

```python
from agents.chaos_agent import generate_attacks, probe_attacks
from agents.developer_agent import generate_patch, merge_source_files

strategy = generate_attacks()
results = probe_attacks(strategy)

# After a vulnerable result:
patch = generate_patch(
    source_files={},
    failed_request=results[0].request,
    stack_trace=results[0].stack_trace or "",
)
merged = merge_source_files({}, patch)
```

### Manual probe script

Chaos → Judge, with optional single-patch re-eval:

```bash
export GROQ_API_KEY=...
JUDGE_SANDBOX=local python scripts/run_chaos_probe.py
JUDGE_SANDBOX=local python scripts/run_chaos_probe.py --patch
```

With `--patch`, the script patches the **first** `vulnerable` / `logic_error` result and re-runs **only that attack payload** against the patched overlay. It does **not** run `tests/test_baseline_happy_path.py` or re-probe all attacks. Baseline regression gating is planned for Phase 4 (LangGraph loop).

### Tests

Unit tests (no API key):

```bash
pytest tests/test_agents_models.py tests/test_agents_converters.py tests/test_source_bundle.py \
  tests/test_developer_validation.py tests/test_llm.py tests/test_chaos_agent.py \
  tests/test_developer_agent.py -v
```

Optional live Groq test:

```bash
pytest tests/test_agents_live.py -v -m llm
```

LangGraph orchestration (Chaos ↔ Judge ↔ Developer loop) arrives in **Phase 4**.

## API reference

Human-readable docs: [`docs/API_SCHEMA.md`](docs/API_SCHEMA.md)

Regenerate `schemas/` after changing Pydantic models:

```bash
python scripts/export_schemas.py
```
