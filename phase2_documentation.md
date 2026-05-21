# Phase 2 Documentation - Logging Layer

## Purpose

Phase 2 built the logging system for the agent.

The agent runs as a loop: it asks the model what to do, executes one action, records what happened, and repeats. Without logs, it is hard to understand why the agent made a decision or why it failed. The logging layer is the audit trail for that loop.

The implemented file is:

```text
logger.py
```

The test file is:

```text
test_logger.py
```

## Public API

`logger.py` exposes four functions:

```python
get_logger(name: str) -> logging.Logger
log_intervention(message: str) -> None
set_iteration(n: int) -> None
get_iteration() -> int
```

`agent.py` already imports and uses `get_logger()` and `log_intervention()`. The logger was built around those existing call sites, so `agent.py` did not need to change.

## Log Files

All logs live in:

```text
agent_logs/
```

The main logger names are:

```text
prompts
decisions
commands
test_runs
errors
```

Each logger writes to a matching file:

```text
agent_logs/prompts.log
agent_logs/decisions.log
agent_logs/commands.log
agent_logs/test_runs.log
agent_logs/errors.log
```

Human intervention messages use a separate file:

```text
agent_logs/human_interventions.log
```

## Log Format

Normal log lines use this format:

```text
<ISO UTC timestamp> [iter <N>] <message>
```

Example:

```text
2026-05-21T13:16:52.402Z [iter 0] iter 0 decision action=stop args={"reason": "stub model - exiting immediately"} reasoning=stub call_model always stops
```

Human intervention logs intentionally do not include an iteration prefix:

```text
2026-05-21T13:16:58.060Z test
```

## How It Works

`get_logger(name)` validates the logger name, creates `agent_logs/` if needed, and returns a cached Python `logging.Logger`.

Caching matters because repeated calls like this:

```python
get_logger("prompts")
get_logger("prompts")
```

must return the same logger without adding duplicate file handlers. Without caching, each log call could be written multiple times.

The logger uses:

- one file handler per logger
- UTF-8 output
- append mode
- no propagation to the root logger
- flushing after each write

Flushing means the files can be read while the agent is still running.

## Iteration Handling

The logger supports:

```python
set_iteration(n)
get_iteration()
```

These store the current loop iteration in module-level state. If no iteration has been set, logs show:

```text
[iter -]
```

The current `agent.py` does not yet call `set_iteration()`. To keep logs useful anyway, the formatter can recover an `iter N` prefix from messages that already include it. This compatibility behavior lets current logs show `[iter 0]` without modifying `agent.py`.

## How It Adds To `agent.py`

`agent.py` uses logs in these places:

- planning prompt metadata goes to `prompts.log`
- planning results go to `decisions.log`
- model decisions go to `decisions.log`
- guardrail rejections go to `decisions.log`
- edit, shell, and test commands go to `commands.log`
- test run details go to `test_runs.log`
- parse failures, timeouts, and crashes go to `errors.log`
- manual notes go to `human_interventions.log`

Phase 2 turned these existing logging calls from stub output into structured, timestamped files.

## Tests

`test_logger.py` verifies:

- `agent_logs/` is created on import
- timestamps are ISO UTC
- `[iter -]` appears before an iteration is set
- `set_iteration(5)` makes logs show `[iter 5]`
- logger caching returns the same object
- duplicate handlers are not added
- human intervention logs have no iteration prefix
- invalid logger names raise `ValueError`
- `logger.exception(...)` writes tracebacks

Run it with:

```bash
python3 test_logger.py
```

## Verification Status

Phase 2 passed:

```bash
python3 test_logger.py
python3 -m py_compile logger.py test_logger.py
python3 agent.py --spec dummy_spec.md
python3 agent.py --log-intervention test
```

The only known caveat is that `commands.log` and `test_runs.log` can be empty during a stub-model smoke test, because the stub model stops before any command or test action is executed.
