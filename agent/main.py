import os
import time
import json
import hashlib
from .config import MAX_ITERATIONS, SPEC_PATH, LOOP_DELAY
from .llm import ask_model, log_event
from .tools.filesystem import read_file, edit_file, list_files
from .tools.shell import run_command, git_snapshot
from .tools.parser import parse_action

# Configuration for stability
VALID_ACTIONS = {"edit_file", "run_command", "read_file", "list_files", "stop"}

def load_prompt(name):
    path = f"prompts/{name}.txt"
    if os.path.exists(path):
        with open(path, "r") as f:
            return f.read()
    return "You are a coding agent. Return JSON."

def classify_failure(output):
    """Classifies a command failure into actionable types."""
    if not output: return "UNKNOWN"
    low_out = output.lower()
    if "syntaxerror" in low_out or "invalid syntax" in low_out:
        return "SYNTAX"
    if "assertionerror" in low_out or "failed" in low_out:
        return "ASSERTION"
    if "modulenotfounderror" in low_out or "not found" in low_out:
        return "ENVIRONMENT"
    if "timeout" in low_out:
        return "TIMEOUT"
    return "RUNTIME"

def main():
    # 1. Goal-Stable State Initialization
    project_root = os.getcwd()
    state = {
        "iteration": 0,
        "memory": [],  # Strategic insights
        "project_summary": {
            "goal": "Uninitialized",
            "progress": "Just started",
            "last_failure": None,
            "hypothesis": "Initial exploration",
            "next_step": "List files"
        },
        "action_history": [], # Track (action, params_hash) to detect loops
        "spec_hash": "",
        "consecutive_success_count": 0
    }

    planner_prompt = load_prompt("planner")
    fixer_prompt = load_prompt("fixer")

    log_event("decisions.log", "42-X-Needle-Agent started (Fixing Oscillations).")

    while state["iteration"] < MAX_ITERATIONS:
        log_event("decisions.log", f"Starting iteration {state['iteration']}")
        
        # A. Read & Sync Specification
        spec = read_file(SPEC_PATH) or "No specification found."
        current_spec_hash = hashlib.md5(spec.encode()).hexdigest()
        if state["spec_hash"] and state["spec_hash"] != current_spec_hash:
            log_event("decisions.log", "Spec change detected! Resetting for new objective.")
            state["memory"] = ["Resetting state for new task specification."]
            state["iteration"] = 0
            state["consecutive_success_count"] = 0
        state["spec_hash"] = current_spec_hash
        state["project_summary"]["goal"] = spec[:500]

        # B. THE "THINK" PHASE
        # Enhanced Oscillation Detection (Action-Param based)
        oscillation_warning = ""
        last_actions = state["action_history"][-3:]
        if len(last_actions) >= 3 and len(set(last_actions)) == 1:
            oscillation_warning = "\n\nCRITICAL WARNING: You have repeated the EXACT SAME action and parameters 3 times in a row. You are stuck in a loop. You MUST change your strategy, parameters, or tool immediately."

        # Select System Prompt
        is_failing = state["project_summary"]["last_failure"] is not None
        system_inst = fixer_prompt if is_failing else planner_prompt
        
        # Inject state summary and project context
        context = {
            "project_root": project_root,
            "summary": state["project_summary"],
            "insights": state["memory"][-5:],
            "files": list_files(".")[:20]
        }
        
        prompt = f"SPECIFICATION:\n{spec[:1000]}\n\nCONTEXT:\n{json.dumps(context, indent=2)}{oscillation_warning}\n\nDECIDE NEXT ACTION:"

        # C. LLM Call with Schema Enforcement
        decision = None
        for retry in range(2):
            response_str = ask_model(prompt, system_inst)
            decision, error = parse_action(response_str)
            if not error:
                action = decision.get("action")
                if action in VALID_ACTIONS:
                    break
                else:
                    error = f"Invalid action '{action}'. Must be one of {VALID_ACTIONS}"
            
            log_event("errors.log", f"Refining response (Retry {retry}): {error}")
            prompt += f"\n\nERROR: {error}. Return valid JSON with a supported 'action'."

        if not decision:
            log_event("errors.log", "LLM failed to provide valid instruction. Skipping turn.")
            state["iteration"] += 1
            continue

        # D. Update State Tracking
        action = decision.get("action")
        params = decision.get("params", {})
        params_hash = hashlib.md5(json.dumps(params, sort_keys=True).encode()).hexdigest()
        state["action_history"].append(f"{action}:{params_hash}")
        
        state["project_summary"]["hypothesis"] = decision.get("hypothesis", state["project_summary"]["hypothesis"])
        state["project_summary"]["next_step"] = decision.get("task_status", "Proceeding...")

        log_event("decisions.log", f"Action: {action} | Hypothesis: {state['project_summary']['hypothesis']}")

        # E. THE "ACT" PHASE: Execute Tools
        result_output = ""
        success = False
        
        if action == "edit_file":
            path, content = params.get("path"), params.get("content")
            if path and content is not None:
                # Syntax Gate (Felix recommendation)
                if path.endswith(".py"):
                    # Use temporary file to check syntax before overwriting
                    tmp_path = f"{path}.tmp"
                    if edit_file(tmp_path, content):
                        code, out = run_command(f"python3 -m py_compile {tmp_path}")
                        os.remove(tmp_path)
                        if code == 0:
                            success = edit_file(path, content)
                            result_output = f"File {path} updated successfully."
                        else:
                            success = False
                            result_output = f"SYNTAX ERROR PREVENTED: Your proposed code for {path} was invalid:\n{out}"
                else:
                    success = edit_file(path, content)
                    result_output = f"File {path} written."
            else:
                result_output = "ERROR: Missing path or content."

        elif action == "run_command":
            cmd = params.get("command")
            if cmd:
                code, out = run_command(cmd)
                success = (code == 0)
                result_output = out[:1000] # Token efficiency (Luis recommendation)
                
                # Update failure clustering
                if not success:
                    state["failure_types"].append(classify_failure(out))
                
                # Auto-Snapshot
                if success and ("test" in cmd or "git" in cmd):
                    git_snapshot(f"Success in {state['iteration']}: {cmd}")
            else:
                result_output = "ERROR: Missing command."

        elif action == "read_file":
            path = params.get("path")
            content = read_file(path) if path else None
            success = (content is not None)
            result_output = content[:1000] if success else "File not found."

        elif action == "list_files":
            dir_path = params.get("dir", ".")
            files = list_files(dir_path)
            success = True
            result_output = f"Files in {dir_path}: {str(files)}"

        elif action == "stop":
            log_event("decisions.log", f"Agent stopped: {params.get('reason')}")
            break

        # F. Update Summary & Reasoning Memory
        state["project_summary"]["last_action"] = action
        state["project_summary"]["last_result"] = "SUCCESS" if success else "FAILURE"
        
        if not success:
            state["project_summary"]["last_failure"] = result_output[:500]
            state["memory"].append(f"FAILED {action}: {result_output[:100]}")
            state["consecutive_success_count"] = 0
        else:
            state["project_summary"]["last_failure"] = None
            state["memory"].append(f"SUCCESS {action}: {state['project_summary']['hypothesis']}")
            state["consecutive_success_count"] += 1

        # G. Autonomous Stopping Rule
        if state["consecutive_success_count"] >= 3:
             # Stop if stable and a terminal command (like git or test) was successful
             if any(x in str(state["memory"][-5:]) for x in ["SUCCESS run_command: git", "SUCCESS run_command: pytest"]):
                 log_event("decisions.log", "System stabilized after successful terminal actions. Stopping.")
                 break

        state["iteration"] += 1
        time.sleep(LOOP_DELAY)

    log_event("decisions.log", "42-X-Needle-Agent finished.")

if __name__ == "__main__":
    main()
