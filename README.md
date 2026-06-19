# Chaos QA Swarm

**White-Box Semantic Fuzzing** pipeline: a source-readable FastAPI target app, happy-path regression tests, and API reference exports.

## White-Box vs Black-Box

| Approach | Input | How it finds bugs |
| --- | --- | --- |
| **Black-box fuzzing** | JSON Schema / OpenAPI | Mutates fields randomly against type constraints |
| **White-box (this project)** | `target_app/` source code | Reads logic branches, hypothesizes compound payloads that execute vulnerable paths |

Phase 1 delivers the target application layer. Phase 3 adds White-Box Chaos and Developer agents that read [`target_app/`](target_app/) source and craft targeted payloads. LangGraph orchestration arrives in Phase 4.

Trap ground truth for maintainers lives in [`docs/VULNERABILITIES.md`](docs/VULNERABILITIES.md) — not in source comments.

## Phase 2 — Judge (Deterministic Sandbox)

The Judge executes payloads against an isolated copy of `target_app/` and classifies outcomes without an LLM.

- **Docker** (default): real container isolation via `JUDGE_SANDBOX=docker`
- **Local** (dev): subprocess uvicorn via `JUDGE_SANDBOX=local` — no container isolation

Install Judge dependencies:

```bash
pip install -e ".[dev,judge]"
```

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

## Phase 3 — White-Box Agents

LLM agents use LangChain + Groq structured output to analyze source and generate attacks (1–3 per run, no padding).

Install:

```bash
pip install -e ".[dev,judge,agents]"
cp .env.example .env   # set GROQ_API_KEY
```

Environment variables:

| Variable | Purpose |
| --- | --- |
| `GROQ_API_KEY` | Groq API authentication (required for agents) |
| `CHAOS_QA_MODEL` | Default `openai/gpt-oss-120b` |
| `CHAOS_ATTACK_MAX` | Max attacks per run (default `3`) |
| `JUDGE_SANDBOX` | `local` or `docker` for probe script |

Usage:

```python
from agents.chaos_agent import generate_attacks, probe_attacks
from agents.developer_agent import generate_patch

strategy = generate_attacks()
results = probe_attacks(strategy)
```

Run the manual probe (Chaos → Judge, optional patch re-eval):

```bash
export GROQ_API_KEY=...
JUDGE_SANDBOX=local python scripts/run_chaos_probe.py
JUDGE_SANDBOX=local python scripts/run_chaos_probe.py --patch
```

Agent unit tests (no API key):

```bash
pytest tests/test_agents_models.py tests/test_agents_converters.py tests/test_source_bundle.py tests/test_developer_validation.py tests/test_chaos_agent.py tests/test_developer_agent.py -v
```

Optional live Groq test:

```bash
pytest tests/test_agents_live.py -v -m llm
```

## Phase 1 — Target App

- FastAPI app with 5 endpoints containing compound logical traps
- Happy-path baseline tests that must pass after any future patch
- Machine-readable JSON schemas under `schemas/` (API reference and future Judge routing)

## Setup

```bash
cd ~/Desktop/chaos-qa-swarm
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Run the app

```bash
uvicorn target_app.main:app --reload --port 8000
```

- Health: `GET http://localhost:8000/health`
- OpenAPI: `http://localhost:8000/openapi.json`

## Run baseline tests

```bash
pytest tests/test_baseline_happy_path.py -v
```

## API reference

Human-readable docs: [`docs/API_SCHEMA.md`](docs/API_SCHEMA.md)

Regenerate `schemas/` after changing Pydantic models:

```bash
python scripts/export_schemas.py
```
