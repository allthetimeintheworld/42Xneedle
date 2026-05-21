import subprocess
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
    run_command("git add .")
    run_command(f'git commit -m "agent: {message}"')
