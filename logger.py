import logging
import re
from datetime import datetime, timezone
from pathlib import Path


LOG_DIR = Path("agent_logs")
VALID_LOGGERS = ("prompts", "decisions", "commands", "test_runs", "errors")

LOG_DIR.mkdir(exist_ok=True)

_current_iteration = -1
_loggers: dict[str, logging.Logger] = {}
_ITER_RE = re.compile(r"(?:^|\s)iter (-?\d+)(?:\s|$)")


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def set_iteration(n: int) -> None:
    """Set the current loop iteration for subsequent logger output."""
    global _current_iteration
    _current_iteration = n


def get_iteration() -> int:
    """Return the current loop iteration, or -1 before the loop has started."""
    return _current_iteration


class IterationFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        message = record.getMessage()
        iteration = get_iteration()
        if iteration < 0:
            match = _ITER_RE.search(message)
            if match:
                iteration = int(match.group(1))
        iter_str = f"[iter {iteration}]" if iteration >= 0 else "[iter -]"
        line = f"{_timestamp()} {iter_str} {message}"
        if record.exc_info:
            line = f"{line}\n{self.formatException(record.exc_info)}"
        return line


class FlushingFileHandler(logging.FileHandler):
    def emit(self, record: logging.LogRecord) -> None:
        super().emit(record)
        self.flush()


def get_logger(name: str) -> logging.Logger:
    """Return a cached logger that writes to agent_logs/<name>.log."""
    if name not in VALID_LOGGERS:
        valid = ", ".join(VALID_LOGGERS)
        raise ValueError(f"unknown logger name: {name}. Valid names: {valid}")

    if name in _loggers:
        return _loggers[name]

    LOG_DIR.mkdir(exist_ok=True)
    logger = logging.getLogger(f"agent.{name}")

    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()

    handler = FlushingFileHandler(LOG_DIR / f"{name}.log", mode="a", encoding="utf-8")
    handler.setFormatter(IterationFormatter())
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    _loggers[name] = logger
    return logger


def log_intervention(message: str) -> None:
    """Append a timestamped human intervention message."""
    LOG_DIR.mkdir(exist_ok=True)
    with open(LOG_DIR / "human_interventions.log", "a", encoding="utf-8") as f:
        f.write(f"{_timestamp()} {message}\n")
        f.flush()
