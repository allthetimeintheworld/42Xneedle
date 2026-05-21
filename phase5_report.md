# Phase 5 Report - Context Layer

## What Was Built

Phase 5 replaced the stub `context.py` with a real prompt/context builder for the autonomous coding agent.

The implemented public functions are:

```python
build_planning_prompt(spec_text: str) -> tuple[str, str]
build_context(state: dict) -> tuple[str, str]
summarize_trajectory(recent_actions: list[dict]) -> str
```

These are the exact functions imported by `agent.py`.

## Prompt Templates

Phase 5 added a new `prompts/` directory:

```text
prompts/system.txt
prompts/plan.txt
prompts/decide.txt
```

The prompt content now lives in editable text files instead of long Python string literals.

Current prompt sizes:

- `system.txt`: 442 words
- `plan.txt`: 114 words
- `decide.txt`: 74 words
- total: 630 words

The system prompt establishes:

- the agent role
- the gather-act-verify workflow
- tool descriptions
- read-before-edit expectations
- test-after-change expectations
- JSON-only output format
- source-of-truth rules
- anti-patterns to avoid

## Context Builder Behavior

`build_planning_prompt(spec_text)`:

- Loads the shared system prompt.
- Builds the planning user prompt from `prompts/plan.txt`.
- Includes the full spec text.
- Asks for JSON of shape `{"steps": [...]}`.
- Logs prompt size metadata to `prompts.log`.

`build_context(state)`:

- Loads the shared system prompt.
- Builds a per-iteration decide prompt from `prompts/decide.txt`.
- Includes five labeled sections:
  - `=== SPEC ===`
  - `=== PLAN ===`
  - `=== WORKSPACE ===`
  - `=== LAST TEST RESULT ===`
  - `=== RECENT ACTIONS ===`
- Logs section sizes and total prompt size to `prompts.log`.

Section helpers now build:

- a spec section with truncation support for very large specs
- a plan section with `current_step_index` marked as current
- a workspace tree with file sizes, capped at 30 entries
- a test-result section with pass/fail/error counts
- a compact trajectory section from recent actions and older summaries

`summarize_trajectory(recent_actions)`:

- Uses deterministic summarization, not a model call.
- Counts reads, edits, test runs, edited files, and guardrail rejections.
- Returns a compact summary under 500 characters.

## How This Adds To `agent.py`

`agent.py` did not need to change.

Before Phase 5, `agent.py` called a stub context layer that returned minimal prompts like `You are a stub` and `Iteration 0`. After Phase 5, those same call sites now receive structured prompts that tell the model:

- what the task is
- what the current plan is
- what files exist in `workspace/`
- what happened in the last test run
- what recent actions were already attempted
- exactly which JSON decision schema to return

This turns the model call from a generic prompt into an agent-specific decision interface.

## Test Coverage Added

Phase 5 added `test_context.py` with 10 unit tests covering:

- planning prompt shape
- spec inclusion in the planning prompt
- `steps` output-key instruction
- decide prompt shape
- all five section headers
- recent action formatting
- last test result formatting
- no-test-run messaging
- empty trajectory summary behavior
- non-empty trajectory summary under 500 chars
- prompt template file existence

These tests intentionally verify structure, not prompt quality. Prompt quality still needs manual tuning during real runs.

## Verification Results

Commands run:

```bash
python3 test_context.py
python3 test_logger.py
python3 test_tools.py
python3 test_model.py
python3 -m py_compile agent.py logger.py tools.py model.py context.py test_logger.py test_tools.py test_model.py test_context.py
rm -rf agent_logs state.json workspace
python3 agent.py --spec dummy_spec.md
wc -w prompts/system.txt prompts/plan.txt prompts/decide.txt
```

Results:

- `test_context.py` passes.
- `test_logger.py` passes.
- `test_tools.py` passes.
- `test_model.py` passes its unit tests, with provider integration tests skipped because API keys are not configured.
- Compile checks pass.
- `python3 agent.py --spec dummy_spec.md` exits with code `0`.
- `agent_logs/prompts.log` shows the new planning and decide prompt metadata.
- `agent_logs/calls/` contains per-call prompt/response files.

Known limitation:

- Because no `GEMINI_API_KEY` or `GROQ_API_KEY` is configured, the smoke test uses the Phase 4 offline fallback and stops immediately. That confirms orchestration compatibility and prompt construction, but it does not validate live model behavior or prompt quality.

## Issue Fixed During Phase 5

The first smoke run hit the iteration cap because the Phase 4 offline fallback classified the new decide prompt as a planning prompt. The new decide prompt contains a `PLAN` section, and the fallback was using overly broad `"plan"` detection.

I tightened the offline fallback in `model.py` so it recognizes actual planning prompts by the planning-template language and `steps` schema. After that fix, the smoke test exited cleanly.

## Current General Status

The project now has all core modules implemented:

- `agent.py`: orchestrator loop
- `logger.py`: structured logging
- `tools.py`: sandboxed filesystem/shell/test tools
- `model.py`: Gemini/Groq wrapper with offline fallback
- `context.py`: prompt/context builder

Test files now present:

- `test_logger.py`
- `test_tools.py`
- `test_model.py`
- `test_context.py`

Remaining work:

- Add real API keys and rerun `test_model.py` integration tests.
- Tune `prompts/system.txt`, `prompts/plan.txt`, and `prompts/decide.txt` based on real model behavior.
- Run Phase 6 end-to-end against a more realistic dummy spec.
- Add `agent_manifest.json` and final project documentation if required by the hackathon flow.
