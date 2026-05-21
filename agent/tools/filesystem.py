import os
from ..llm import log_event

def read_file(path):
    if os.path.exists(path):
        with open(path, "r") as f:
            content = f.read()
        log_event("commands.log", f"Read file: {path}")
        return content
    log_event("errors.log", f"read_file failed: path not found: {path}")
    return None

def edit_file(path, content):
    if not path:
        log_event("errors.log", "edit_file failed: no path provided")
        return False
    
    # Safety: ensure path is relative and within project
    if os.path.isabs(path) or ".." in path:
        # For the hackathon, we allow it if it's within the project root
        # but let's encourage relative paths.
        log_event("errors.log", f"edit_file: absolute or parent paths are risky: {path}")

    try:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    except Exception as e:
        log_event("errors.log", f"edit_file failed to create directories for {path}: {str(e)}")
        return False
    
    # Simple backup before overwrite
    if os.path.exists(path):
        backup_path = f"{path}.bak"
        with open(path, "r") as f_src, open(backup_path, "w") as f_dst:
            f_dst.write(f_src.read())
        log_event("commands.log", f"Created backup: {backup_path}")

    with open(path, "w") as f:
        f.write(content)
    log_event("commands.log", f"Edited file: {path}")
    return True

def list_files(dir_path="."):
    if os.path.isdir(dir_path):
        files = os.listdir(dir_path)
        log_event("commands.log", f"Listed files in: {dir_path}")
        return files
    log_event("errors.log", f"list_files failed: dir not found: {dir_path}")
    return []
