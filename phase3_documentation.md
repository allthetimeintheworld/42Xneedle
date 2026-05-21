# Phase 3 Documentation - Tools Layer

## Purpose

Phase 3 built the tool layer.

The tool layer is how the agent interacts with the generated-code workspace. It can read files, write files, list directories, run shell commands, and run tests.

The critical property is sandboxing. The model may suggest unsafe actions. The tool layer must reject those actions before they reach the filesystem or shell.

The implemented file is:

```text
tools.py
```

The test file is:

```text
test_tools.py
```

## Public API

`tools.py` exposes five functions used by `agent.py`:

```python
read_file(path: str) -> str
edit_file(path: str, content: str) -> dict
list_dir(path: str = "workspace/") -> list[str]
run_shell(cmd: str, timeout: int = 60, cwd: str = "workspace/") -> dict
run_tests() -> dict
```

`agent.py` dispatches model decisions to these functions.

## Sandbox Rule

All file operations are restricted to:

```text
workspace/
```

The helper `_safe_path(path)`:

1. resolves relative paths against `workspace/`
2. resolves `..` segments
3. follows symlinks
4. checks that the final path is still inside `workspace/`
5. raises `PermissionError` if not

This blocks attempts such as:

```python
read_file("../agent.py")
edit_file("/tmp/evil.txt", "x")
list_dir("/etc")
```

It also blocks symlinks inside `workspace/` that point outside the sandbox.

## Shell Safety

`run_shell()` uses `_safe_cmd(cmd)` before executing anything.

The command checker rejects obvious unsafe patterns, including:

- `../`
- `cd ..`
- `rm -rf /`
- `rm -rf ~`
- references to protected absolute paths like `/etc`, `/usr`, `/bin`, `/sbin`, `/var`, `/root`, and `/home`
- redirects to absolute paths
- risky command substitutions

The shell checker is not intended to be a perfect security sandbox. It is a practical guardrail that refuses the obvious bad actions an autonomous model might propose.

## Function Behavior

### `read_file`

Reads a UTF-8 file inside `workspace/` and prepends line numbers.

Example output:

```text
   1	print("hello")
   2	print("world")
```

Missing files raise `FileNotFoundError`. Binary or invalid UTF-8 files return a clear error string.

### `edit_file`

Creates or overwrites a file inside `workspace/`.

It returns:

```python
{
    "success": True,
    "bytes_written": 12,
    "diff_summary": "created new file; wrote 12 bytes to main.py"
}
```

It creates parent directories when needed and logs the write summary without logging file contents.

### `list_dir`

Lists a sandboxed directory.

It returns sorted, non-hidden entries. Missing directories return an empty list.

### `run_shell`

Runs a safe shell command inside `workspace/` with:

- `subprocess.run`
- captured stdout
- captured stderr
- a timeout on every call
- duration measurement

Timeouts return:

```python
{
    "stdout": "",
    "stderr": "timeout after 1s",
    "exit_code": -1,
    "duration_s": 1.0
}
```

### `run_tests`

Reads `agent_manifest.json` for:

```json
{"test_command": "..."}
```

If no manifest command exists, it defaults to:

```bash
python -m pytest -v
```

It runs the command through `run_shell()`, parses test counts, and returns:

```python
{
    "passed": 0,
    "failed": 0,
    "errors": 0,
    "failure_summary": "...",
    "raw_output": "..."
}
```

It supports pytest-style summaries and basic unittest output. If pytest is missing, it returns a clean "test runner not found" result instead of crashing.

## Logging

The tools layer logs through Phase 2's logger:

- command summaries go to `agent_logs/commands.log`
- full test output goes to `agent_logs/test_runs.log`
- sandbox rejections and exceptions go to `agent_logs/errors.log`

It avoids logging full edited file contents.

## How It Adds To `agent.py`

Before Phase 3, the orchestrator could call tool functions, but the functions were placeholders.

After Phase 3:

- `read_file` decisions can inspect real workspace files
- `edit_file` decisions can create or overwrite generated code
- `list_dir` decisions can inspect workspace structure
- `run_shell` decisions can execute safe commands
- `run_tests` decisions can run and summarize tests

Most importantly, unsafe model decisions are rejected at the tool boundary.

## Tests

`test_tools.py` has 17 tests covering:

- file reading
- missing files
- file creation
- file overwrite
- directory listing
- hidden file skipping
- shell stdout
- shell stderr
- shell timeout
- test runner handling
- sandbox escapes
- symlink escapes

Run it with:

```bash
python3 test_tools.py
```

## Verification Status

Phase 3 passed:

```bash
python3 test_tools.py
python3 test_logger.py
python3 -m py_compile tools.py test_tools.py logger.py test_logger.py
python3 -c "from tools import read_file; print(read_file('../agent.py'))"
python3 -c "from tools import run_shell; print(run_shell('echo hello'))"
python3 agent.py --spec dummy_spec.md
```

The manual escape check raises `PermissionError`, and `run_shell("echo hello")` returns stdout `hello\n` with exit code `0`.
