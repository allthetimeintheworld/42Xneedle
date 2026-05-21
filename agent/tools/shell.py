import subprocess
from ..llm import log_event

def run_command(command):
    log_event("commands.log", f"Running: {command}")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        output = result.stdout + result.stderr
        log_event("commands.log", f"Exit Code: {result.returncode}")
        
        if result.returncode != 0:
            log_event("errors.log", f"Command failed: {command}\nOutput: {output}")
        
        return result.returncode, output
    except Exception as e:
        log_event("errors.log", f"Exception running command: {command}\n{str(e)}")
        return -1, str(e)

def git_snapshot(message):
    run_command("git add .")
    run_command(f'git commit -m "agent: {message}"')
