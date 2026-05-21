import os

def load_env(filepath=".env"):
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    try:
                        key, value = line.split("=", 1)
                        os.environ[key.strip()] = value.strip()
                    except ValueError:
                        continue

load_env()

# Configuration
LOG_DIR = "agent_logs"
SPEC_PATH = "secret_spec/SECRET_SPEC.md"
MAX_ITERATIONS = 40 # Increased for more complex autonomous tasks
LOOP_DELAY = int(os.environ.get("LOOP_DELAY", 2))

# Model Fallback Lists (Priority Order)
GROQ_MODELS = ["llama-3.3-70b-versatile", "llama-3.1-70b-versatile", "llama-3.1-8b-instant"]
MISTRAL_MODELS = ["mistral-large-latest", "mistral-small-latest"]
DEEPSEEK_MODELS = ["deepseek-chat"]

PLANNER_MODEL = GROQ_MODELS[0]
CODER_MODEL = GROQ_MODELS[0]

# API Keys
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL")
