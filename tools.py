from pathlib import Path


def read_file(path):
    return Path(path).read_text() if Path(path).exists() else ""


def edit_file(path, content):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(content)
    return {"success": True, "bytes_written": len(content), "diff_summary": f"wrote {path}"}


def list_dir(path="workspace/"):
    p = Path(path)
    return [str(f) for f in p.iterdir()] if p.exists() else []


def run_shell(cmd, timeout=60, cwd="workspace/"):
    return {"stdout": "", "stderr": "", "exit_code": 0, "duration_s": 0.0}


def run_tests():
    return {"passed": 0, "failed": 0, "errors": 0, "failure_summary": "stub", "raw_output": "stub tests"}
