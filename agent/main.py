import os
import time
import json
import hashlib
from .config import MAX_ITERATIONS, SPEC_PATH, LOOP_DELAY, INFRASTRUCTURE_FILES
from .config import GROQ_API_KEY, MISTRAL_API_KEY, DEEPSEEK_API_KEY
from .llm import ask_model, log_event
from .tools.filesystem import read_file, edit_file, list_files
from .tools.shell import run_command, git_snapshot
from .tools.parser import parse_action

# Configuration for stability
VALID_ACTIONS = {"edit_file", "run_command", "read_file", "list_files", "stop"}

def load_prompt(name):
    path = f"orchestrator/{name}.txt"
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

def print_banner():
    colors = ["\033[91m", "\033[93m", "\033[92m", "\033[96m", "\033[94m", "\033[95m"]
    reset = "\033[0m"
    banner = r"""
  _____ __  __          _____ 
 |___ /|  \/  |   /\   / ____|
   |_ \| |\/| |  /  \ | |     
  ___) | |  | | / /\ \| |     
 |____/|_|  |_|/_/    \_\_____|
                               
    42-X-Needle Autonomous Agent
    """
    for i, line in enumerate(banner.split("\n")):
        print(f"{colors[i % len(colors)]}{line}{reset}")

def main():
    if not any([GROQ_API_KEY, MISTRAL_API_KEY, DEEPSEEK_API_KEY]):
        print("\nFATAL ERROR: No API keys found.")
        return

    project_root = os.getcwd()
    print_banner()
    state = {
        "iteration": 0,
        "memory": [],
        "last_tool_output": None,
        "completed_milestones": [],
        "implementation_started": False,
        "project_summary": {"goal": "Uninitialized", "progress": "Just started", "last_failure": None, "hypothesis": "Initial exploration", "next_step": "List files"},
        "action_history": [],
        "failure_types": [],
        "consecutive_failure_count": 0,
        "spec_hash": "",
        "consecutive_success_count": 0
    }

    prompts = {"architect": load_prompt("architect"), "researcher": load_prompt("researcher"), "reviewer": load_prompt("reviewer")}

    while state["iteration"] < MAX_ITERATIONS:
        log_event("decisions.log", f"Starting iteration {state['iteration']}")
        spec = read_file(SPEC_PATH) or "No specification found."
        current_spec_hash = hashlib.md5(spec.encode()).hexdigest()
        if state["spec_hash"] and state["spec_hash"] != current_spec_hash:
            state["memory"], state["completed_milestones"], state["iteration"], state["consecutive_success_count"] = ["Resetting state for new task."], [], 0, 0
            state["implementation_started"] = False
        state["spec_hash"] = current_spec_hash
        state["project_summary"]["goal"] = spec[:500]

        # 2. ROLE ROUTING (Refined)
        if state["project_summary"]["last_failure"]:
            role = "researcher"
        elif state["implementation_started"] and state["consecutive_success_count"] >= 4:
            role = "reviewer"
        else:
            role = "architect"
        system_inst = prompts[role]
        
        oscillation_warning = ""
        if len(state["action_history"]) >= 3 and len(set(state["action_history"][-3:])) == 1:
            oscillation_warning = f"\n\nCRITICAL STALL WARNING: You have repeated the exact same action 3 times. CHANGE STRATEGY or use line ranges for reads."

        workspace_files = []
        try:
            raw_files = os.listdir(".")
            workspace_files = [f for f in raw_files if f not in INFRASTRUCTURE_FILES]
        except: workspace_files = []
            
        context = {"current_role": role, "project_root": project_root, "summary": state["project_summary"], "last_tool_output": state["last_tool_output"], "completed_milestones": state["completed_milestones"], "insights": state["memory"][-5:], "workspace_files": workspace_files[:20]}
        prompt = f"SPECIFICATION (TRUNCATED):\n{spec[:4000]}\n\nCONTEXT:\n{json.dumps(context, indent=2)}{oscillation_warning}\n\nDECIDE NEXT ACTION:"

        decision = None
        for retry in range(2):
            response_str = ask_model(prompt, system_inst)
            decision, error = parse_action(response_str)
            if not error and decision.get("action") in VALID_ACTIONS: break
            prompt += f"\n\nERROR: {error}. Return valid JSON."

        if not decision:
            state["iteration"] += 1
            continue

        action, params, thought = decision.get("action"), decision.get("params", {}), decision.get("thought", "No thought")
        params_hash = hashlib.md5(json.dumps(params, sort_keys=True).encode()).hexdigest()
        action_sig = f"{action}:{params_hash}"
        if len(state["action_history"]) > 0 and action_sig == state["action_history"][-1]: state["consecutive_success_count"] = 0
        state["action_history"].append(action_sig)
        
        if "milestone_reached" in decision:
            m = decision["milestone_reached"]
            if m not in state["completed_milestones"]: state["completed_milestones"].append(m)

        state["project_summary"]["hypothesis"] = decision.get("hypothesis", state["project_summary"]["hypothesis"])
        state["project_summary"]["next_step"] = decision.get("task_status", "Proceeding...")
        print(f"\n[{state['iteration']}] ROLE: {role.upper()} | THOUGHT: {thought}\nACTION: {action}({json.dumps(params)})")

        result_output, success = "", False
        if action == "edit_file":
            state["implementation_started"] = True
            path, content = params.get("path"), params.get("content")
            if path and content is not None:
                if path.endswith(".py"):
                    tmp_path = f"{path}.tmp"
                    if edit_file(tmp_path, content):
                        code, out = run_command(f"python3 -m py_compile {tmp_path}")
                        if os.path.exists(tmp_path): os.remove(tmp_path)
                        if code == 0:
                            success, result_output = edit_file(path, content), f"File {path} updated."
                        else: success, result_output = False, f"SYNTAX ERROR PREVENTED:\n{out}"
                else: success, result_output = edit_file(path, content), f"File {path} written."
            else: result_output = "ERROR: Missing path/content."
        elif action == "run_command":
            state["implementation_started"] = True
            cmd = params.get("command")
            if cmd:
                code, out = run_command(cmd)
                success, result_output = (code == 0), out[:800]
                if not success: state["failure_types"].append(classify_failure(out))
                if success and ("test" in cmd or "git" in cmd): git_snapshot(f"Success: {cmd}")
            else: result_output = "ERROR: Missing command."
        elif action == "read_file":
            path = params.get("path")
            content = read_file(path) if path else None
            success, result_output = (content is not None), (content[:1000] if content else "File not found.")
            state["last_tool_output"] = result_output
        elif action == "list_files":
            dir_path = params.get("dir", ".")
            files = list_files(dir_path)
            success = True
            files_with_info = []
            for f in files:
                try:
                    fpath = os.path.join(dir_path, f)
                    if os.path.isfile(fpath): files_with_info.append(f"{f} ({os.path.getsize(fpath)} bytes)")
                    else: files_with_info.append(f"{f} [DIR]")
                except: files_with_info.append(f)
            result_output, state["last_tool_output"] = str(files_with_info), str(files_with_info)
        elif action == "stop":
            log_event("decisions.log", f"Agent stopped: {params.get('reason')}")
            break

        state["project_summary"]["last_action"], state["project_summary"]["last_result"] = action, "SUCCESS" if success else "FAILURE"
        if not success:
            state["project_summary"]["last_failure"] = result_output[:500]
            state["memory"].append(f"FAILED {action}: {result_output[:100]}")
            state["consecutive_success_count"], state["consecutive_failure_count"] = 0, state["consecutive_failure_count"] + 1
            print(f"RESULT: ❌ FAILURE ({result_output[:100]}...)")
            if state["consecutive_failure_count"] >= 5: break
        else:
            state["project_summary"]["last_failure"] = None
            state["memory"].append(f"SUCCESS {action}: {state['project_summary']['hypothesis'][:100]}")
            state["consecutive_success_count"], state["consecutive_failure_count"] = state["consecutive_success_count"] + 1, 0
            print(f"RESULT: ✅ SUCCESS")

        state["iteration"] += 1
        time.sleep(LOOP_DELAY)

    print("\nRUNNING FINAL CLEANUP HOOK...")
    run_command("find . -name '*.bak' -type f -delete")
    log_event("decisions.log", "42-X-Needle-Agent finished.")

if __name__ == "__main__": main()
