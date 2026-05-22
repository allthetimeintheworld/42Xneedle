# Agent Setup Specification

This document describes what your agent setup should be able to do by the **19:45 checkpoint on Thursday**, shortly before the hidden task is released at **20:00**.

It does not prescribe a specific framework or architecture. You can use a custom script, a simple loop, an existing agent framework, or a combination of tools. What matters is that your setup can take an unfamiliar technical specification, produce code, run tests, inspect failures, and keep improving with minimal human intervention.

The hidden task itself will be released separately under `secret_spec/`.

---

## Goal

By the 19:45 checkpoint, your team should have a working agent setup that can:

1. read a technical specification;
2. plan an implementation;
3. write or modify files;
4. run commands and tests;
5. inspect failures;
6. repair its own work;
7. repeat the cycle;
8. keep logs of what happened.

The goal is not to build the most complicated agent framework. A simple, reliable loop is better than a beautiful architecture that collapses at the first missing dependency.

---

## Required capabilities

### 1. Read a specification

Your agent should be able to read a Markdown file describing the hidden task.

It should treat the specification as the source of truth. If the public tests and the specification seem to disagree, ask organizers in the correct Slack channel. Do not quietly invent a third interpretation. Software already has enough folklore.

Your agent should be able to extract:

- required command-line behavior;
- input format;
- output format;
- error handling rules;
- edge cases;
- constraints;
- test expectations.

---

### 2. Create an implementation plan

Your agent should be able to break the task into smaller steps.

For example:

- parse the specification;
- identify required files;
- implement the minimal command first;
- add support for valid cases;
- add error handling;
- run tests;
- fix failing categories.

The plan does not need to be fancy. It just needs to prevent the agent from writing a giant blob of code in a random order and then looking surprised when reality declines to cooperate.

---

### 3. Write code to disk

Your agent must be able to create and modify files in the working directory.

This means actual file edits, not only suggesting code in chat for a human to paste manually.

A useful agent setup should be able to:

- create new files;
- edit existing files;
- inspect file contents;
- keep track of what changed;
- avoid overwriting important files without reason.

---

### 4. Run commands and tests

Your agent should be able to execute shell commands and capture their output.

At minimum, it should be able to:

- run the program it is building;
- run the public test suite;
- capture stdout, stderr, and exit codes;
- save test results to logs;
- rerun tests after changes.

If your agent cannot run tests, it cannot really iterate. It is just a very confident intern with no feedback loop.

---

### 5. Read test failures

The public test output is feedback. Your agent should use it.

A good setup should be able to identify:

- which tests failed;
- which category failed;
- what the expected behavior was;
- what the actual behavior was;
- whether the failure is likely parsing, output format, exit code, or runtime behavior.

The agent does not need to understand everything perfectly. It does need to use the feedback instead of blindly regenerating the same broken code with more enthusiasm.

---

### 6. Modify code based on failures

After reading failures, your agent should attempt targeted fixes.

Good behavior:

- fix one failure category at a time;
- rerun tests after a change;
- avoid breaking passing tests;
- revert or revise if a patch makes things worse;
- keep changes small enough to understand.

Bad behavior:

- rewrite everything after every failure;
- ignore test output;
- keep applying the same failed fix;
- add random features not requested by the spec;
- fill stdout with debug logs because “it helped during development.” It did not help the judge.

---

### 7. Iterate

The hidden task is designed for an implementation-test-repair loop.

Your agent should be able to repeat:

1. inspect current state;
2. choose next action;
3. edit code;
4. run tests;
5. analyze failures;
6. patch;
7. log what happened.

One-shot generation is allowed, but it is unlikely to perform well. The task is about sustained improvement, not one lucky response.

---

### 8. Keep logs

Logs are required because judges need evidence of the agent process.

Your setup should create or maintain:

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

Logs should include timestamps.

Useful logs include:

- human prompts;
- model responses or summaries;
- commands run;
- test scores;
- error summaries;
- important agent decisions;
- human interventions;
- restarts or failed runs.

Do not log API keys, tokens, passwords, or private credentials. The judges want process evidence, not your security incident.

---

## The 19:45 checkpoint

At **19:45 Thursday**, each team should create a checkpoint of the agent setup.

The hidden specification is released at **20:00** under `secret_spec/`. The 15-minute gap is intentional: make the checkpoint first, then open the box. Very ceremonial, mildly bureaucratic.

Create this checkpoint in your **own team repository**, not in the public hackathon materials repository.

Prefer:

```bash
git commit -m "Agent readiness checkpoint"
git tag agent-readiness-1945
git push --follow-tags
```

If you are not using git, use a zip archive or clearly timestamped folder snapshot. Git is preferred because judges can inspect the submitted team repository history.

The checkpoint should show the version of your agent setup that existed before the hidden task was released.

This is not a hard freeze. After the reveal, you may still fix setup issues, adjust prompts, restart the agent, rerun tests, and make limited interventions.

However, every human intervention after the reveal must be logged in `agent_logs/human_interventions.log`.

Examples of interventions to log:

- restarting a crashed agent;
- installing a missing dependency;
- changing a model endpoint;
- editing a prompt;
- fixing a path;
- manually selecting between agent-generated outputs;
- changing the orchestration loop.

You are not punished for needing interventions. You are penalized for hiding them.

---

## What this is not

This is not a required architecture.

You do not need to implement functions with specific names. You do not need to use a particular framework. You do not need multiple agents unless that helps.

Possible approaches include:

- one Python loop;
- a ReAct-style loop;
- a planner/coder/tester setup;
- a small tool-calling agent;
- an existing framework;
- a shell-script-driven workflow;
- a custom orchestration layer.

A simple setup that can read, write, test, repair, and log is enough to be competitive.

---

## Models and compute

This hackathon is about engineering around constrained model access.

### Allowed after the hidden task release

You may use:

- local models;
- open-weight models;
- Ollama;
- LM Studio;
- llama.cpp;
- genuinely free-tier API providers;
- free public model endpoints that do not require a paid plan;
- free coding-agent tiers;
- custom scripts and wrappers;
- your own orchestration code.

### Not allowed after the hidden task release

You may not use:

- paid frontier-model access;
- paid GitHub Copilot or Copilot Chat;
- Copilot access through school, employer, organization, or bundled license;
- paid Claude, ChatGPT, Cursor, Windsurf, Devin, or similar coding-agent subscriptions;
- enterprise, student, work, or sponsored seats that provide paid model quota;
- high-end paid APIs routed through someone else’s account;
- undisclosed paid model access of any kind.

If access is paid by someone — you, your school, your employer, your company, or a mysterious benefactor with suspiciously generous cloud credits — it counts as paid access.

Before the reveal, you may use your usual tools to prepare your agent infrastructure.

After the reveal, the hidden-task implementation must be produced through allowed local/free/open model access and your disclosed agent setup.

---

## Suggested tools

You are free to choose your stack.

Useful capabilities to consider:

- file reading and writing;
- shell command execution;
- test runner execution;
- structured logging;
- git commits or snapshots;
- prompt templates;
- state tracking between iterations;
- a way to summarize test failures;
- a way to prevent the agent from rewriting everything unnecessarily.

Possible model/tool options:

- Ollama with Qwen, Llama, DeepSeek, Mistral, or similar;
- LM Studio;
- llama.cpp;
- free model APIs;
- a custom Python agent;
- existing agent frameworks;
- plain shell scripts plus model calls.

Do not pick a framework just because it has an impressive diagram. If a loop with five functions works, use the loop with five functions. The universe will survive.

---

## Minimal loop example

This is only an example. Your agent can look different.

```python
state = {
    "spec_path": "secret_spec/SECRET_SPEC.md",
    "last_test_result": None,
    "iteration": 0,
}

while state["iteration"] < MAX_ITERATIONS:
    decision = ask_model_for_next_step(state)

    if decision["action"] == "edit_file":
        edit_file(decision["path"], decision["content"])

    elif decision["action"] == "run_tests":
        state["last_test_result"] = run_public_tests()

    elif decision["action"] == "stop":
        break

    log_iteration(state, decision)
    state["iteration"] += 1
```

The hard parts are not the loop itself. The hard parts are deciding what context to give the model, how to parse its output, how to recover from mistakes, and how to avoid making the same broken change ten times in a row like a tiny automated tragedy.

---

## What “ready” looks like at 19:45

A team is ready if they can:

1. copy the released hidden spec into the agent workspace once it appears at 20:00;
2. start the agent with one clear command;
3. let it read the spec;
4. let it produce code;
5. let it run tests;
6. let it repair failures;
7. come back to logs, commits, and a final result.

A team is not ready if, at 19:45, they are still:

- choosing a model;
- figuring out how to call the model;
- setting up file editing;
- setting up command execution;
- writing the first prompt;
- creating the first log file;
- discovering that their tool loop only works in theory.

Build something simple and working before trying to build something elegant.

---

## What judges will look for

Judges will look for evidence that:

- your agent had a real implementation loop;
- prompts and model usage were disclosed;
- test results influenced later actions;
- logs are clear and timestamped;
- human interventions are disclosed;
- the agent recovered from failures;
- the final result was produced by the agent workflow, not manually written after the reveal.

A strong submission shows both code and process.

If the final program works but the logs are empty, the process score suffers. If the agent fails but the logs clearly show a thoughtful system, that still earns process credit.

---

## Practical preparation checklist

Before 20:00, check that your setup can:

- [ ] call the model you plan to use;
- [ ] read a Markdown spec;
- [ ] create and edit files;
- [ ] run shell commands;
- [ ] run a test command;
- [ ] capture stdout and stderr;
- [ ] save logs with timestamps;
- [ ] preserve human prompts;
- [ ] track changes with git or snapshots;
- [ ] restart cleanly if the process crashes;
- [ ] run without paid post-reveal model access;
- [ ] produce an `agent_manifest.json`;
- [ ] produce `agent_logs/`.

Do this before the reveal. Debugging your model API at 20:07 is not a commendable strategy.

---

## Final note

Do not overbuild.

The goal is not the fanciest architecture. The goal is a working agent loop that can make progress on an unfamiliar task, use tests as feedback, and show what happened.

Clear, boring, reliable systems usually beat elaborate systems that only work in a demo. Annoying, but true.
