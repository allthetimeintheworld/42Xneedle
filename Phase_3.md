# Phase 3 — Build `tools.py`

## Status check before starting

Before opening Codex, confirm:

- [ ] `agent.py` exists and the orchestrator smoke test passes
- [ ] `logger.py` is the real implementation (Phase 2 complete), not the stub
- [ ] `test_logger.py` passes
- [ ] `python agent.py --spec dummy_spec.md` still exits 0 with the real logger in place
- [ ] `tools.py` is still the temporary stub from the setup phase

If any of those are not true, stop and fix them first. Phase 3 assumes a working orchestrator and a working logger.

## What you're building in this phase

The tool layer — the functions the agent uses to interact with a sandboxed workspace directory. The orchestrator calls these functions to read files, write files, list directories, run shell commands, and run tests against the code the agent produces.

**The single most important property of this module is sandbox enforcement.** The agent is an autonomous loop driven by a language model. If the model decides to do something stupid (delete your home directory, exfiltrate environment variables, edit `agent.py` itself), the tools layer must refuse before anything reaches the filesystem.

## Files this phase produces

- `tools.py` — replaces the existing stub
- `test_tools.py` — verification suite, runnable as `python test_tools.py`

No other files are modified. `agent.py`, `logger.py`, `model.py`, `context.py` stay untouched.

## How to run this phase

1. Open a terminal in your project root.
2. Run `codex` to start a CLI session in the current directory.
3. Paste the brief below as your first message.
4. Codex will ask clarifying questions before writing — answer them.
5. Approve file writes and command executions one at a time for the first session.
6. After Codex declares done, run the integration check yourself (see "Verification" below).

---

## Codex CLI Brief — Build `tools.py`

### Rules for this session

1. The file you build is `tools.py` in the current directory. There is already a stub `tools.py` in place — replace it entirely.
2. Match the function signatures in the existing `agent.py` exactly. Do not change `agent.py`.
3. Do not add third-party dependencies. Standard library only.
4. Use the existing `logger.py` for logging — import `get_logger` from it.
5. Before declaring done, write a small `test_tools.py` and run it to confirm each function works in isolation.
6. After tests pass, re-run `python agent.py --spec dummy_spec.md` to confirm the orchestrator still works with the real tools layer in place.
7. Ask clarifying questions before writing code if anything is ambiguous.

### Task

Build the tools layer for an autonomous coding agent. These are the functions the agent uses to interact with a sandboxed workspace directory. The orchestrator (`agent.py`) calls these functions to read files, write files, list directories, run shell commands, and run tests against the code the agent produces.

All file operations must be **sandboxed to `workspace/`** — the agent must not be able to read or write files outside this directory, even if it tries via relative paths, symlinks, or shell tricks.

### Function signatures

```python
def read_file(path: str) -> str:
    """Read a file from the workspace. Returns the contents with line numbers prepended (format: '   1\t<line>\n   2\t<line>\n...'). Refuses paths outside workspace/."""

def edit_file(path: str, content: str) -> dict:
    """Write content to a file in the workspace. Creates parent directories if needed. Returns {'success': bool, 'bytes_written': int, 'diff_summary': str}. Refuses paths outside workspace/."""

def list_dir(path: str = "workspace/") -> list[str]:
    """List entries in a directory. Returns a list of relative paths, sorted. Refuses paths outside workspace/. Skips hidden files (those starting with '.')."""

def run_shell(cmd: str, timeout: int = 60, cwd: str = "workspace/") -> dict:
    """Run a shell command via subprocess. Returns {'stdout': str, 'stderr': str, 'exit_code': int, 'duration_s': float}. Must always have a timeout. Captures both stdout and stderr. Refuses unsafe commands."""

def run_tests() -> dict:
    """Run the test suite for the agent's generated code. Returns {'passed': int, 'failed': int, 'errors': int, 'failure_summary': str, 'raw_output': str}. Reads the test command from agent_manifest.json (key: 'test_command'); defaults to 'python -m pytest -v' if not set."""
```

### Sandbox enforcement

Implement a helper `_safe_path(path: str) -> Path` that:

1. Resolves the path against `workspace/` if relative.
2. Calls `.resolve()` to collapse `..` segments and follow symlinks.
3. Raises `PermissionError(f"path outside sandbox: {path}")` if the resolved path is not inside the absolute resolved path of `workspace/`.

Every function that takes a `path` argument must call `_safe_path` first.

For `run_shell`: implement `_safe_cmd(cmd: str) -> None` that raises `PermissionError` if the command contains any of:

- `cd ..` (with or without spaces)
- `rm -rf /` or `rm -rf ~`
- Absolute paths starting with `/etc`, `/usr`, `/bin`, `/sbin`, `/var`, `/root`, `/home` (except `/home` followed by nothing meaningful)
- `> /` redirects to absolute paths outside the workspace
- `..` path segments that escape `workspace/`
- Backticks or `$(...)` command substitution involving forbidden patterns

Implement these as simple substring checks. Don't try to be clever with full shell parsing — that's a rabbit hole. The goal is "refuses the obvious bad stuff," not "bulletproof against a determined attacker."

### Logging

Use the project's logger:

```python
from logger import get_logger
commands_log = get_logger("commands")
test_runs_log = get_logger("test_runs")
errors_log = get_logger("errors")
```

Log every call:

- `edit_file`: log path and bytes written. Do not log file contents (too noisy).
- `run_shell`: log the full command, exit code, duration, first 500 chars of stdout, first 500 chars of stderr.
- `run_tests`: log the full raw output to `test_runs.log` with a separator line `--- iter N ---` before each run (use the iteration from the logger module). Log a one-line summary to `commands.log`.
- Sandbox rejections: log to `errors.log` with the attempted path/command and the reason.

### Implementation details

**`read_file`**: Use `Path.read_text()`. Prepend line numbers using `enumerate(lines, start=1)` with format `f"{i:>4}\t{line}"`. If the file doesn't exist, raise `FileNotFoundError`. Handle binary files gracefully — wrap the read in try/except for `UnicodeDecodeError` and return a clear error message.

**`edit_file`**: Use `Path.parent.mkdir(parents=True, exist_ok=True)` then `Path.write_text(content)`. For `diff_summary`, return `f"wrote {len(content)} bytes to {path}"`. If the file already exists, the summary can note `"overwrote existing file"` vs `"created new file"`.

**`list_dir`**: Use `Path.iterdir()`. Return entries as strings (relative to the requested path), sorted alphabetically. Skip hidden files. If the path doesn't exist, return an empty list rather than raising.

**`run_shell`**: Use `subprocess.run` with these arguments:

```python
subprocess.run(
    cmd,
    shell=True,
    capture_output=True,
    text=True,
    timeout=timeout,
    cwd=cwd,
)
```

Catch `subprocess.TimeoutExpired` and return:

```python
{"stdout": "", "stderr": f"timeout after {timeout}s", "exit_code": -1, "duration_s": float(timeout)}
```

Time the call with `time.monotonic()` to get `duration_s`. The `cwd` argument must also pass through `_safe_path` to prevent escape.

**`run_tests`**: Read `agent_manifest.json` to get the test command. If the file doesn't exist or doesn't contain `test_command`, default to `python -m pytest -v`. Run via `run_shell` with a 120-second timeout.

Parse pytest output for pass/fail/error counts using regex on the summary line. Common patterns:

- `"5 passed, 2 failed"` → `passed=5, failed=2, errors=0`
- `"3 failed, 7 passed, 1 error"` → `passed=7, failed=3, errors=1`
- `"10 passed"` → `passed=10, failed=0, errors=0`
- `"no tests ran"` → all zeros

For `failure_summary`, extract the first 3 failure blocks (lines starting with `FAILED` or `ERROR`) and join with newlines, max 1000 chars total.

If pytest isn't available, the function should still work — return zeros with `failure_summary="test runner not found"` and `raw_output` containing the actual command output. Do not crash.

### Test file: `test_tools.py`

Write tests that cover:

1. **Setup**: Create a temporary workspace directory (`workspace/test_sandbox/`), remove it in `tearDown`.
2. **`read_file` happy path**: Create a file with known content, read it, assert line numbers are correctly prepended.
3. **`read_file` missing**: Confirm `FileNotFoundError` raised on missing files.
4. **`edit_file` create**: Write to a new path, confirm file exists with correct content, parent dirs created.
5. **`edit_file` overwrite**: Write again to the same path, confirm `diff_summary` reflects overwrite.
6. **`list_dir`**: Create several files, list them, assert sorted order and hidden files skipped.
7. **`run_shell` happy path**: Run `echo hello`, assert stdout, exit_code=0, duration > 0.
8. **`run_shell` timeout**: Run `sleep 5` with `timeout=1`, assert exit_code=-1 and stderr mentions timeout.
9. **`run_shell` stderr capture**: Run a command that writes to stderr, confirm capture works.
10. **`run_tests` no pytest**: With no test files in workspace, confirm function returns zeros without crashing.
11. **`run_tests` happy path**: Create a tiny passing pytest file in workspace, run, assert passed > 0.
12. **Sandbox: read**: `read_file("../agent.py")` raises `PermissionError`.
13. **Sandbox: edit**: `edit_file("/tmp/evil.txt", "x")` raises `PermissionError`.
14. **Sandbox: list**: `list_dir("/etc")` raises `PermissionError`.
15. **Sandbox: shell escape**: `run_shell("cat ../agent.py")` raises `PermissionError`.
16. **Sandbox: shell rm**: `run_shell("rm -rf /")` raises `PermissionError`.
17. **Sandbox: symlink**: Create a symlink inside workspace pointing outside, attempt to read through it, confirm rejection.

Use Python's `unittest` module (it's stdlib) — no pytest dependency for the tests themselves.

The test file should be runnable as `python test_tools.py` and exit 0 on success.

### What this file must NOT do

- Must not import any third-party packages.
- Must not write outside `workspace/`, `agent_logs/`, or read-only access to `agent_manifest.json`.
- Must not call language models.
- Must not modify `agent.py` or any other module.
- Must not use `os.system` or `os.popen` — only `subprocess.run`.
- Must not have any `subprocess.run` calls without a timeout.
- Must not silently swallow exceptions — log them to `errors.log` before re-raising.

### Definition of done

- `tools.py` exists, all five functions implemented.
- `test_tools.py` exists and passes when run as `python test_tools.py`.
- All 17 test cases pass.
- The sandbox rejects `read_file("../agent.py")` with `PermissionError`.
- `run_shell("echo hello")` returns `{"stdout": "hello\n", "stderr": "", "exit_code": 0, ...}`.
- `python agent.py --spec dummy_spec.md` still exits 0 with the real `tools.py` in place.
- File length: 200–300 lines.

---

## Verification (you, after Codex finishes)

Do not skip these. They take 5 minutes and catch the bugs Codex won't.

1. **Run the unit tests**:
   ```bash
   python test_tools.py
   ```
   All tests must pass. If any fail, paste the failure into Codex and ask for a fix.

2. **Manual sandbox check** — try to escape the sandbox from a Python REPL:
   ```bash
   python -c "from tools import read_file; print(read_file('../agent.py'))"
   ```
   This must raise `PermissionError`. If it doesn't, the sandbox is broken — fix before continuing.

3. **Run a real shell command**:
   ```bash
   python -c "from tools import run_shell; print(run_shell('ls -la'))"
   ```
   You should see a dict with `workspace/` directory contents and `exit_code: 0`.

4. **Run the orchestrator smoke test**:
   ```bash
   rm -rf agent_logs state.json
   python agent.py --spec dummy_spec.md
   ```
   Must exit 0. Inspect `agent_logs/commands.log` — it should now have real log entries from `tools.py`, not stub entries.

5. **Inspect a log file**:
   ```bash
   cat agent_logs/commands.log
   ```
   Lines should be timestamped, prefixed with iteration number, and human-readable. If they're cryptic, push back on Codex.

## What can go wrong in this phase

- **Sandbox is too strict**: legitimate workspace operations get blocked. Symptom: every `edit_file` call returns `success: False`. Fix: check that the workspace path resolves correctly and `_safe_path` isn't rejecting valid relative paths.

- **Sandbox is too loose**: the manual escape check above succeeds when it shouldn't. Fix: ensure `.resolve()` is called and the comparison is against the resolved absolute workspace path, not a string prefix.

- **Tests hang**: probably a `subprocess.run` without a timeout. Find it and add one.

- **`run_tests` returns zeros even when tests passed**: regex doesn't match your version of pytest's output. Print the raw output, adjust the regex.

- **Logger imports cause circular dependency**: shouldn't happen with the planned module structure, but if it does, the fix is to import `get_logger` inside each function rather than at module top.

## After Phase 3

Once `tools.py` is solid and the orchestrator smoke test still passes:

- **Phase 4** is `model.py` — the wrapper around Gemini and Groq free-tier APIs. This is when you'll need your API keys ready and your `.env` file set up.
- **Phase 5** is `context.py` — the prompt builder. Hardest module conceptually; save it for last.
- **Phase 6** is the end-to-end dry run on a real dummy spec, with all real modules in place.

Keep going. The skeleton is the hard part and you're past it.
