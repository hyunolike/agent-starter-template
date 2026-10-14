# Extend the starter

[English README](../README.md) · [한국어 README](README.ko.md)

## Add a read-only tool

1. Implement the domain behavior in `services/`.
2. Add a Pydantic input model inheriting `ToolInput` in `tools/registry.py`.
3. Write an async function returning a JSON-serializable dictionary.
4. Register a `StructuredTool` in `build_tools()` with a clear description and schema.
5. Add tests for valid input, invalid input, absence of data, and service failure.

For example, a purely local greeting tool can be added to the registry module:

```python
class GreetingInput(ToolInput):
    name: str = Field(min_length=1, max_length=80)


async def greet(name: str) -> dict:
    return {"greeting": f"Hello, {name}!"}


# Append inside build_tools():
StructuredTool.from_function(
    coroutine=greet,
    name="greet",
    description="Return a friendly greeting for the supplied name.",
    args_schema=GreetingInput,
)
```

The real model receives registered tool schemas automatically. The scripted `DemoModel` does not discover new tools: extend its deterministic routing explicitly if you want a demo example, or exercise the tool directly in tests.

For network I/O, use an async client with its own timeout. Return compact, bounded results. Do not pass provider exceptions or credentials directly to the model. All tools must return a dictionary; use an `error` key for a handled failure.

## Replace demo data

`services/knowledge.py` performs keyword overlap against the packaged JSON corpus. It is not vector retrieval or a production RAG pipeline. Replace the service with your chosen retrieval implementation while preserving explicit source identifiers and empty-result behavior.

`services/requests.py` uses fictional records. Replace it with an authorized application-service call; keep business permissions out of prompts.

## Add a model provider

Implement the `AgentModel` protocol: `ainvoke(messages)` must return a LangChain `AIMessage`, including normalized `tool_calls` when applicable. Bind the tool schemas, add the provider choice to `Settings`, and update `build_model()`.

Keep model names and credentials in environment configuration. Add adapter-construction tests without networking, plus opt-in live tests for the chosen provider. Never make paid evaluations a prerequisite for the default quick start.

## Change prompts

Edit `src/agent_app/agent/prompts/system.md`, which is packaged with the wheel. Test affected behavior against representative real-model cases; scripted demo checks do not validate prompt quality.

## Add write operations later

Read [execution semantics](ARCHITECTURE.md#extending-to-writes) first. Add durable authorization/approval and idempotency before exposing writes. Neither SQLite checkpoints nor `run_id` alone guarantee exactly-once side effects.
