import subprocess
import os
from ..llm import log_event

def run_command(command, timeout=120):
    log_event("commands.log", f"Running: {command}")
    try:
        # Hardened invocation using bash -c with a strict timeout
        result = subprocess.run(
            ["bash", "-c", command],
            capture_output=True, 
            text=True, 
            timeout=timeout,
            shell=False
        )
        output = result.stdout + result.stderr
        log_event("commands.log", f"Exit Code: {result.returncode}")
        
        if result.returncode != 0:
            log_event("errors.log", f"Command failed: {command}\nOutput: {output}")
        
        return result.returncode, output
    except subprocess.TimeoutExpired:
        msg = f"TIMEOUT: Command exceeded {timeout}s limit: {command}"
        log_event("errors.log", msg)
        return 124, msg
    except Exception as e:
        log_event("errors.log", f"Exception running command: {command}\n{str(e)}")
        return -1, str(e)

def git_snapshot(message):
    # 1. Check if git is initialized
    if not os.path.exists(".git"):
        log_event("errors.log", "git_snapshot failed: .git directory not found. Skipping snapshot.")
        return False

    # 2. Check if there are changes to commit
    status_code, status_out = run_command("git status --porcelain")
    if status_code == 0 and not status_out.strip():
        # No changes, skip commit to avoid noise
        return True

    # 3. Perform snapshot
    run_command("git add .")
    # Wrap message in single quotes to handle special characters
    code, out = run_command(f"git commit -m 'agent: {message}'")
    
    if code != 0 and "nothing to commit" not in out:
        log_event("errors.log", f"git_snapshot failed: {out}")
        return False
        
    return True
