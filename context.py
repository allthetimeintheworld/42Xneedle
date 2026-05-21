from pathlib import Path

from logger import get_logger


PROMPT_DIR = Path("prompts")
SYSTEM_PROMPT_PATH = PROMPT_DIR / "system.txt"
PLAN_PROMPT_PATH = PROMPT_DIR / "plan.txt"
DECIDE_PROMPT_PATH = PROMPT_DIR / "decide.txt"
SPEC_TRUNCATE_AT = 6000
WORKSPACE_ENTRY_LIMIT = 30


def _read_template(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


SYSTEM_TEMPLATE = _read_template(SYSTEM_PROMPT_PATH)
PLAN_TEMPLATE = _read_template(PLAN_PROMPT_PATH)
DECIDE_TEMPLATE = _read_template(DECIDE_PROMPT_PATH)


def build_planning_prompt(spec_text: str) -> tuple[str, str]:
    """Build prompts for the initial planning call."""
    user_prompt = PLAN_TEMPLATE.format(spec_text=spec_text)
    get_logger("prompts").info(
        "built planning prompt: spec=%s total=%s chars",
        len(spec_text),
        len(user_prompt),
    )
    return SYSTEM_TEMPLATE, user_prompt


def build_context(state: dict) -> tuple[str, str]:
    """Build prompts for the per-iteration decision call."""
    spec_section = _build_spec_section(state)
    plan_section = _build_plan_section(state)
    workspace_section = _build_workspace_section(state)
    last_test_section = _build_last_test_section(state)
    trajectory_section = _build_trajectory_section(state)

    user_prompt = DECIDE_TEMPLATE.format(
        spec_section=spec_section,
        plan_section=plan_section,
        workspace_section=workspace_section,
        last_test_section=last_test_section,
        trajectory_section=trajectory_section,
    )
    get_logger("prompts").info(
        "built decide prompt: spec=%s plan=%s workspace=%s test=%s traj=%s total=%s chars",
        len(spec_section),
        len(plan_section),
        len(workspace_section),
        len(last_test_section),
        len(trajectory_section),
        len(user_prompt),
    )
    return SYSTEM_TEMPLATE, user_prompt


def summarize_trajectory(recent_actions: list[dict]) -> str:
    """Return a compact deterministic summary of older action records."""
    if not recent_actions:
        return "No earlier actions."

    edited = []
    read_count = 0
    test_count = 0
    rejection_count = 0
    last_test = ""

    for record in recent_actions:
        action = record.get("action", "")
        args = record.get("args", {}) if isinstance(record.get("args"), dict) else {}
        summary = str(record.get("result_summary", ""))
        success = record.get("success")

        if action == "edit_file":
            path = args.get("path")
            if path:
                edited.append(Path(path).name)
        elif action == "read_file":
            read_count += 1
        elif action == "run_tests":
            test_count += 1
            last_test = summary
        if success is False and "reject" in summary.lower():
            rejection_count += 1

    parts = [f"Earlier: {len(recent_actions)} actions."]
    if edited:
        unique = sorted(set(edited))[:5]
        parts.append(f"Edited {len(edited)} files ({', '.join(unique)}).")
    if read_count:
        parts.append(f"Read {read_count} files.")
    if test_count:
        detail = f", last result: {last_test}" if last_test else ""
        parts.append(f"Ran tests {test_count} times{detail}.")
    if rejection_count:
        parts.append(f"{rejection_count} guardrail rejections.")

    # Option B for future tuning: summarize with the model if deterministic counts are too thin.
    return " ".join(parts)[:500]


def _build_spec_section(state: dict) -> str:
    spec = str(state.get("spec_text", ""))
    spec_path = state.get("spec_path", "the spec file")
    if len(spec) <= SPEC_TRUNCATE_AT:
        return spec
    # TODO: tune this threshold after seeing real hackathon spec sizes.
    return (
        spec[:1500]
        + f"\n[... spec truncated, full version at {spec_path}; ask the human if more is needed ...]\n"
        + spec[-900:]
    )


def _build_plan_section(state: dict) -> str:
    plan = state.get("plan") or []
    if not plan:
        return "(no plan generated yet)"

    current = int(state.get("current_step_index", 0) or 0)
    lines = []
    for index, step in enumerate(plan):
        marker = "  [<-- current]" if index == current else ""
        lines.append(f"Step {index + 1}: {step}{marker}")
    # TODO: agent.py does not auto-advance current_step_index yet.
    return "\n".join(lines)


def _build_workspace_section(state: dict) -> str:
    root = Path("workspace")
    root.mkdir(exist_ok=True)
    entries = [path for path in root.rglob("*") if not _is_hidden(path) and path.exists()]
    files = [path for path in entries if path.is_file()]
    dirs = [path for path in entries if path.is_dir()]

    if not files and not dirs:
        return "workspace/\n(empty - no files created yet)"

    shown = sorted(files + dirs, key=lambda item: str(item.relative_to(root)))[:WORKSPACE_ENTRY_LIMIT]
    lines = ["workspace/"]
    for path in shown:
        rel = path.relative_to(root)
        indent = "    " * (len(rel.parts) - 1)
        name = rel.name + ("/" if path.is_dir() else "")
        try:
            size = "" if path.is_dir() else f" ({_format_size(path.stat().st_size)})"
        except FileNotFoundError:
            continue
        lines.append(f"{indent}- {name}{size}")

    remaining = len(files) + len(dirs) - len(shown)
    if remaining > 0:
        lines.append(f"... and {remaining} more files")
    return "\n".join(lines)


def _build_last_test_section(state: dict) -> str:
    result = state.get("last_test_result")
    if not result:
        return "(no test run yet - call run_tests to get feedback)"

    passed = result.get("passed", 0)
    failed = result.get("failed", 0)
    errors = result.get("errors", 0)
    failure_summary = result.get("failure_summary") or "(none)"
    return (
        f"Last test run: {passed} passed, {failed} failed, {errors} errors\n\n"
        f"Failures (first 3):\n{failure_summary}"
    )


def _build_trajectory_section(state: dict) -> str:
    older = str(state.get("older_trajectory_summary") or "").strip()
    recent = state.get("recent_actions") or []

    recent_lines = [_format_action(record) for record in recent]
    if not recent_lines:
        recent_text = "(no recent actions yet)"
    else:
        recent_text = "\n".join(recent_lines)

    if older:
        return f"Earlier in this session:\n{older}\n\nRecent actions:\n{recent_text}"
    return recent_text


def _format_action(record: dict) -> str:
    iteration = record.get("iteration", "?")
    action = record.get("action", "?")
    args = record.get("args", {}) if isinstance(record.get("args"), dict) else {}
    summary = str(record.get("result_summary", "")).strip()
    status = "success" if record.get("success") else "failed"

    target = ""
    if action in {"read_file", "edit_file"} and args.get("path"):
        target = f" {args['path']}"
    elif action == "list_dir":
        target = f" {args.get('path', 'workspace/')}"
    elif action == "run_shell":
        target = f" {args.get('cmd', '')}"

    detail = f" - {summary}" if summary else ""
    return f"iter {iteration}: {action}{target}{detail} ({status})"


def _is_hidden(path: Path) -> bool:
    return any(part.startswith(".") for part in path.parts)


def _format_size(size: int) -> str:
    if size < 1024:
        return f"{size} bytes"
    return f"{size / 1024:.1f} KB"
