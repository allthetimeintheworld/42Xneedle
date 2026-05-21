import os
import time
import json
import hashlib
from .config import MAX_ITERATIONS, SPEC_PATH, LOOP_DELAY
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
    colors = [
        "\033[91m", # Red
        "\033[93m", # Yellow
        "\033[92m", # Green
        "\033[96m", # Cyan
        "\033[94m", # Blue
        "\033[95m"  # Magenta
    ]
    reset = "\033[0m"
    banner = r"""
  _____ __  __          _____ 
 |___ /|  \/  |   /\   / ____|
   |_ \| |\/| |  /  \ | |     
  ___) | |  | | / /\ \| |     
 |____/|_|  |_|/_/    \_\_____|
                               
    42-X-Needle Autonomous Agent
    """
    lines = banner.split("\n")
    for i, line in enumerate(lines):
        color = colors[i % len(colors)]
        print(f"{color}{line}{reset}")

def main():
    # 0. Startup Validation (James's SecOps recommendation)
    if not any([GROQ_API_KEY, MISTRAL_API_KEY, DEEPSEEK_API_KEY]):
        print("\nFATAL ERROR: No API keys found for Groq, Mistral, or DeepSeek.")
        print("Please check your .env file and ensure credentials are correct.")
        return

    # 1. Goal-Stable State Initialization
    project_root = os.getcwd()
    print_banner()
    state = {
        "iteration": 0,
        "memory": [],  # Strategic insights
        "completed_milestones": [], # EXPLICIT DONE LIST
        "project_summary": {
            "goal": "Uninitialized",
            "progress": "Just started",
            "last_failure": None,
            "hypothesis": "Initial exploration",
            "next_step": "List files"
        },
        "action_history": [], # Track (action, params_hash) to detect loops
        "failure_types": [],
        "consecutive_failure_count": 0,
        "spec_hash": "",
        "consecutive_success_count": 0
    }

    # Load Role-Based Prompts
    prompts = {
        "architect": load_prompt("architect"),
        "researcher": load_prompt("researcher"),
        "reviewer": load_prompt("reviewer")
    }

    log_event("decisions.log", "42-X-Needle-Agent started (Milestone Registry Mode).")

    while state["iteration"] < MAX_ITERATIONS:
        log_event("decisions.log", f"Starting iteration {state['iteration']}")
        
        # A. Read Specification
        spec = read_file(SPEC_PATH) or "No specification found."
        current_spec_hash = hashlib.md5(spec.encode()).hexdigest()
        if state["spec_hash"] and state["spec_hash"] != current_spec_hash:
            log_event("decisions.log", "Spec change detected! Resetting for new objective.")
            state["memory"] = ["Resetting state for new task specification."]
            state["completed_milestones"] = []
            state["iteration"] = 0
            state["consecutive_success_count"] = 0
        state["spec_hash"] = current_spec_hash
        state["project_summary"]["goal"] = spec[:500]

        # B. ROLE ROUTING (Thinking Phase)
        is_failing = state["project_summary"]["last_failure"] is not None
        
        if is_failing:
            role = "researcher"
        elif state["consecutive_success_count"] >= 2:
            role = "reviewer"
        else:
            role = "architect"
            
        system_inst = prompts[role]
        
        # Oscillation Detection
        oscillation_warning = ""
        last_actions = state["action_history"][-3:]
        if len(last_actions) >= 3 and len(set(last_actions)) == 1:
            oscillation_warning = f"\n\nSTALL WARNING: You have repeated the same action 3 times. CHANGE STRATEGY."

        # Inject state summary and project context
        all_files = list_files(".")
        # Filter out agent infrastructure to prevent distraction
        workspace_files = [f for f in all_files if f not in [
            "agent", "orchestrator", "agent_logs", "README.md", 
            "ARCHITECTURAL_OVERVIEW.md", "GEMINI.md", ".env", ".venv", 
            ".git", "__pycache__", "secret_spec"
        ]]

        context = {
            "current_role": role,
            "project_root": project_root,
            "summary": state["project_summary"],
            "completed_milestones": state["completed_milestones"],
            "insights": state["memory"][-5:],
            "workspace_files": workspace_files[:20]
        }
        
        prompt = f"SPECIFICATION:\n{spec[:1000]}\n\nCONTEXT:\n{json.dumps(context, indent=2)}{oscillation_warning}\n\nDECIDE NEXT ACTION:"

        # C. LLM Call
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
            state["iteration"] += 1
            continue

        # D. Update State Tracking
        action = decision.get("action")
        params = decision.get("params", {})
        thought = decision.get("thought", "No thought provided")
        
        # Milestone tracking
        if "milestone_reached" in decision:
            m = decision["milestone_reached"]
            if m not in state["completed_milestones"]:
                state["completed_milestones"].append(m)

        params_hash = hashlib.md5(json.dumps(params, sort_keys=True).encode()).hexdigest()
        state["action_history"].append(f"{action}:{params_hash}")
        
        state["project_summary"]["hypothesis"] = decision.get("hypothesis", state["project_summary"]["hypothesis"])
        state["project_summary"]["next_step"] = decision.get("task_status", "Proceeding...")

        log_event("decisions.log", f"Role: {role} | Action: {action} | Thought: {thought}")
        print(f"\n[{state['iteration']}] ROLE: {role.upper()} | THOUGHT: {thought}")
        print(f"ACTION: {action}({json.dumps(params)})")

        # E. THE "ACT" PHASE
        result_output = ""
        success = False
        
        if action == "edit_file":
            path, content = params.get("path"), params.get("content")
            if path and content is not None:
                if path.endswith(".py"):
                    tmp_path = f"{path}.tmp"
                    if edit_file(tmp_path, content):
                        code, out = run_command(f"python3 -m py_compile {tmp_path}")
                        if os.path.exists(tmp_path): os.remove(tmp_path)
                        if code == 0:
                            success = edit_file(path, content)
                            result_output = f"File {path} updated."
                        else:
                            success = False
                            result_output = f"SYNTAX ERROR PREVENTED:\n{out}"
                else:
                    success = edit_file(path, content)
                    result_output = f"File {path} written."
            else:
                result_output = "ERROR: Missing path/content."

        elif action == "run_command":
            cmd = params.get("command")
            if cmd:
                code, out = run_command(cmd)
                success = (code == 0)
                result_output = out[:800]
                if not success: state["failure_types"] = state.get("failure_types", []) + [classify_failure(out)]
                if success and ("test" in cmd or "git" in cmd): git_snapshot(f"Success: {cmd}")
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
            result_output = str(files)

        elif action == "stop":
            log_event("decisions.log", f"Agent stopped explicitly: {params.get('reason')}")
            break

        # F. Update Summary
        state["project_summary"]["last_action"] = action
        state["project_summary"]["last_result"] = "SUCCESS" if success else "FAILURE"
        
        if not success:
            state["project_summary"]["last_failure"] = result_output[:500]
            state["memory"].append(f"FAILED {action}: {result_output[:100]}")
            state["consecutive_success_count"] = 0
            state["consecutive_failure_count"] += 1
            print(f"RESULT: ❌ FAILURE ({result_output[:100]}...)")
            
            # G. Infinite Loop Circuit Breaker (Deep Fix)
            if state["consecutive_failure_count"] >= 5:
                msg = "CRITICAL: 5 consecutive failures detected. Terminating to prevent infinite loop."
                log_event("errors.log", msg)
                print(f"\n{msg}")
                break
        else:
            state["project_summary"]["last_failure"] = None
            state["memory"].append(f"SUCCESS {action}: {state['project_summary']['hypothesis'][:100]}")
            state["consecutive_success_count"] += 1
            state["consecutive_failure_count"] = 0 # Reset on success
            print(f"RESULT: ✅ SUCCESS")

        # G. Intelligent Stop
        if state["consecutive_success_count"] >= 3 and role == "reviewer":
             log_event("decisions.log", "Reviewer satisfied. Stopping.")
             break

        state["iteration"] += 1
        time.sleep(LOOP_DELAY)

    # FINAL CLEANUP HOOK (Non-persistent rule)
    print("\nRUNNING FINAL CLEANUP HOOK...")
    run_command("find . -name '*.bak' -type f -delete")

    log_event("decisions.log", "42-X-Needle-Agent finished.")

if __name__ == "__main__":
    main()
