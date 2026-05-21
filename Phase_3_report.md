# Phase 3 Report - Tools Layer

## What Was Built

Phase 3 replaced the temporary `tools.py` stub with a real sandboxed tools layer for the orchestrator.

The implemented functions are:

```python
read_file(path: str) -> str
edit_file(path: str, content: str) -> dict
list_dir(path: str = "workspace/") -> list[str]
run_shell(cmd: str, timeout: int = 60, cwd: str = "workspace/") -> dict
run_tests() -> dict
```

These are the exact functions `agent.py` imports and calls when executing model decisions.

## Core Behavior

All file-oriented operations are sandboxed to `workspace/`.

The helper `_safe_path(path)` resolves the requested path, follows symlinks, collapses `..` segments, and rejects anything outside the resolved `workspace/` directory with `PermissionError`.

The helper `_safe_cmd(cmd)` rejects obvious unsafe shell commands before they reach `subprocess.run`, including:

- parent-directory escapes like `../`
- `cd ..`
- `rm -rf /`
- `rm -rf ~`
- references to protected absolute paths such as `/etc`, `/usr`, `/bin`, `/sbin`, `/var`, `/root`, and `/home`
- redirects to absolute paths
- forbidden patterns inside command substitutions

## Function Details

`read_file`:

- Reads UTF-8 text files inside `workspace/`.
- Prepends one-based line numbers in the required format.
- Raises `FileNotFoundError` for missing files.
- Rejects sandbox escapes.
- Returns a clear error string for non-UTF-8 files.

`edit_file`:

- Writes files inside `workspace/`.
- Creates parent directories as needed.
- Returns `success`, `bytes_written`, and `diff_summary`.
- Distinguishes between created files and overwritten files.
- Logs write summaries without logging file contents.

`list_dir`:

- Lists entries inside a sandboxed directory.
- Returns sorted relative names.
- Skips hidden files.
- Returns an empty list for missing directories.

`run_shell`:

- Runs commands with `subprocess.run`.
- Always uses a timeout.
- Captures stdout and stderr.
- Forces `cwd` through `_safe_path`.
- Logs command, exit code, duration, and short output previews.
- Returns timeout results with `exit_code=-1`.

`run_tests`:

- Reads `agent_manifest.json` for a `test_command` when present.
- Defaults to `python -m pytest -v` when no manifest command is configured.
- Runs the command through `run_shell` with a 120-second timeout.
- Parses pytest-style output such as `5 passed, 2 failed`.
- Also handles `unittest` output such as `Ran 1 test ... OK`, which was needed because this environment does not have pytest installed.
- Handles missing pytest or missing `python` command without crashing.
- Logs raw test output to `test_runs.log`.
- Logs a compact summary to `commands.log`.

## Logging Integration

`tools.py` now imports the Phase 2 logger:

```python
from logger import get_iteration, get_logger
```

It writes to:

- `commands.log` for `edit_file`, `run_shell`, and `run_tests` summaries.
- `test_runs.log` for raw test command output.
- `errors.log` for sandbox rejections and exceptions.

The tool layer does not log full edited file contents, which keeps logs readable and avoids noisy output.

## How This Adds To `agent.py`

`agent.py` did not need to change.

Before Phase 3, the orchestrator could call `read_file`, `edit_file`, `list_dir`, `run_shell`, and `run_tests`, but those functions were placeholders. After Phase 3, the same execution paths in `agent.py` now have real behavior:

- `read_file` decisions can inspect workspace files safely.
- `edit_file` decisions can create or overwrite generated code inside `workspace/`.
- `list_dir` decisions can inspect sandbox contents.
- `run_shell` decisions can execute safe shell commands inside `workspace/`.
- `run_tests` decisions can run the generated project's test command and produce structured results.

The most important upgrade is sandbox enforcement. Even if a future model decision tries to read `../agent.py`, edit `/tmp/evil.txt`, list `/etc`, or run `rm -rf /`, the tool layer rejects it before filesystem or shell execution.

## Test Coverage Added

Phase 3 added `test_tools.py` with 17 `unittest` cases covering:

- `read_file` happy path with line numbers.
- `read_file` missing file behavior.
- `edit_file` create behavior.
- `edit_file` overwrite behavior.
- `list_dir` sorting and hidden-file filtering.
- `run_shell("echo hello")`.
- shell timeout behavior.
- stderr capture.
- `run_tests` missing pytest behavior.
- `run_tests` happy path using a temporary `unittest` manifest command.
- read sandbox rejection.
- edit sandbox rejection.
- list sandbox rejection.
- shell parent-directory rejection.
- shell `rm -rf /` rejection.
- symlink escape rejection.
- missing directory listing returning an empty list.

## Verification Results

Commands run:

```bash
python3 test_tools.py
python3 test_logger.py
python3 -m py_compile tools.py test_tools.py logger.py test_logger.py
python3 -c "from tools import read_file; print(read_file('../agent.py'))"
python3 -c "from tools import run_shell; print(run_shell('ls -la'))"
rm -rf agent_logs state.json
python3 agent.py --spec dummy_spec.md
python3 -c "from tools import run_shell; print(run_shell('echo hello'))"
```

Results:

- `test_tools.py` passes all 17 tests.
- `test_logger.py` still passes.
- `tools.py`, `test_tools.py`, `logger.py`, and `test_logger.py` compile successfully.
- Manual sandbox escape check raises `PermissionError`.
- `run_shell("ls -la")` returns a successful result from inside `workspace/`.
- `run_shell("echo hello")` returns:

```python
{"stdout": "hello\n", "stderr": "", "exit_code": 0, ...}
```

- `python3 agent.py --spec dummy_spec.md` exits with code `0`.

Known verification note:

- The orchestrator smoke test still does not naturally call `edit_file`, `run_shell`, or `run_tests`, because `model.py` is still a stub and immediately returns `stop`. The tools layer itself is verified through `test_tools.py` and direct manual checks.
- The smoke run still prints the existing `datetime.utcnow()` deprecation warning from `agent.py`. It does not cause failure.

## Current General Status

The agent now has:

- A functional orchestrator shell in `agent.py`.
- A real structured logging layer in `logger.py`.
- A real sandboxed tools layer in `tools.py`.
- Unit tests for the logger and tools layers.

Remaining stub modules:

- `model.py`: still returns a canned plan and immediate `stop`.
- `context.py`: still builds minimal placeholder prompts.

The project can now safely perform real workspace operations once the model/context layers begin producing meaningful decisions. The main missing pieces are the real model wrapper and stronger prompt/context construction.

## Next Recommended Phase

Phase 4 should replace `model.py` with a real model client wrapper.

After that, Phase 5 should replace `context.py` with richer prompt construction and trajectory summarization. Once those are in place, the project can run an end-to-end dry run against a real dummy spec using the real orchestrator, logger, tools, model, and context layers together.
