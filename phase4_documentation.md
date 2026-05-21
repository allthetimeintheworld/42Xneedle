# Phase 4 Documentation - Model Layer

## Purpose

Phase 4 built the model wrapper.

The rest of the agent should not need to know which provider is being used. It calls one function, `call_model()`, and receives a string response. The wrapper handles provider selection, retries, fallback, JSON extraction, and logging.

The implemented file is:

```text
model.py
```

The test file is:

```text
test_model.py
```

## Public API

`model.py` exposes:

```python
call_model(system: str, user: str, expect_json: bool = False) -> str
```

It also exposes helper functions for tests:

```python
_call_gemini(system: str, user: str) -> str
_call_groq(system: str, user: str) -> str
_extract_json(text: str) -> str
```

`agent.py` uses only `call_model()`.

## Providers

The wrapper is configured for two providers.

Primary provider:

```text
Gemini 2.5 Flash
```

Fallback provider:

```text
Groq Llama 3.3 70B
```

If the primary Groq model fails, the wrapper tries:

```text
llama-3.1-70b-versatile
```

## Configuration

The wrapper reads API keys from the environment, with `.env` support through `python-dotenv`.

Expected variables:

```text
GEMINI_API_KEY
GROQ_API_KEY
```

No keys are hardcoded. API keys are never logged.

## Retry And Fallback Behavior

`call_model()` tries available providers in order.

For each provider:

- up to 3 attempts
- timeout per request
- rate-limit style errors trigger backoff
- client/auth errors are logged and skipped faster
- provider failure falls through to the next provider

If all configured providers fail, the wrapper raises an error.

## JSON Extraction

When `expect_json=True`, the wrapper validates that the returned content is parseable JSON.

`_extract_json()` handles:

- plain JSON
- markdown fenced JSON
- markdown fenced JSON without a language tag
- prose before or after JSON
- nested objects and arrays

This matters because models often return:

```text
```json
{"action": "stop", "args": {}, "reasoning": "done"}
```
```

The extractor strips the fence and returns the JSON text.

## Offline Fallback

The current workspace does not have `.env`, `GEMINI_API_KEY`, or `GROQ_API_KEY`.

To keep tests and smoke runs usable without live provider access, `model.py` includes an offline fallback. It is only used when no keys are configured.

The fallback returns deterministic responses:

- planning calls return `{"steps": ["offline planning fallback"]}`
- decision calls return a valid JSON `stop` action
- plain text calls return an offline message

This lets `agent.py --spec dummy_spec.md` continue to run locally. With real keys configured, the wrapper uses Gemini/Groq instead.

## Logging

The model layer logs metadata to:

```text
agent_logs/prompts.log
agent_logs/errors.log
```

It also writes full per-call files to:

```text
agent_logs/calls/
```

Each call file contains:

- full system prompt
- full user prompt
- full response
- provider
- model
- duration
- status

The main log keeps previews short. Full prompts and responses live in `agent_logs/calls/` for auditability.

## How It Adds To `agent.py`

Before Phase 4, `model.py` was a stub that always returned a canned plan and then stopped.

After Phase 4, `agent.py` can call a real provider through the same function signature:

```python
response = call_model(system, user, expect_json=True)
```

That means the orchestrator does not need provider-specific logic.

## Tests

`test_model.py` includes unit tests for:

- plain JSON extraction
- fenced JSON extraction
- prose-wrapped JSON extraction
- nested JSON extraction
- invalid JSON rejection
- no API key leakage in logs

It also includes integration tests for real model calls. Those tests are skipped when no API keys are configured.

Run it with:

```bash
python3 test_model.py
```

## Verification Status

Phase 4 passed offline verification:

```bash
python3 test_model.py
python3 test_logger.py
python3 test_tools.py
python3 -m py_compile model.py test_model.py logger.py tools.py test_logger.py test_tools.py
grep -r "AIzaSy\|gsk_" agent_logs
python3 agent.py --spec dummy_spec.md
```

The provider integration tests were skipped because API keys are not configured in this workspace.

To verify live providers later:

1. create `.env`
2. add `GEMINI_API_KEY`
3. add `GROQ_API_KEY`
4. rerun `python3 test_model.py`
