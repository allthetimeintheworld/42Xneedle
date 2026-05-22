import os
import time
from ..llm import log_event

def _enforce_sandbox(path):
    """Ensures the path is relative to the project root and doesn't escape it."""
    if not path:
        return None
    try:
        project_root = os.getcwd()
        abs_path = os.path.abspath(path)
        if not abs_path.startswith(project_root):
            log_event("errors.log", f"SECURITY VIOLATION: Attempted to access out-of-sandbox path: {abs_path}")
            return None
        return abs_path
    except Exception as e:
        log_event("errors.log", f"Path resolution error for {path}: {str(e)}")
        return None

def read_file(path, start_line=None, end_line=None, max_size=1024*1024): # 1MB limit
    safe_path = _enforce_sandbox(path)
    if safe_path and os.path.exists(safe_path):
        try:
            # Check size before reading
            file_size = os.path.getsize(safe_path)
            
            with open(safe_path, "r") as f:
                if start_line is not None or end_line is not None:
                    # Surgical read
                    lines = f.readlines()
                    start = max(0, (start_line or 1) - 1)
                    end = end_line or len(lines)
                    content = "".join(lines[start:end])
                    msg = f"Read lines {start+1}-{end} of {len(lines)} from {path}."
                    log_event("commands.log", msg)
                    return content
                
                if file_size > max_size:
                    msg = f"WARNING: File {path} is too large ({file_size} bytes). Truncating output to 1MB."
                    log_event("errors.log", msg)
                    content = f.read(max_size)
                    return f"{msg}\n\n{content}"
                
                content = f.read()
                log_event("commands.log", f"Read file: {path} ({file_size} bytes)")
                return content
        except Exception as e:
            log_event("errors.log", f"read_file failed for {path}: {str(e)}")
            return None
            
    log_event("errors.log", f"read_file failed: path invalid or not found: {path}")
    return None

def edit_file(path, content):
    safe_path = _enforce_sandbox(path)
    if not safe_path:
        return False
    
    try:
        os.makedirs(os.path.dirname(safe_path), exist_ok=True)
        
        # Versioned backup before overwrite
        if os.path.exists(safe_path):
            timestamp = int(time.time())
            backup_path = f"{safe_path}.{timestamp}.bak"
            with open(safe_path, "r") as f_src, open(backup_path, "w") as f_dst:
                f_dst.write(f_src.read())
            log_event("commands.log", f"Created versioned backup: {backup_path}")

        with open(safe_path, "w") as f:
            f.write(content)
        log_event("commands.log", f"Edited file: {path}")
        return True
    except Exception as e:
        log_event("errors.log", f"edit_file failed for {path}: {str(e)}")
        return False

def list_files(dir_path="."):
    safe_dir = _enforce_sandbox(dir_path)
    if safe_dir and os.path.isdir(safe_dir):
        files = os.listdir(safe_dir)
        log_event("commands.log", f"Listed files in: {dir_path}")
        return files
    log_event("errors.log", f"list_files failed: dir invalid or not found: {dir_path}")
    return []
