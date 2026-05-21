# 42-X-Needle-Agent Setup

> **TASK SOURCE OF TRUTH**: The active task specification is located in `secret_spec/SECRET_SPEC.md`. 
> Do not waste iterations reading this README for task requirements; it is for setup only.

## Quick Start
1. **Initialize Environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install openai requests
   ```
2. **Configure Credentials**:
   Copy `.env.template` to `.env` and fill in your keys:
   ```bash
   cp .env.template .env
   # Ensure GROQ_API_KEY is set in .env
   ```
3. **Run the agent**:
   ```bash
   python3 -m agent.main
   ```

## Architecture
- **`agent/main.py`**: Core loop and orchestration.
- **`agent/llm.py`**: OpenAI SDK integration.
- **`agent/tools/`**: Modular file, shell, and parsing tools.
- **`orchestrator/`**: Multi-role (Architect, Researcher, Reviewer) prompts.

## Logging
Check `agent_logs/` for:
- `decisions.log`: High-level strategy.
- `commands.log`: Shell commands and file I/O.
- `test_runs.log`: Detailed test output.
- `prompts.log`: Full LLM context and responses.

## Checkpoint (19:45)
```bash
git add .
git commit -m "42-X-Needle-Agent: Modular refactor complete"
git tag agent-readiness-1945
git push --follow-tags
```
