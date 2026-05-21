import argparse
import json
import os
import sys
import time
import hashlib
from datetime import datetime
from pathlib import Path
import traceback

from model import call_model
from tools import read_file, edit_file, list_dir, run_shell, run_tests
from context import build_context, build_planning_prompt, summarize_trajectory
from logger import get_logger, log_intervention


STATE_FILE = "state.json"
STATE_TMP_FILE = "state.json.tmp"
WORKSPACE_DIR = "workspace"
LOG_DIR = "agent_logs"
RECENT_ACTION_LIMIT = 8
FINGERPRINT_LIMIT = 20
ITERATION_SOFT_TIMEOUT_S = 180

ALLOWED_ACTIONS = {
    "read_file",
    "edit_file",
    "list_dir",
    "run_shell",
    "run_tests",
    "stop",
}

SYSTEM_DIR_PREFIXES = (
    "/bin",
    "/boot",
    "/dev",
    "/etc",
    "/lib",
    "/lib64",
    "/proc",
    "/root",
    "/sbin",
    "/sys",
    "/usr",
    "/var",
    "/private/etc",
    "/private/var",
)


def utc_now() -> str:
    """Return the current UTC time as an ISO-8601 string.
    Returns a timestamp string ending in Z.
    """
    return datetime.utcnow().isoformat() + "Z"


def preview(text: object, limit: int = 200) -> str:
    """Create a compact single-line preview of text for logs.
    Returns a string no longer than the requested limit plus an ellipsis.
    """
    value = str(text).replace("\n", "\\n")
    if len(value) <= limit:
        return value
    return value[:limit] + "..."


def ensure_runtime_dirs() -> None:
    """Create runtime directories that the orchestrator is allowed to use.
    Returns None.
    """
    Path(WORKSPACE_DIR).mkdir(exist_ok=True)
    Path(LOG_DIR).mkdir(exist_ok=True)


def ensure_log_files() -> None:
    """Ensure expected log files exist for fresh runs and definition-of-done checks.
    Returns None.
    """
    ensure_runtime_dirs()
    names = [
        "prompts.log",
        "decisions.log",
        "commands.log",
        "test_runs.log",
        "errors.log",
        "human_interventions.log",
    ]
    for name in names:
        path = Path(LOG_DIR) / name
        if not path.exists():
            path.touch()


def initialize_state(spec_path: str, max_iter: int) -> dict:
    """Create a fresh orchestrator state from a specification file.
    Returns the state dictionary matching the required schema.
    """
    spec_text = Path(spec_path).read_text()
    return {
        "iteration": 0,
        "max_iterations": max_iter,
        "spec_path": spec_path,
        "spec_text": spec_text,
        "plan": [],
        "current_step_index": 0,
        "last_test_result": None,
        "recent_actions": [],
        "older_trajectory_summary": "",
        "files_touched": [],
        "started_at": utc_now(),
        "done": False,
        "stop_reason": None,
        "fingerprints": [],
    }


def save_state(state: dict) -> None:
    """Persist state.json using an atomic replacement.
    Returns None.
    """
    with open(STATE_TMP_FILE, "w") as f:
        json.dump(state, f, indent=2, default=str)
    os.replace(STATE_TMP_FILE, STATE_FILE)


def load_state() -> dict:
    """Load persisted state from state.json.
    Returns the decoded state dictionary.
    """
    with open(STATE_FILE, "r") as f:
        return json.load(f)


def log_model_call(
    iteration: int,
    system: str,
    user: str,
    response: str,
    label: str,
) -> None:
    """Log prompt and response metadata for a model call.
    Returns None.
    """
    logger = get_logger("prompts")
    logger.info(
        "iter %s %s system_len=%s user_len=%s response_len=%s "
        "system_preview=%s user_preview=%s response_preview=%s",
        iteration,
        label,
        len(system),
        len(user),
        len(response),
        preview(system),
        preview(user),
        preview(response),
    )


def log_error(iteration: int, message: str) -> None:
    """Log an error message with an iteration number.
    Returns None.
    """
    get_logger("errors").error("iter %s %s", iteration, message)


def parse_json_response(response: str) -> dict:
    """Parse a model JSON response.
    Returns the decoded JSON object.
    """
    parsed = json.loads(response)
    if not isinstance(parsed, dict):
        raise ValueError("model response must be a JSON object")
    return parsed


def run_planner(state: dict) -> None:
    """Ask the model for an implementation plan and store it in state.
    Returns None.
    """
    iteration = state["iteration"]
    system, user = build_planning_prompt(state["spec_text"])
    response = ""
    parsed = None

    for attempt in range(2):
        try:
            response = call_model(system, user, expect_json=True)
            log_model_call(iteration, system, user, response, f"planning_attempt={attempt + 1}")
            parsed = parse_json_response(response)
            break
        except Exception as exc:
            log_error(iteration, f"planning parse failure attempt={attempt + 1}: {exc}")
            if attempt == 1:
                parsed = None

    steps = []
    if parsed is not None:
        raw_steps = parsed.get("steps", [])
        if isinstance(raw_steps, list):
            steps = [str(step) for step in raw_steps]
        else:
            log_error(iteration, "planning response has non-list steps")

    state["plan"] = steps
    get_logger("decisions").info("iter %s planning_result steps=%s", iteration, json.dumps(steps))
    save_state(state)


def normalize_workspace_path(path: str) -> Path:
    """Resolve a tool path against the workspace sandbox.
    Returns an absolute Path.
    """
    raw = Path(path)
    if raw.is_absolute():
        return raw.resolve()
    if path == WORKSPACE_DIR or path.startswith(WORKSPACE_DIR + os.sep):
        return raw.resolve()
    return (Path(WORKSPACE_DIR) / raw).resolve()


def is_path_in_workspace(path: str) -> bool:
    """Check whether a path resolves inside the workspace directory.
    Returns True when the path is inside workspace/.
    """
    workspace = Path(WORKSPACE_DIR).resolve()
    resolved = normalize_workspace_path(path)
    try:
        resolved.relative_to(workspace)
        return True
    except ValueError:
        return False


def workspace_path_exists(path: str) -> bool:
    """Check whether a path exists inside workspace/.
    Returns True when the sandboxed path exists.
    """
    if not is_path_in_workspace(path):
        return False
    return normalize_workspace_path(path).exists()


def action_path(decision: dict) -> str | None:
    """Extract a path argument from an action when one is present.
    Returns a path string or None.
    """
    args = decision.get("args", {})
    action = decision.get("action")
    if action in {"read_file", "edit_file"}:
        return args.get("path")
    if action == "list_dir":
        return args.get("path", "workspace/")
    return None


def command_looks_unsafe(cmd: str) -> bool:
    """Detect command strings that should not be sent to the sandboxed shell.
    Returns True when the command violates orchestrator guardrails.
    """
    normalized = " ".join(cmd.split())
    if "cd .." in normalized or "rm -rf /" in normalized:
        return True
    if "git " in f" {normalized} " or normalized.startswith("git"):
        return True
    for prefix in SYSTEM_DIR_PREFIXES:
        if prefix + "/" in normalized or normalized.endswith(prefix):
            return True
    return False


def validate_schema(decision: dict) -> tuple[bool, str]:
    """Validate the model decision schema.
    Returns (accepted, rejection_reason).
    """
    if not isinstance(decision, dict):
        return False, "decision must be an object"
    for key in ("action", "args", "reasoning"):
        if key not in decision:
            return False, f"missing key: {key}"
    action = decision["action"]
    args = decision["args"]
    if action not in ALLOWED_ACTIONS:
        return False, f"unknown action: {action}"
    if not isinstance(args, dict):
        return False, "args must be an object"
    if not isinstance(decision["reasoning"], str):
        return False, "reasoning must be a string"

    if action == "read_file":
        if not isinstance(args.get("path"), str):
            return False, "read_file requires string path"
    elif action == "edit_file":
        if not isinstance(args.get("path"), str) or not isinstance(args.get("content"), str):
            return False, "edit_file requires string path and content"
    elif action == "list_dir":
        if "path" in args and not isinstance(args.get("path"), str):
            return False, "list_dir path must be a string"
    elif action == "run_shell":
        if not isinstance(args.get("cmd"), str):
            return False, "run_shell requires string cmd"
        if "timeout" in args and not isinstance(args.get("timeout"), int):
            return False, "run_shell timeout must be an integer"
    elif action == "run_tests":
        if args:
            return False, "run_tests args must be empty"
    elif action == "stop":
        if "reason" in args and not isinstance(args.get("reason"), str):
            return False, "stop reason must be a string"

    return True, ""


def check_repeat(decision: dict, state: dict) -> tuple[bool, str]:
    """Reject duplicate action fingerprints.
    Returns (accepted, rejection_reason).
    """
    last_failure = ""
    if state.get("last_test_result"):
        last_failure = state["last_test_result"].get("failure_summary", "")

    payload = {
        "action": decision["action"],
        "args": decision["args"],
        "last_failure": last_failure,
    }
    fingerprint = hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode("utf-8")
    ).hexdigest()[:16]

    if fingerprint in state["fingerprints"]:
        return False, "repeat detected — propose a different approach"

    state["fingerprints"].append(fingerprint)
    state["fingerprints"] = state["fingerprints"][-FINGERPRINT_LIMIT:]
    return True, ""


def check_read_before_edit(decision: dict, state: dict) -> tuple[bool, str]:
    """Require a recent successful read before editing existing files.
    Returns (accepted, rejection_reason).
    """
    if decision["action"] != "edit_file":
        return True, ""

    path = decision["args"]["path"]
    needs_read = path in state["files_touched"] or workspace_path_exists(path)
    if not needs_read:
        return True, ""

    for record in state["recent_actions"][-5:]:
        if (
            record.get("action") == "read_file"
            and record.get("args", {}).get("path") == path
            and record.get("success") is True
        ):
            return True, ""

    return False, "must read existing file before editing it"


def check_path_sandbox(decision: dict) -> tuple[bool, str]:
    """Reject paths and shell commands that leave the sandbox policy.
    Returns (accepted, rejection_reason).
    """
    path = action_path(decision)
    if path is not None and not is_path_in_workspace(path):
        return False, f"path resolves outside workspace: {path}"

    if decision["action"] == "run_shell":
        cmd = decision["args"].get("cmd", "")
        if command_looks_unsafe(cmd):
            return False, "command violates sandbox guardrails"

    if decision["action"] == "edit_file":
        parts = Path(decision["args"]["path"]).parts
        if "tests" in parts or "test" in parts:
            return False, "must not modify files in the test suite"

    return True, ""


def run_guardrails(decision: dict, state: dict) -> tuple[bool, str]:
    """Apply all guardrails in order.
    Returns (accepted, rejection_reason).
    """
    checks = [
        validate_schema,
        lambda item: check_repeat(item, state),
        lambda item: check_read_before_edit(item, state),
        check_path_sandbox,
    ]
    for check in checks:
        accepted, reason = check(decision)
        if not accepted:
            return False, reason
    return True, ""


def log_rejection(iteration: int, decision: dict, reason: str) -> None:
    """Log a guardrail rejection.
    Returns None.
    """
    get_logger("decisions").info(
        "%s iter %s REJECTED action=%s reason=%s reasoning=%s",
        utc_now(),
        iteration,
        decision.get("action"),
        reason,
        decision.get("reasoning", ""),
    )


def summarize_dropped_actions(state: dict, dropped: list[dict]) -> None:
    """Compress older recent actions into the trajectory summary.
    Returns None.
    """
    if not dropped:
        return
    try:
        summary = summarize_trajectory(dropped)
    except Exception as exc:
        summary = f"trajectory summarization failed: {exc}"
    previous = state.get("older_trajectory_summary", "")
    if previous:
        state["older_trajectory_summary"] = previous + "\n" + summary
    else:
        state["older_trajectory_summary"] = summary


def append_action_record(state: dict, decision: dict, result: dict) -> None:
    """Append an action record and cap recent action history.
    Returns None.
    """
    record = {
        "iteration": state["iteration"],
        "timestamp": utc_now(),
        "action": decision["action"],
        "args": decision["args"],
        "reasoning": decision["reasoning"],
        "result_summary": result["summary"],
        "success": result["success"],
    }
    state["recent_actions"].append(record)
    if len(state["recent_actions"]) > RECENT_ACTION_LIMIT:
        overflow = len(state["recent_actions"]) - RECENT_ACTION_LIMIT
        dropped = state["recent_actions"][:overflow]
        state["recent_actions"] = state["recent_actions"][overflow:]
        summarize_dropped_actions(state, dropped)


def execute(decision: dict, state: dict) -> dict:
    """Execute a validated decision through the fixed tool interfaces.
    Returns {'success': bool, 'summary': str}.
    """
    action = decision["action"]
    args = decision["args"]
    iteration = state["iteration"]

    if action == "read_file":
        try:
            content = read_file(args["path"])
            return {"success": True, "summary": f"read {args['path']} ({len(content)} chars)"}
        except Exception as exc:
            return {"success": False, "summary": f"error: {exc}"}

    elif action == "edit_file":
        try:
            result = edit_file(args["path"], args["content"])
            if args["path"] not in state["files_touched"]:
                state["files_touched"].append(args["path"])
            summary = result.get("diff_summary", "")
            get_logger("commands").info(
                "iter %s edit_file path=%s success=%s summary=%s",
                iteration,
                args["path"],
                result.get("success"),
                summary,
            )
            return {"success": bool(result["success"]), "summary": summary}
        except Exception as exc:
            get_logger("commands").info(
                "iter %s edit_file path=%s success=False summary=error: %s",
                iteration,
                args.get("path"),
                exc,
            )
            return {"success": False, "summary": f"error: {exc}"}

    elif action == "list_dir":
        try:
            path = args.get("path", "workspace/")
            files = list_dir(path)
            return {"success": True, "summary": f"{len(files)} entries in {path}"}
        except Exception as exc:
            return {"success": False, "summary": f"error: {exc}"}

    elif action == "run_shell":
        try:
            result = run_shell(args["cmd"], timeout=args.get("timeout", 60))
            summary = f"exit {result['exit_code']} in {result['duration_s']:.1f}s"
            get_logger("commands").info(
                "iter %s run_shell cmd=%s success=%s summary=%s",
                iteration,
                args["cmd"],
                result["exit_code"] == 0,
                summary,
            )
            return {"success": result["exit_code"] == 0, "summary": summary}
        except Exception as exc:
            get_logger("commands").info(
                "iter %s run_shell cmd=%s success=False summary=error: %s",
                iteration,
                args.get("cmd"),
                exc,
            )
            return {"success": False, "summary": f"error: {exc}"}

    elif action == "run_tests":
        try:
            result = run_tests()
            state["last_test_result"] = result
            summary = (
                f"{result['passed']} passed, {result['failed']} failed, "
                f"{result['errors']} errors"
            )
            get_logger("commands").info(
                "iter %s run_tests success=%s summary=%s",
                iteration,
                result["failed"] == 0 and result["errors"] == 0,
                summary,
            )
            get_logger("test_runs").info("iter %s run_tests noted", iteration)
            return {
                "success": result["failed"] == 0 and result["errors"] == 0,
                "summary": summary,
            }
        except Exception as exc:
            get_logger("commands").info(
                "iter %s run_tests success=False summary=error: %s",
                iteration,
                exc,
            )
            return {"success": False, "summary": f"error: {exc}"}

    elif action == "stop":
        state["done"] = True
        state["stop_reason"] = args.get("reason", "model requested stop")
        return {"success": True, "summary": f"stop: {state['stop_reason']}"}

    else:
        raise ValueError(f"unknown action: {action}")


def call_decider(state: dict) -> dict:
    """Build context, call the model, and parse a decision.
    Returns the parsed decision dictionary.
    """
    system, user = build_context(state)
    response = call_model(system, user, expect_json=True)
    log_model_call(state["iteration"], system, user, response, "decision")
    decision = parse_json_response(response)
    get_logger("decisions").info(
        "iter %s decision action=%s args=%s reasoning=%s",
        state["iteration"],
        decision.get("action"),
        json.dumps(decision.get("args", {}), sort_keys=True),
        decision.get("reasoning", ""),
    )
    return decision


def finish_iteration(state: dict, start_time: float) -> None:
    """Persist state and log a warning if an iteration exceeded soft timeout.
    Returns None.
    """
    elapsed = time.monotonic() - start_time
    if elapsed > ITERATION_SOFT_TIMEOUT_S:
        log_error(
            state["iteration"],
            f"iteration exceeded soft timeout: {elapsed:.1f}s",
        )
    save_state(state)


def run_iteration(state: dict) -> None:
    """Run one decide-execute-observe-log iteration.
    Returns None.
    """
    start_time = time.monotonic()

    try:
        decision = call_decider(state)
    except Exception as exc:
        log_error(state["iteration"], f"decision parse/call failure: {exc}")
        state["iteration"] += 1
        finish_iteration(state, start_time)
        return

    accepted, reason = run_guardrails(decision, state)
    if not accepted:
        log_rejection(state["iteration"], decision, reason)
        state["iteration"] += 1
        finish_iteration(state, start_time)
        return

    result = execute(decision, state)
    append_action_record(state, decision, result)

    if decision["action"] == "stop":
        finish_iteration(state, start_time)
        return

    state["iteration"] += 1
    finish_iteration(state, start_time)


def parse_args(argv: list[str]) -> argparse.Namespace:
    """Parse command-line arguments.
    Returns an argparse namespace.
    """
    parser = argparse.ArgumentParser(
        description="Run an autonomous coding-agent orchestrator loop."
    )
    parser.add_argument("--spec", help="Path to the technical specification.")
    parser.add_argument("--resume", action="store_true", help="Resume from state.json.")
    parser.add_argument(
        "--max-iter",
        type=int,
        default=40,
        help="Maximum number of orchestrator iterations.",
    )
    parser.add_argument(
        "--log-intervention",
        help="Append a human intervention message and exit.",
    )
    args = parser.parse_args(argv)

    if not args.resume and not args.spec and not args.log_intervention:
        parser.print_usage()
        sys.exit(2)

    return args


def prepare_state(args: argparse.Namespace) -> dict:
    """Load or initialize orchestrator state based on CLI arguments.
    Returns the state dictionary.
    """
    if args.resume:
        try:
            state = load_state()
        except Exception as exc:
            print(f"could not load {STATE_FILE}: {exc}", file=sys.stderr)
            sys.exit(3)
        state["max_iterations"] = args.max_iter
        return state

    return initialize_state(args.spec, args.max_iter)


def run_loop(state: dict) -> int:
    """Run the main orchestrator loop until stop, cap, or crash.
    Returns a process exit code.
    """
    if not state.get("plan"):
        run_planner(state)

    while True:
        if state.get("done"):
            break
        if state["iteration"] >= state["max_iterations"]:
            break
        run_iteration(state)

    if state.get("done"):
        get_logger("errors").info(
            "iter %s final_summary clean_stop reason=%s",
            state["iteration"],
            state.get("stop_reason"),
        )
        save_state(state)
        return 0

    state["stop_reason"] = "iteration cap reached without stop"
    get_logger("errors").info(
        "iter %s final_summary cap_reached max_iterations=%s",
        state["iteration"],
        state["max_iterations"],
    )
    save_state(state)
    return 1


def main(argv: list[str] | None = None) -> int:
    """Run the CLI entrypoint.
    Returns a process exit code.
    """
    ensure_log_files()
    args = parse_args(sys.argv[1:] if argv is None else argv)

    if args.log_intervention:
        log_intervention(args.log_intervention)
        return 0

    state = prepare_state(args)

    try:
        return run_loop(state)
    except KeyboardInterrupt:
        try:
            save_state(state)
        except Exception as save_exc:
            log_error(state.get("iteration", -1), f"state save after interrupt failed: {save_exc}")
        raise
    except Exception:
        tb = traceback.format_exc()
        log_error(state.get("iteration", -1), f"uncaught exception:\n{tb}")
        try:
            save_state(state)
        except Exception as save_exc:
            log_error(state.get("iteration", -1), f"state save after crash failed: {save_exc}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
