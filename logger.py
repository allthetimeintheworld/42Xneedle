import logging
from pathlib import Path
from datetime import datetime


Path("agent_logs").mkdir(exist_ok=True)


def get_logger(name):
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.FileHandler(f"agent_logs/{name}.log")
        handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def log_intervention(message):
    with open("agent_logs/human_interventions.log", "a") as f:
        f.write(f"{datetime.utcnow().isoformat()}Z {message}\n")
