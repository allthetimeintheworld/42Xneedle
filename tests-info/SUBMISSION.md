# Submission Requirements

This document explains what your team must submit by **Friday 12:00**.

The short version: submit the final program, the agent that produced it, the logs showing what happened, and enough instructions for judges to run your work without becoming archaeologists.

The final task details will be released under `secret_spec/` at 20:00 on Thursday. Until then, this document describes the submission structure and process.

---

## Where to work

Each team works in its **own team repository**.

This public hackathon repository is only for event materials, templates, and reveal files. It is not the submission target. Do not submit your final program here; the judges will not go hunting through pull requests in the event repo. They have enough hobbies.

Your team repository is where you should keep:

- your agent setup;
- your 19:45 checkpoint commit or tag;
- your final program;
- logs and reports;
- dependency files;
- enough process evidence for judges to understand how the final program was produced.

The repository may be public or private, but judges must be able to access it by the Friday 12:00 deadline.

---

## 19:45 checkpoint

At **19:45 on Thursday**, create a checkpoint in your team repository before the hidden task is released at **20:00**.

Recommended:

```bash
git commit -m "Agent readiness checkpoint"
git tag agent-readiness-1945
git push --follow-tags
```

The checkpoint should capture the agent setup as it existed before the hidden task was known. After 20:00, you may continue committing changes as your agent runs, fixes issues, produces logs, and builds the final program.

Judges may inspect the checkpoint, later commits, logs, and final report to understand the process. This is not meant to be scary. It is meant to make the timeline visible without requiring a detective board and string.

---

## Deadline

Final submissions close on:

```text
Friday, May 22 — 12:00
```

This is a hard deadline.

After 12:00, organizers begin pre-flight checks and judging preparation. If your team submits late, your project may not be judged.

We will be emotionally understanding and operationally unforgiving. A classic combination.

---

## What to submit

Submit the URL of your team repository by the deadline.

The submitted team repository should contain:

```text
README.md
agent_manifest.json
agent_logs/
  prompts.log
  decisions.log
  commands.log
  test_runs.log
  errors.log
  human_interventions.log
  final_report.md
final program files
agent code or process evidence
dependency files, if needed
```

Your final program files are whatever the hidden specification requires.

Do **not** assume the exact entrypoint before the hidden task is released. The released spec is the source of truth.

---

## Required files

### 1. Final program

Your repository must contain the program your agent built after the hidden task was released.

The hidden spec will define:

- required command;
- expected input format;
- expected output format;
- exit codes;
- test behavior;
- constraints.

Judges will run your program according to the released specification.

If your entrypoint differs from the default instructions for a good reason, document the exact command clearly in `README.md`.

“Works on my machine if you stand facing north” is not a valid run instruction.

---

### 2. `README.md`

Your final submission must include a `README.md` with:

- team name;
- team members;
- exact command to run the final program;
- Python version or runtime version;
- dependency installation instructions;
- one-paragraph overview of the agent architecture;
- link or reference to the 19:45 checkpoint commit/tag;
- how to run public tests;
- known limitations.

Suggested structure:

````markdown
# Team Name

## Final command

```bash
python3 <entrypoint> <args from hidden spec>
```

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Agent overview

Short explanation of the agent architecture.

## Public test run

Command used and final public score.

## Known limitations

Anything judges should know.
````

---

### 3. `agent_manifest.json`

This file discloses model and tool usage.

Required fields:

```json
{
  "team_name": "Example Team",
  "primary_model": "qwen2.5-coder:7b",
  "provider": "Ollama",
  "runtime_or_tool": "custom Python agent",
  "additional_models": [
    {
      "model": "llama3.1:8b",
      "provider": "Ollama",
      "purpose": "reviewing failed test summaries"
    }
  ],
  "paid_frontier_models_used_after_spec_release": false,
  "copilot_or_paid_ide_assistant_used_after_spec_release": false,
  "institutional_or_work_model_quota_used_after_spec_release": false,
  "model_configuration_location": "agent/config.yaml",
  "notes": "No paid model access was used after the hidden task release."
}
```

If a model, tool, IDE assistant, or API touched the hidden-task implementation after 20:00, disclose it.

Do not include API keys, tokens, passwords, or private credentials. Judges want disclosure, not your security incident.

---

### 4. `agent_logs/`

Your submission must include:

```text
agent_logs/
  prompts.log
  decisions.log
  commands.log
  test_runs.log
  errors.log
  human_interventions.log
  final_report.md
```

Use the templates provided in:

```text
templates/agent_logs/
```

If the templates are not available in the repository yet, create the files manually with the same names.

Logs must include timestamps.

#### `prompts.log`

Human prompts/instructions sent to the agent after the hidden task release.

#### `decisions.log`

Important agent decisions and strategy changes.

#### `commands.log`

Commands run by the agent or humans.

#### `test_runs.log`

Public test runs, scores, failure categories, and score progression.

#### `errors.log`

Agent crashes, model failures, tool failures, repeated loops, corrupted outputs, and other operational problems.

#### `human_interventions.log`

Every human action after the hidden task release that affected the agent, environment, prompts, test loop, or final solution.

If there were no human interventions, write:

```text
No human interventions after hidden task release.
```

Missing `human_interventions.log` is suspicious. Not mysterious. Suspicious.

#### `final_report.md`

Your final report should explain what happened, what worked, what failed, and how the agent produced the final program.

Use the provided template if available.

---

### 5. Dependency files

If your final program or agent needs dependencies, include one of:

```text
requirements.txt
pyproject.toml
environment.yml
package.json
```

Use pinned versions where possible.

Good:

```text
pytest==8.4.2
pydantic==2.8.2
```

Less good:

```text
just install whatever probably works
```

That second one is not a dependency strategy. It is a cry for help.

If no dependencies are needed, say so in `README.md`.

---

### 6. Agent code

Include the code for your agent setup if possible.

This may include:

```text
agent/
  run_agent.py
  prompts/
  tools/
  config/
  logs/
```

Judges are interested in the system that produced the final program, not only the final program itself.

If your agent uses an external tool or UI that cannot be fully submitted, document:

- tool name;
- model used;
- prompts used;
- configuration;
- what the tool did;
- logs or exports where possible.

---

## What not to include

Do **not** include:

- API keys;
- tokens;
- passwords;
- private credentials;
- paid model account credentials;
- hidden test guesses;
- copied hidden tests;
- private expected outputs;
- reference implementation code;
- organizer scripts not explicitly released to participants;
- large local model files;
- `.venv/`;
- `__pycache__/`;
- massive generated junk folders.

If your submission is 4 GB because you committed a model file, a virtual environment, and the entire emotional history of your terminal, judges will not thank you.

---

## Human intervention disclosure

After the hidden task release, humans may operate the agent, restart it, adjust prompts, fix setup issues, and choose between agent-generated outputs.

Humans may **not** manually write the final program logic.

Every human intervention must be logged in:

```text
agent_logs/human_interventions.log
```

Use this format:

```text
[YYYY-MM-DD HH:MM] TYPE
What happened:
Why:
Files or settings affected:
Touched final task code directly: yes/no
Notes:
```

Logging a forbidden action does not magically make it allowed. It only makes it honest, which is still better than hoping nobody notices.

---

## Pre-flight checks after submission

After the 12:00 deadline, organizers may clone your submitted team repository and perform setup checks.

They may check:

- repository can be cloned;
- checkpoint commit/tag is present or clearly documented;
- dependencies can be installed;
- final command runs;
- public test runner can run;
- logs exist;
- model disclosure exists;
- no obvious secrets are committed.

If there is a setup-only problem, organizers may contact you during the pre-flight window.

You may fix setup files if organizers allow it, for example:

- `README.md`;
- dependency files;
- invocation script;
- path typo.

You may not edit final program logic or agent logic after the submission deadline.

The difference between “the command path is wrong” and “I rewrote the parser” is not subtle. Please do not make us litigate it.

---

## Presentation preparation

Your presentation should focus on the agent system, not only the final program.

Prepare to explain:

- model(s) used;
- agent architecture;
- tool access;
- prompting strategy;
- test loop;
- score progression;
- failures;
- human interventions;
- final result;
- what you would improve.

Do not spend five minutes walking through implementation details of the final program. The final program matters, but the agent is the project.

---

## Submission checklist

Before submitting, confirm:

- [ ] Team repository URL is ready to submit.
- [ ] Judges can access the repository.
- [ ] 19:45 checkpoint commit/tag exists or is clearly documented.
- [ ] Final program files are included.
- [ ] `README.md` exists.
- [ ] Exact run command is documented.
- [ ] Dependencies are documented.
- [ ] `agent_manifest.json` exists.
- [ ] Model usage is disclosed.
- [ ] Paid model / Copilot / institutional quota fields are filled honestly.
- [ ] `agent_logs/prompts.log` exists.
- [ ] `agent_logs/decisions.log` exists.
- [ ] `agent_logs/commands.log` exists.
- [ ] `agent_logs/test_runs.log` exists.
- [ ] `agent_logs/errors.log` exists.
- [ ] `agent_logs/human_interventions.log` exists.
- [ ] `agent_logs/final_report.md` exists.
- [ ] Human interventions are disclosed.
- [ ] Public score is recorded.
- [ ] No API keys, tokens, passwords, or private credentials are committed.
- [ ] No large model files or virtual environments are committed.
- [ ] Final submission commit hash is noted.
- [ ] Presentation focuses on the agent system.

---

## Recommended final folder structure

You do not have to follow this exactly, but something close will make judges happier and less feral.

```text
your-team-repository/
  README.md
  agent_manifest.json
  requirements.txt
  final_program_file_or_folder/
  agent/
  agent_logs/
    prompts.log
    decisions.log
    commands.log
    test_runs.log
    errors.log
    human_interventions.log
    final_report.md
```

If your structure is different, explain it clearly in `README.md`.

---

## Final note

A good submission is not just a working program. It is a clear record of how your agent tried, failed, recovered, and improved.

That record is part of the project.

Make it easy for judges to see what happened. Future-you at 11:55 on Friday will also appreciate this, assuming future-you still believes in file organization.
