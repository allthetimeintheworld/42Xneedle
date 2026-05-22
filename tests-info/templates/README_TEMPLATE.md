# Team Name

## Team members

- Name:
- Name:
- Name:

## Final command

```bash
# Replace with the exact command from the hidden spec / your implementation
python3 <entrypoint> <args>
```

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

If no dependencies are required, say so here.

## Python/runtime version

Example:

```text
Python 3.11
```

## Agent overview

Briefly describe your agent architecture.

Example:
The agent used a planner/coder/tester loop. It read the hidden spec, created an implementation plan, edited files, ran public tests, summarized failures, and patched the implementation iteratively.

## Model setup

Primary model:

Provider/runtime:

Additional models:

See `agent_manifest.json` for full disclosure.

## Public test result

Final public score:

Command used:

```bash
python3 secret_spec/test_runner/run_tests.py --program "python3 <entrypoint>" --suite public
```

## Known limitations

List known issues or incomplete areas.

## Repository structure

Briefly explain where the final program, agent code, and logs are located.
