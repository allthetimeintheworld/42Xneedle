# Project Instructions: Hackathon Agent Setup

## Logging Protocol
Every action taken by the agent must be logged in the `agent_logs/` directory.
- Use `agent_logs/decisions.log` for high-level strategy and reasoning.
- Use `agent_logs/commands.log` for every shell command executed.
- Use `agent_logs/prompts.log` for model interactions (if applicable).

## Implementation Rules
- **Atomic Edits:** Prefer small, targeted changes over large file rewrites.
- **Verification-First:** Always run tests immediately after a change.
- **Spec-Driven:** The `secret_spec/SECRET_SPEC.md` is the absolute source of truth.

## Test Handling
- If tests fail, the agent must read the output and categorize the failure before attempting a fix.
- Failed tests should be logged in `agent_logs/test_runs.log`.

## Human Intervention
- Any manual edit or manual command run must be recorded in `agent_logs/human_interventions.log`.
