# Architecture and execution semantics

[English README](../README.md) · [한국어 README](README.ko.md)

## Decisions

| Decision | Reason | Trade-off |
| --- | --- | --- |
| One agent with tools | Small enough to understand and test | No specialist delegation |
| Explicit LangGraph loop | Make state transitions and budgets visible | A little more code than a prebuilt agent |
| Thin tool adapters | Reuse business services from other entrypoints | Developers must keep the boundary intact |
| Async SQLite checkpoints | Run locally without another service | One application worker per file |
| Scripted default provider | Reproducible onboarding without API charges | Does not demonstrate language-model quality |
| Read-only examples | Incomplete nodes can be replayed safely | Write workflows need additional design |

## State and identifiers

`thread_id` is a UUID identifying a conversation and its saved checkpoints. `run_id` identifies one HTTP execution or resume response; it is not an idempotency key or a persistent job record.

The state contains messages, current-turn model/tool counters, tool event metadata, status, and provider-reported token counts. New turns reset counters but retain messages. Resume uses `ainvoke(None, config)` and preserves the last committed state.

Each completed graph step is checkpointed. If a request is interrupted, the current node may execute again. Counters and token usage reflect committed graph state, not every attempted network request. Provider retries and interrupted responses may consume additional tokens. They are not a billing ledger or hard monetary budget.

## Concurrency

The runtime keeps an in-process set of active thread IDs. With one async event loop, checking and adding an ID without awaiting prevents two requests from entering the same thread simultaneously. The second request receives `409 thread_busy`; other threads remain independent.

This is not a distributed lock. Multiple processes or replicas can violate this guarantee. Before scaling, use an appropriate persistent checkpointer and durable admission/concurrency mechanism. Changing only `--workers` is insufficient.

## Timeouts and recovery

Tools execute sequentially and return structured errors for invalid inputs, unregistered tools, timeout, or exceptions. A model can use those observations to explain or recover within the remaining budget.

The outer async timeout stops the current graph invocation. The API returns 504 with the thread ID. Inspect the thread and resume only if it has pending nodes. A completed thread returns `409 nothing_to_resume`. Sending new input to an unfinished thread returns `409 resume_required`.

Cancellation is cooperative. A blocking function can block the event loop and defeat a timeout; use async clients for I/O and isolated workers for CPU-heavy/untrusted execution.

The history setting is a new-turn admission threshold, not a database retention limit. A final turn can cross the threshold, and checkpoints remain until separately cleaned up. This starter intentionally does not delete user data automatically.

## Extending to writes

Before adding an action such as issuing a reward, implement authorization in the service, durable approval state when needed, and a persisted idempotency key tied to the business operation. Record intent and outcome, and test failure between the external side effect and checkpoint commit. Model prompts and local thread serialization do not prevent duplicate writes after a crash.

## Data boundaries

The registry controls which functions the model may call. It is not a per-user permission system. The optional bearer token is shared by a single tenant; any holder can access a known thread ID. Do not use this as a multi-user authorization boundary.

SQLite stores message and tool content. Application events log only event/status/run ID metadata. Uvicorn access logs and optional third-party tracing have separate behavior; inspect their configuration before connecting sensitive data. The included corpus and request records are fictional.
