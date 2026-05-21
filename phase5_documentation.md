# Phase 5 Documentation - Context Layer

## Purpose

Phase 5 built the context layer.

This is the part of the agent that shapes model behavior. It decides what the model sees during planning and during each action decision.

The implemented file is:

```text
context.py
```

The test file is:

```text
test_context.py
```

The prompt templates live in:

```text
prompts/
```

## Public API

`context.py` exposes three functions used by `agent.py`:

```python
build_planning_prompt(spec_text: str) -> tuple[str, str]
build_context(state: dict) -> tuple[str, str]
summarize_trajectory(recent_actions: list[dict]) -> str
```

These functions do not call the model. They only return `(system_prompt, user_prompt)` tuples.

## Prompt Files

Phase 5 added:

```text
prompts/system.txt
prompts/plan.txt
prompts/decide.txt
```

Prompt text lives in files so it can be edited without changing Python code.

Current prompt sizes:

- `system.txt`: 442 words
- `plan.txt`: 114 words
- `decide.txt`: 74 words

## System Prompt

`prompts/system.txt` describes how the agent should behave.

It tells the model:

- it is an autonomous coding agent
- it must choose exactly one action per turn
- it should work in a gather-act-verify loop
- it should read/list before editing
- it should run tests after meaningful changes
- it must return JSON only
- it must not edit tests to hide failures
- it must not declare success until tests pass

It also describes each available action:

```text
read_file
edit_file
list_dir
run_shell
run_tests
stop
```

## Planning Prompt

`build_planning_prompt(spec_text)` uses:

```text
prompts/system.txt
prompts/plan.txt
```

It asks the model to turn the task spec into ordered implementation steps.

Expected model response:

```json
{"steps": ["step 1", "step 2", "step 3"]}
```

`agent.py` stores those steps in `state["plan"]`.

## Decide Prompt

`build_context(state)` uses:

```text
prompts/system.txt
prompts/decide.txt
```

The user prompt contains five labeled sections:

```text
=== SPEC ===
=== PLAN ===
=== WORKSPACE ===
=== LAST TEST RESULT ===
=== RECENT ACTIONS ===
```

The model is expected to return:

```json
{"action": "...", "args": {}, "reasoning": "..."}
```

`agent.py` validates and executes that decision.

## Section Builders

### Spec Section

Includes the task specification.

Small specs are included in full. Very large specs are truncated with a note, so prompts do not become too large.

### Plan Section

Lists the planned steps and marks the current step:

```text
Step 1: create main.py  [<-- current]
Step 2: run tests
```

`agent.py` does not yet auto-advance `current_step_index`, so the marker is currently informational.

### Workspace Section

Lists files under `workspace/` with sizes.

If the workspace is empty, it says:

```text
workspace/
(empty - no files created yet)
```

The listing is capped at 30 entries.

### Last Test Result Section

If no tests have run, it says:

```text
(no test run yet - call run_tests to get feedback)
```

If tests have run, it shows pass/fail/error counts and the failure summary.

### Recent Actions Section

Shows recent actions in compact one-line form:

```text
iter 3: read_file main.py - read 412 chars (success)
iter 4: edit_file main.py - wrote 500 bytes (success)
iter 5: run_tests - 1 failed (failed)
```

If older actions were compressed, it prepends the older summary.

## Trajectory Summary

`summarize_trajectory(recent_actions)` compresses old action records into a short deterministic summary.

It counts:

- total actions
- edited files
- read operations
- test runs
- guardrail rejections

It does not call the model. This keeps summarization fast and reliable.

## Logging

The context layer logs prompt size metadata to:

```text
agent_logs/prompts.log
```

For planning prompts, it logs spec length and total prompt length.

For decide prompts, it logs section sizes:

```text
spec=<N> plan=<N> workspace=<N> test=<N> traj=<N> total=<N>
```

This helps spot prompt bloat during longer runs.

## How It Adds To `agent.py`

Before Phase 5, `context.py` returned minimal stub prompts.

After Phase 5, `agent.py` receives prompts that include:

- the spec
- the plan
- workspace contents
- test feedback
- action history
- exact JSON output instructions

This gives the model enough context to make informed decisions instead of guessing from `Iteration 0`.

## Tests

`test_context.py` verifies:

- planning prompt shape
- spec inclusion
- `steps` instruction
- decide prompt shape
- all five section headers
- recent action formatting
- test result formatting
- no-test-run message
- trajectory summarization
- prompt template files exist

Run it with:

```bash
python3 test_context.py
```

## Verification Status

Phase 5 passed:

```bash
python3 test_context.py
python3 test_logger.py
python3 test_tools.py
python3 test_model.py
python3 -m py_compile agent.py logger.py tools.py model.py context.py test_logger.py test_tools.py test_model.py test_context.py
python3 agent.py --spec dummy_spec.md
```

The smoke test exits with code `0`.

Because no real API keys are configured, the smoke test uses the Phase 4 offline fallback. That verifies prompt construction and orchestrator compatibility, but real prompt quality still needs to be tuned with live model calls.
