# Agent Orchestrator Documentation

## Overview

This project contains a single-file autonomous coding-agent orchestrator in `agent.py`.

The orchestrator does not call a model API directly. Instead, it depends on four project modules:

- `model.py` provides `call_model(...)`
- `tools.py` provides sandboxed file, shell, and test tools
- `context.py` builds prompts and summarizes old action history
- `logger.py` provides named loggers and human intervention logging

The orchestrator reads a technical spec from disk, asks the model for a plan, then enters a decide-execute-observe-log loop. Each loop iteration asks the model for one JSON decision, validates it with guardrails, executes the allowed action, records the result, and persists state to `state.json`.

## Files

### `agent.py`

The main orchestrator. Run it with:

```bash
python3 agent.py --spec dummy_spec.md
```

Useful commands:

```bash
python3 agent.py --resume
python3 agent.py --spec dummy_spec.md --max-iter 80
python3 agent.py --log-intervention "manual note"
```

### `model.py`

Temporary stub dependency for smoke testing.

It returns:

- a canned plan during the planning step
- a canned `stop` action during the loop

This lets us test orchestrator plumbing without needing a real language model yet.

### `tools.py`

Temporary stub dependency for smoke testing.

It provides simple implementations of:

- `read_file`
- `edit_file`
- `list_dir`
- `run_shell`
- `run_tests`

These are intentionally minimal. The real project should replace them with sandboxed implementations.

### `context.py`

Temporary stub dependency for smoke testing.

It returns simple planning and decision prompts and a basic trajectory summary string.

### `logger.py`

Temporary stub dependency for smoke testing.

It creates log files under `agent_logs/` and supports human intervention logging.

### `dummy_spec.md`

A tiny spec used for smoke testing:

```text
Build a CLI that prints "hello world".
```

## Runtime Outputs

When the orchestrator runs, it creates:

```text
state.json
workspace/
agent_logs/
```

The `agent_logs/` directory should contain:

```text
commands.log
decisions.log
errors.log
human_interventions.log
prompts.log
test_runs.log
```

## State Persistence

The orchestrator stores progress in `state.json` after every iteration.

Important fields:

- `iteration`: current loop iteration
- `plan`: model-generated implementation plan
- `recent_actions`: latest action records
- `files_touched`: files edited by the orchestrator
- `done`: whether the run has stopped cleanly
- `stop_reason`: why the run stopped
- `fingerprints`: recent action fingerprints used for repeat detection

State is written atomically through `state.json.tmp` and then renamed to `state.json`.

## Guardrails

Before executing a model decision, `agent.py` applies these checks:

1. Schema validation
2. Repeat detection
3. Read-before-edit for existing files
4. Path and shell sandbox checks

If a guardrail rejects an action, the orchestrator logs the rejection, saves state, increments the iteration, and continues.

## Smoke Tests

These tests verify that the orchestrator plumbing works. They do not verify autonomous coding quality.

### 1. Syntax Check

Run:

```bash
python3 -m py_compile agent.py model.py tools.py context.py logger.py
```

Expected result:

- no output
- exit code `0`

This confirms the Python files parse correctly.

### 2. Fresh Run Test

Run:

```bash
python3 agent.py --spec dummy_spec.md
```

Expected result:

- process exits cleanly
- `state.json` exists
- `agent_logs/` exists
- `workspace/` exists

You may see this warning:

```text
DeprecationWarning: datetime.datetime.utcnow() is deprecated
```

This is only a warning and does not mean the run failed.

### 3. State Verification

Run:

```bash
python3 -m json.tool state.json
```

Expected state values:

```json
"done": true
```

and:

```json
"stop_reason": "stub model - exiting immediately"
```

This confirms that the stub model returned a stop action and the orchestrator exited cleanly.

### 4. Resume Test

Run:

```bash
python3 agent.py --resume
```

Expected result:

- process exits cleanly
- existing `state.json` is loaded
- no new spec is required

This confirms resume plumbing works.

### 5. Intervention Log Test

Run:

```bash
python3 agent.py --log-intervention "manual smoke test note"
```

Then inspect:

```bash
cat agent_logs/human_interventions.log
```

Expected result:

- the message appears in `human_interventions.log`

This confirms human intervention logging works.

## Clean Reset

To rerun the smoke test from a clean state, remove generated runtime outputs:

```bash
rm -rf state.json state.json.tmp agent_logs workspace __pycache__
```

Then run again:

```bash
python3 agent.py --spec dummy_spec.md
```

## Current Test Status

The smoke test has been run successfully with:

```bash
python3 agent.py --spec dummy_spec.md
```

Result:

- exit code `0`
- `state.json` created
- all expected log files created
- orchestrator entered the loop
- stub model returned `stop`
- orchestrator exited cleanly

## Next Steps

Replace the stub modules one at a time with real implementations:

1. Replace `model.py` with the real `call_model(...)` wrapper.
2. Replace `tools.py` with sandboxed implementations.
3. Expand `context.py` to provide useful prompts.
4. Keep `logger.py` compatible with the expected logger names.

After each replacement, rerun the same smoke tests before adding more complexity.
