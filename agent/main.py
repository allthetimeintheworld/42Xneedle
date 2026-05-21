import os
import time
import json
import hashlib
from .config import MAX_ITERATIONS, SPEC_PATH, LOOP_DELAY
from .llm import ask_model, log_event
from .tools.filesystem import read_file, edit_file, list_files
from .tools.shell import run_command, git_snapshot
from .tools.parser import parse_action

def load_prompt(name):
    path = f"prompts/{name}.txt"
    if os.path.exists(path):
        with open(path, "r") as f:
            return f.read()
    return "You are a coding agent. Return JSON."

def get_output_hash(output):
    if not output: return ""
    return hashlib.md5(output.encode()).hexdigest()

def main():
    state = {
        "iteration": 0,
        "last_command_result": None,
        "last_read_content": None,
        "last_file_list": None,
        "history": [],
        "failure_hashes": [],
        "task_status": "Starting task..."
    }

    planner_prompt = load_prompt("planner")
    fixer_prompt = load_prompt("fixer")

    log_event("decisions.log", "42-X-Needle-Agent started.")

    while state["iteration"] < MAX_ITERATIONS:
        log_event("decisions.log", f"Starting iteration {state['iteration']}")

        # 1. Read Spec
        spec = read_file(SPEC_PATH) or "No specification found."

        # 2. Select Prompt & Add Robustness Layers
        if state["last_command_result"] and state["last_command_result"]["code"] != 0:
            history_summary = json.dumps(state["history"][-5:], indent=2)
            system_inst = fixer_prompt.replace("{test_output}", state["last_command_result"]["output"])\
                                     .replace("{spec}", spec[:1000])\
                                     .replace("{task_status}", state["task_status"])\
                                     .replace("{history}", history_summary)
            prompt = "The previous command failed. Analyze the failure and provide a fix."
        else:
            system_inst = planner_prompt
            context = {
                "iteration": state["iteration"],
                "task_status": state["task_status"],
                "history": state["history"][-5:], # Last 5 steps for short-term memory
                "last_file_list": state["last_file_list"],
                "last_read_content": state["last_read_content"][:500] if state["last_read_content"] else "None"
            }
            prompt = f"Spec: {spec[:1000]}\n\nCurrent State:\n{json.dumps(context, indent=2)}\n\nWhat is the next action?"

        # Oscillation Detection
        if len(state["failure_hashes"]) >= 3 and len(set(state["failure_hashes"][-3:])) == 1:
            oscillation_warning = "\n\nCRITICAL WARNING: You have produced the exact same failure 3 times in a row. Your current approach is stuck. You MUST change your strategy fundamentally (e.g., check environment, project structure, or a completely different code approach)."
            prompt += oscillation_warning
            system_inst += oscillation_warning

        # 3. Ask Model with Retries
        decision = None
        for retry in range(2):
            response_str = ask_model(prompt, system_inst)
            decision, error = parse_action(response_str)
            if not error:
                break
            log_event("errors.log", f"JSON Parse Error (Retry {retry}): {error}")
            prompt += f"\n\nERROR: Your last response was not valid JSON: {error}. Please return ONLY a valid JSON object."

        if not decision:
            log_event("errors.log", "Failed to get valid JSON after retries. Skipping iteration.")
            state["iteration"] += 1
            continue

        action = decision.get("action")
        params = decision.get("params", {})

        # Goal Tracking Update
        if "task_status" in decision:
            new_status = decision["task_status"]
            state["task_status"] = str(new_status) if new_status is not None else "Unknown"

        log_event("decisions.log", f"Decision: {action} - {json.dumps(params)}")

        # 4. Execute Action
        error_msg = None
        if action == "edit_file":
            path = params.get("path")
            content = params.get("content")
            if path and content is not None:
                if edit_file(path, content):
                    log_event("decisions.log", f"Successfully edited {path}")
                    # Syntax Gate
                    if path.endswith(".py"):
                        code, out = run_command(f"python3 -m py_compile {path}")
                        if code != 0:
                            error_msg = f"Syntax error introduced in {path}: {out}"
            else:
                error_msg = "edit_file requires both 'path' and 'content' parameters."

        elif action == "read_file":
            path = params.get("path")
            if path:
                content = read_file(path)
                state["last_read_content"] = content
            else:
                error_msg = "read_file requires 'path' parameter."

        elif action == "list_files":
            dir_path = params.get("dir", ".")
            state["last_file_list"] = list_files(dir_path)

        elif action == "run_command":
            command = params.get("command")
            if command:
                code, output = run_command(command)
                state["last_command_result"] = {"code": code, "output": output}
                log_event("commands.log", f"Command Output ({command}):\n{output}")

                # Track failure hashes for oscillation detection
                if code != 0:
                    state["failure_hashes"].append(get_output_hash(output))

                if code == 0 and ("test" in command or "git" in command):
                    git_snapshot(f"Iteration {state['iteration']} - {command} passed")
            else:
                error_msg = "run_command requires 'command' parameter."

        elif action == "stop":
            log_event("decisions.log", f"Agent stopped: {params.get('reason', 'No reason provided')}")
            break

        if error_msg:
            log_event("errors.log", error_msg)
            state["last_command_result"] = {"code": 1, "output": f"ERROR: {error_msg}"}

        # Update History
        state["history"].append({
            "iteration": state["iteration"],
            "action": action,
            "params": params,
            "success": (error_msg is None and (not state["last_command_result"] or state["last_command_result"]["code"] == 0))
        })

        state["iteration"] += 1
        time.sleep(LOOP_DELAY)

    log_event("decisions.log", "42-X-Needle-Agent finished.")
if __name__ == "__main__":
    main()
