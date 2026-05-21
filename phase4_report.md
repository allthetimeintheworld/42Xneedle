# Phase 4 Report - Model Layer

## What Was Built

Phase 4 replaced the stub `model.py` with a provider wrapper for model calls.

The public function remains compatible with `agent.py`:

```python
call_model(system: str, user: str, expect_json: bool = False) -> str
```

The module also exposes the requested testing helpers:

```python
_call_gemini(system: str, user: str) -> str
_call_groq(system: str, user: str) -> str
_extract_json(text: str) -> str
```

## Provider Behavior

The wrapper is configured for:

- Gemini primary provider:
  - model: `gemini-2.5-flash`
  - endpoint: Google Generative Language API
  - key: `GEMINI_API_KEY`

- Groq fallback provider:
  - primary model: `llama-3.3-70b-versatile`
  - secondary model: `llama-3.1-70b-versatile`
  - endpoint: OpenAI-compatible Groq chat completions API
  - key: `GROQ_API_KEY`

`call_model()` tries available providers in order. It retries provider failures up to 3 attempts, backs off on rate-limit-like failures, falls through from Gemini to Groq, and raises if configured providers all fail.

## JSON Handling

`_extract_json()` handles:

- plain JSON
- fenced JSON with `json` language tag
- fenced JSON without language tag
- prose-wrapped JSON
- nested objects and arrays

When `expect_json=True`, `call_model()` validates and returns parseable JSON text.

## Logging

The model layer writes structured metadata to:

```text
agent_logs/prompts.log
agent_logs/errors.log
```

It also writes full per-call evidence files under:

```text
agent_logs/calls/
```

Each call file contains:

- full system prompt
- full user prompt
- full model response
- provider metadata
- model name
- duration
- status

API keys are never written to logs.

## Offline Smoke Fallback

This environment does not currently have `.env`, `GEMINI_API_KEY`, or `GROQ_API_KEY` configured.

To keep local unit tests and the existing orchestrator smoke test runnable, `model.py` includes a no-key offline fallback. It logs that no API keys were found and returns deterministic smoke-test responses:

- planner-style JSON for planning calls
- a JSON `stop` action for decision calls
- a plain offline message for non-JSON calls

When real keys are configured, the wrapper uses Gemini and/or Groq instead.

## Test Coverage Added

Phase 4 added `test_model.py`.

The unit tests cover:

- plain JSON extraction
- fenced JSON extraction
- fenced JSON without language tag
- prose-wrapped JSON extraction
- invalid JSON rejection
- nested JSON extraction
- no API key strings in generated logs

The integration tests cover:

- text model call
- JSON model call
- per-call log file creation

Those integration tests are skipped automatically when neither `GEMINI_API_KEY` nor `GROQ_API_KEY` is configured.

## Verification Results

Commands run:

```bash
python3 -m pip install requests python-dotenv
python3 test_model.py
python3 test_logger.py
python3 test_tools.py
python3 -m py_compile model.py test_model.py logger.py tools.py test_logger.py test_tools.py
python3 -c "from model import call_model; print(call_model('Be concise.', 'What is 2+2?'))"
python3 -c "from model import call_model; print(call_model('Respond only in JSON.', 'Return a JSON object with key answer set to 4.', expect_json=True))"
grep -r "AIzaSy\|gsk_" agent_logs
rm -rf agent_logs state.json
python3 agent.py --spec dummy_spec.md
```

Results:

- `requests` and `python-dotenv` were installed successfully.
- `test_model.py` passed:
  - 7 unit tests passed.
  - 3 integration tests skipped because no API keys are configured.
- `test_logger.py` still passes.
- `test_tools.py` still passes.
- Compile checks pass.
- Manual text call returns the offline fallback response.
- Manual JSON call returns parseable JSON.
- API-key grep found no leaked `AIzaSy` or `gsk_` strings.
- `python3 agent.py --spec dummy_spec.md` exits with code `0`.
- `agent_logs/calls/` is created and contains per-call files.

Known limitation:

- I could not verify real Gemini or Groq API calls because no `.env` file or provider keys are present in this workspace.
- The current successful smoke test therefore validates wrapper behavior, JSON validation, logging, and orchestrator compatibility in offline mode, not live provider access.

## Current General Status

The project now has:

- `agent.py`: orchestrator loop
- `logger.py`: real structured logging layer
- `tools.py`: real sandboxed tools layer
- `model.py`: real provider wrapper with offline no-key smoke fallback
- `test_logger.py`: passing
- `test_tools.py`: passing
- `test_model.py`: passing unit tests, integration tests skipped without keys

Remaining stub module:

- `context.py`: still placeholder prompt/context construction

The next major step is Phase 5: replace `context.py` with the real prompt builder and trajectory summarizer. Once API keys are added, Phase 4 integration tests should be rerun to confirm live Gemini and Groq behavior.
