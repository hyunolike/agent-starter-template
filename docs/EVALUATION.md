# Evaluation

[English README](../README.md) · [한국어 README](README.ko.md)

## Included checks

```bash
uv run pytest -q
uv run python evals/evaluate.py
```

Tests exercise validation, tool allowlists, timeouts, model/tool budgets, auth, per-thread concurrency, persistence, and resumption. The evaluation runner reads `evals/cases.jsonl`, creates a temporary database, and uses the deterministic demo provider. It exits nonzero when a case fails.

Each case specifies a message, expected tool, expected output substring, and an optional tool error. Every case uses a fresh thread. The runner is intentionally fixed to demo mode so credentials in the environment cannot silently turn it into a paid evaluation.

## What these results do not prove

A passing demo suite proves that selected application contracts work under a scripted model. It does not establish natural-language understanding, prompt-injection resistance, factual correctness across arbitrary queries, or production reliability.

The real-model adapter test checks construction and schema binding without a network call. Live Anthropic responses are not part of the default test suite.

## Build a real-model suite

Define a separate opt-in runner and a representative dataset before publishing a quality score. Track model/version, prompt version, dependency lock revision, trial count, latency, usage, tool trace, and final outcome. Run multiple trials because model outputs vary.

| Scenario | Suggested assertion |
| --- | --- |
| Supported policy question | Answer is supported by a returned document ID |
| Unknown policy | Agent acknowledges missing evidence |
| Unknown request | No fabricated status or record |
| Malicious retrieved instructions | No forbidden tool or unauthorized behavior |
| Tool failure | No false claim that the action succeeded |
| Budget exhausted | Bounded termination and explicit limit status |
| Added write tool | Inspect the real stored outcome and deduplication behavior |

Prefer deterministic checks for objective outcomes. Use calibrated human or model grading for semantic quality, with a clear rubric. Do not grade only whether the agent says “done.”

Reference: [Anthropic — Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents).
