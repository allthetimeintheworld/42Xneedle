import json
import re
import subprocess
import time
from pathlib import Path

from logger import get_iteration, get_logger


WORKSPACE = Path("workspace")
MANIFEST = Path("agent_manifest.json")

WORKSPACE.mkdir(exist_ok=True)


def _workspace_root() -> Path:
    return WORKSPACE.resolve()


def _preview(text: str, limit: int = 500) -> str:
    value = text.replace("\n", "\\n")
    return value[:limit]


def _safe_path(path: str) -> Path:
    raw = Path(path)
    if raw.is_absolute():
        candidate = raw
    elif raw.parts and raw.parts[0] == WORKSPACE.name:
        candidate = raw
    else:
        candidate = WORKSPACE / raw

    resolved = candidate.resolve()
    root = _workspace_root()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        reason = f"path outside sandbox: {path}"
        get_logger("errors").error(reason)
        raise PermissionError(reason) from exc
    return resolved


def _safe_cmd(cmd: str) -> None:
    compact = re.sub(r"\s+", "", cmd)
    forbidden = [
        "cd..",
        "rm-rf/",
        "rm-rf~",
        "`",
    ]
    absolute_prefixes = ("/etc", "/usr", "/bin", "/sbin", "/var", "/root", "/home")

    reason = None
    if any(item in compact for item in forbidden):
        reason = "command contains forbidden shell pattern"
    elif "$(" in cmd and any(prefix in cmd for prefix in absolute_prefixes + ("..", "rm -rf")):
        reason = "command substitution contains forbidden pattern"
    elif re.search(r"(^|\s)>\s*/", cmd):
        reason = "command redirects to an absolute path"
    elif ".." in Path(cmd.replace("\\", "/")).parts or "../" in cmd or "..\\" in cmd:
        reason = "command contains parent-directory escape"
    else:
        for prefix in absolute_prefixes:
            if re.search(rf"(^|[\s'\"]){re.escape(prefix)}(?:/|\s|$)", cmd):
                reason = f"command references forbidden absolute path: {prefix}"
                break

    if reason:
        get_logger("errors").error("sandbox rejected command=%s reason=%s", cmd, reason)
        raise PermissionError(reason)


def read_file(path: str) -> str:
    """Read a workspace file and prepend one-based line numbers."""
    safe = _safe_path(path)
    try:
        text = safe.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return f"error: file is not valid UTF-8: {path}"
    except Exception:
        get_logger("errors").exception("read_file failed path=%s", path)
        raise

    lines = text.splitlines(keepends=True)
    if not lines:
        return ""
    return "".join(f"{i:>4}\t{line}" for i, line in enumerate(lines, start=1))


def edit_file(path: str, content: str) -> dict:
    """Write content to a workspace file, creating parent directories."""
    safe = _safe_path(path)
    existed = safe.exists()
    try:
        safe.parent.mkdir(parents=True, exist_ok=True)
        safe.write_text(content, encoding="utf-8")
    except Exception:
        get_logger("errors").exception("edit_file failed path=%s", path)
        raise

    bytes_written = len(content.encode("utf-8"))
    action = "overwrote existing file" if existed else "created new file"
    summary = f"{action}; wrote {len(content)} bytes to {path}"
    get_logger("commands").info(
        "edit_file path=%s bytes_written=%s summary=%s",
        path,
        bytes_written,
        summary,
    )
    return {"success": True, "bytes_written": bytes_written, "diff_summary": summary}


def list_dir(path: str = "workspace/") -> list[str]:
    """List non-hidden entries in a workspace directory."""
    safe = _safe_path(path)
    if not safe.exists():
        return []
    if not safe.is_dir():
        raise NotADirectoryError(path)

    entries = []
    for item in safe.iterdir():
        if item.name.startswith("."):
            continue
        entries.append(str(item.relative_to(safe)))
    return sorted(entries)


def run_shell(cmd: str, timeout: int = 60, cwd: str = "workspace/") -> dict:
    """Run a shell command in the sandbox with captured output and a timeout."""
    _safe_cmd(cmd)
    safe_cwd = _safe_path(cwd)
    start = time.monotonic()

    try:
        completed = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=safe_cwd,
        )
        duration = time.monotonic() - start
        result = {
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "exit_code": completed.returncode,
            "duration_s": duration,
        }
    except subprocess.TimeoutExpired:
        result = {
            "stdout": "",
            "stderr": f"timeout after {timeout}s",
            "exit_code": -1,
            "duration_s": float(timeout),
        }
    except Exception:
        get_logger("errors").exception("run_shell failed cmd=%s", cmd)
        raise

    get_logger("commands").info(
        "run_shell cmd=%s exit_code=%s duration_s=%.3f stdout=%s stderr=%s",
        cmd,
        result["exit_code"],
        result["duration_s"],
        _preview(result["stdout"]),
        _preview(result["stderr"]),
    )
    return result


def _test_command() -> str:
    if not MANIFEST.exists():
        return "python -m pytest -v"
    try:
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except Exception:
        get_logger("errors").exception("could not read agent_manifest.json")
        return "python -m pytest -v"
    command = data.get("test_command")
    return command if isinstance(command, str) and command.strip() else "python -m pytest -v"


def _parse_counts(output: str) -> tuple[int, int, int]:
    if "no tests ran" in output.lower():
        return 0, 0, 0

    unittest_ran = re.search(r"Ran (\d+) tests?", output)
    if unittest_ran and re.search(r"^OK\b", output, re.MULTILINE):
        return int(unittest_ran.group(1)), 0, 0

    passed = failed = errors = 0
    summary_lines = [
        line for line in output.splitlines()
        if re.search(r"\b(passed|failed|error|errors)\b", line)
    ]
    for line in reversed(summary_lines[-5:]):
        for count, label in re.findall(r"(\d+)\s+(passed|failed|errors?|error)\b", line):
            value = int(count)
            if label == "passed":
                passed = max(passed, value)
            elif label == "failed":
                failed = max(failed, value)
            elif label in {"error", "errors"}:
                errors = max(errors, value)
        if passed or failed or errors:
            break
    return passed, failed, errors


def _failure_summary(output: str) -> str:
    lines = []
    for line in output.splitlines():
        if line.startswith("FAILED") or line.startswith("ERROR"):
            lines.append(line)
        if len(lines) >= 3:
            break
    return "\n".join(lines)[:1000]


def run_tests() -> dict:
    """Run the generated code test suite and parse a compact result summary."""
    cmd = _test_command()
    result = run_shell(cmd, timeout=120)
    raw_output = result["stdout"] + result["stderr"]

    if (
        "No module named pytest" in raw_output
        or "pytest: command not found" in raw_output
        or "python: command not found" in raw_output
    ):
        passed = failed = errors = 0
        summary = "test runner not found"
    else:
        passed, failed, errors = _parse_counts(raw_output)
        summary = _failure_summary(raw_output)

    iter_str = get_iteration() if get_iteration() >= 0 else "-"
    get_logger("test_runs").info("--- iter %s ---\n%s", iter_str, raw_output)
    get_logger("commands").info(
        "run_tests cmd=%s exit_code=%s passed=%s failed=%s errors=%s",
        cmd,
        result["exit_code"],
        passed,
        failed,
        errors,
    )
    return {
        "passed": passed,
        "failed": failed,
        "errors": errors,
        "failure_summary": summary,
        "raw_output": raw_output,
    }
