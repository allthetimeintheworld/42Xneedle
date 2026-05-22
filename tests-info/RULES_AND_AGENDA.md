# Rules & Agenda

## Agenda

### Thursday, May 21

| Time | What happens |
|---|---|
| 09:00 | Doors open, coffee, arrival, team finding |
| 10:00 | Kickoff: format, rules, judging, Q&A |
| 10:30 | Work begins: build your agent setup |
| 13:00 | Team registration deadline in Slack `#team-formation` |
| 14:00 | Snacks in the 42 café |
| 17:30 | Informal check-in with organizers |
| 19:45 | Agent readiness checkpoint |
| 20:00 | Hidden task released under `secret_spec/` |
| 21:00 | Campus closes for external participants. 42 students may continue on campus |
| Overnight | Run your agent, test, repair, maybe sleep |

### Friday, May 22

| Time | What happens |
|---|---|
| 09:00 | Campus reopens, coffee |
| 10:00 | Final check-in with organisers |
| 10:30 | Final work, public test runs, submission prep |
| 12:00 | Submissions close. This is a hard deadline. |
| 12:00 - 13:30 | Organizer pre-flight checks and presentation prep |
| 13:30 | Final tech check and presentation order |
| 14:00 | Presentations begin |
| Late afternoon | Winners, prizes, pizza, closing, networking |

Times may shift slightly. Watch Slack `#announcements`.

The Friday 12:00 submission deadline is not a vibe. If you miss it, your submission may not be judged. We will sympathize emotionally and proceed mechanically, like a very small court of robots.

---

## Teams and registration

Teams may have 1-4 people.

Teams must be registered by 13:00 on Thursday in Slack `#team-formation`.

To register, post one message in this format:

```text
Team name:
Members:
Repo URL:
Repo visibility: public/private
Organizer access if private:
```

Example:

```text
Team name: Segfault Society
Members: Michael Oval, Britney Spiercing, Barak Obama
Repo URL: https://github.com/example/team-fabulous
Repo visibility: private
Organizer access if private: invited @anavoronkova
```

Rules:

- max 4 people per team;
- each team must create its own Git repository;
- public repositories are fine;
- private repositories are fine, but organizers/judges must be invited before submission;
- the team repository is where your agent, logs, final program, and commit history live;
- the public hackathon repository is only for event materials and reveal materials.

Teams that do not register by 13:00 may not be included in judging logistics. This is not meant to be dramatic. We just need to know which teams exist before the entire event turns into a spreadsheet seance.

---

## What this hackathon is about

This is not a normal “build an app” hackathon.

Your task is to build an **autonomous coding-agent setup**.

That means a system that can:

- read a technical specification it has not seen before;
- plan an implementation;
- write code;
- run tests;
- inspect failures;
- repair mistakes;
- rerun tests;
- keep useful logs of what happened.

The final program matters, but the real project is the **agent workflow**.

Judges will look at both:

1. what your system produced;
2. how your system produced it.

A solution that passes many tests is good. A solution that passes tests and shows a clear autonomous build-repair loop is better.

This is a systems-engineering challenge, not a typing contest.

---

## What you know before the reveal

Before 20:00, you know only the general shape of the hidden task:

> The hidden task will be a CLI-based programming challenge based on a precise technical specification.

You will not know the exact domain or full requirements until the 20:00 release.

During the day, your goal is not to solve the hidden task. You cannot. It is hidden. Mysterious, but not in a romantic way.

Your goal is to prepare an agent that can solve an unfamiliar technical task once the specification is released.

---

## Thursday daytime: build your agent setup

Use the day to build and test your agent workflow.

By the evening, your setup should ideally be able to:

- read a Markdown specification;
- create an implementation plan;
- edit files;
- run shell commands;
- run tests;
- inspect test output;
- decide what to fix next;
- patch code;
- rerun tests;
- save logs;
- preserve prompts and commands;
- track changes with git or another clear history mechanism.

You may test your agent on any toy tasks during the day.

Examples of useful toy tasks:

- build a small CLI tool from a short spec;
- implement a small structured-text task;
- run a test suite and fix failures;
- generate logs of prompts, commands, and test runs.

Do not spend the whole day making a beautiful dashboard. The hidden task will not care about your dashboard. It has no heart.

---

## Where teams work

Each team should work in its **own team repository**.

This public hackathon repository contains event materials, templates, reveal placeholders, and instructions. It is not where teams submit solutions. Please do not open pull requests here with your final program. Bold choice, wrong door.

Your team repository should contain:

- the agent setup you built during the day;
- the 19:45 checkpoint commit or tag;
- the final program produced after reveal;
- logs, model disclosure, and final report;
- enough commit history for judges to understand the process.

You may make the team repository public or private, as long as judges can access it by the Thursday 13:00 deadline. If it is private, make sure access is granted before the deadline. “I invited you at 13:04” is not a time machine.

---

## 19:45 Agent Readiness Check

At 19:45, each team must create a checkpoint of their agent setup.

Prefer a git commit and tag in your team repository, for example:

```bash
git commit -m "Agent readiness checkpoint"
git tag agent-readiness-1945
git push --follow-tags
```

If you are not using git, use a zip archive or clearly timestamped folder snapshot. Git is preferred because judges can inspect history without performing document archaeology.

This is **not** a hard freeze.

After the hidden task is released, you may still:

- restart a crashed agent;
- fix setup problems;
- adjust prompts;
- rerun the agent;
- change model configuration;
- fix infrastructure issues;
- manually choose which agent outputs to keep.

But all human interventions after the reveal must be logged.

The checkpoint exists so judges can understand what your agent setup looked like before the task was known. Judges may compare the checkpoint with later commits to see how the agent, final program, logs, and submission evolved.

---

## After the hidden task release

At 20:00, the hidden task materials will be released under `secret_spec/`.

At that point, your agent should begin an implementation-and-repair loop:

1. read the hidden specification;
2. create a plan;
3. implement the required program;
4. run the public tests;
5. inspect failures;
6. patch the program;
7. rerun tests;
8. optionally generate additional self-tests;
9. repeat until final submission.

The overnight challenge is not to generate code once and pray.

The challenge is to build a system that can keep improving from feedback. Prayer remains optional.

---

## What humans may and may not do after 20:00

The central trust contract:

**Humans should operate the agent, not manually write the final program.**

Allowed after the reveal, if logged:

- restarting the agent;
- editing prompts;
- changing orchestration logic;
- fixing broken paths or setup issues;
- installing missing dependencies;
- rerunning tests;
- selecting between different outputs generated by the agent;
- documenting failures.

Not allowed after the reveal:

- manually writing the final program yourself;
- manually editing the final program to fix logic;
- copying a complete solution from another source;
- hiding paid model usage;
- hiding human intervention.

This is an honor-system challenge. We will not install spyware on your laptop, because apparently even hackathons deserve dignity. But we will read logs, commits, and reports.

If your logs show three vague prompts and your final code looks like it was handcrafted by a suspiciously awake senior engineer, judges may ask questions.

---

## Models and compute rules

This hackathon is about engineering around constrained intelligence.

Paid frontier-model brute force is not the spirit of the challenge.

The constraint is part of the game: local/free models are weaker, cheaper, and less obedient. Your job is to engineer around that, not quietly rent a digital god and call it architecture.

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

If access is paid by someone — you, your school, your employer, your friend’s startup, a mysterious benefactor, or a cloud deity with VC funding — it counts as paid access.

If you have Copilot or another paid assistant enabled in your editor, disable it for post-reveal implementation. Paid autocomplete still counts if it writes or suggests code for the hidden task. The machines are sneaky; we noticed.

### Before 20:00

Before the reveal, you may use your normal tools to prepare your agent framework and infrastructure.

### After 20:00

After the reveal, the hidden-task implementation must be produced through allowed local/free/open model access and your disclosed agent setup.

This is an honor-system rule. Dishonest or unclear disclosure may reduce or invalidate your autonomy/process score.

---

## Model disclosure

Every submission must include an `agent_manifest.json`.

Example:

```json
{
  "primary_model": "qwen2.5-coder:7b",
  "provider": "Ollama",
  "additional_models": [
    {
      "model": "llama3.1:8b",
      "provider": "Ollama",
      "purpose": "reviewing test failures"
    }
  ],
  "paid_frontier_models_used_after_spec_release": false,
  "copilot_or_paid_ide_assistant_used_after_spec_release": false,
  "institutional_or_work_model_quota_used_after_spec_release": false,
  "notes": "Qwen generated code, Llama reviewed failed tests. No paid Copilot, work, school, or enterprise model quota was used after spec release."
}
```

Do not commit API keys, tokens, passwords, or private configuration.

---

## Logging requirements

Your final submission must include an `agent_logs/` folder.

Required files:

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

Logs must include timestamps.

### `prompts.log`

Human prompts and instructions sent to the agent after the hidden task release.

Example:

```text
[2026-05-21 20:18] USER_PROMPT:
Read the hidden specification and create an implementation plan. Do not write code yet.
```

### `decisions.log`

Important agent decisions.

Example:

```text
[2026-05-21 20:31] DECISION:
The agent decided to implement CLI handling first, then valid parsing, then invalid cases.
```

### `commands.log`

Shell commands run by the agent or by humans.

Example:

```text
[2026-05-21 21:04] COMMAND:
python3 secret_spec/test_runner/run_tests.py --program "python3 solution.py" --suite public
```

### `test_runs.log`

Public test runs and score progression.

Example:

```text
[2026-05-21 22:15] TEST_RUN:
Public score: 137/250.
Main failing categories: row expansion, invalid output schema.
```

### `errors.log`

Important crashes, tool failures, model failures, or repeated loops.

### `human_interventions.log`

Manual actions after reveal.

Example:

```text
[2026-05-21 21:16] HUMAN_INTERVENTION:
Installed pytest because the agent could not run tests. No final program code was edited manually.
```

Blank file is fine if there were no interventions. Missing file is not fine. Missing file says “trust me,” and unfortunately we have met software people.

---

## Public and hidden tests

After the hidden task release, public tests and runner instructions will be released under `secret_spec/`.

Public tests are for iteration.

Hidden tests are for final judging.

Hidden tests:

- are based on the same specification;
- do not test behavior outside the specification;
- combine rules more aggressively than public tests;
- are not visible before judging.

Exact error-message wording is not judged unless the hidden specification explicitly says otherwise.

Do not generate expected outputs using your own solution. If organizer tooling appears in the repository, do not use it unless the instructions explicitly say so. Grading yourself with your own answer key is bold, but not useful.

---

## Final program requirements

The hidden specification will define the exact required command and behavior.

In general:

- stdout discipline matters;
- exit codes matter;
- JSON shape may matter;
- no debug text in stdout;
- no extra commands or flags unless required;
- behavior not defined in the hidden specification will not be judged.

If your program only works on your laptop because of a secret path, hidden environment variable, or local ritual sacrifice, it does not work.

---

## Final submission

By Friday 12:00, your team must submit a link to its **own team repository**. Do not submit your solution to this public hackathon materials repository.

The submitted team repository must contain:

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
requirements.txt or pyproject.toml if needed
final program files
agent code or process evidence
```

Your `README.md` must include:

- exact command to run your final program;
- Python version;
- dependency installation instructions;
- one-paragraph overview of your agent architecture;
- link or reference to the 19:45 checkpoint commit/tag;
- how to reproduce the public test run, if possible.

See [`SUBMISSION.md`](./SUBMISSION.md) for the detailed checklist.

---

## `final_report.md`

Your final report must include:

- models used;
- tools available to the agent;
- agent architecture;
- prompting strategy;
- test strategy;
- score progression;
- human interventions;
- what worked;
- what failed;
- what you would improve.

Do not write a marketing essay. Write the kind of report that helps judges understand what actually happened.

---

## Presentation

Each team gets approximately 5 minutes, plus a short Q&A.

Focus on:

- your agent architecture;
- model(s) used;
- tools available to the agent;
- how the agent planned;
- how the agent tested;
- how it responded to failures;
- public score progression;
- logs and timestamps;
- human interventions;
- final result;
- what you would improve.

Do not spend your whole presentation walking through implementation details of the final program. We care more about the system that produced it.

The final program is the battlefield. The agent is the project.

---

## Live judging procedure

At the start of each presentation slot:

1. Team opens their submitted team repository.
2. Team shows the 19:45 checkpoint and recent commits.
3. Team confirms there are no uncommitted changes.
4. Team runs the public score command if requested.
5. Judges run or review the hidden score.
6. Team presents the agent architecture and process.
7. Judges ask questions.

The same procedure applies to every team. This is not suspicion-driven; it is fairness-driven. Tiny bureaucracy, but the useful kind.

---

## Scoring

See [`JUDGING_CRITERIA.md`](./JUDGING_CRITERIA.md) for the full rubric.

Suggested breakdown:

- **40% hidden test score**
- **20% public test score / final public performance**
- **20% agent autonomy and process evidence**
- **10% self-generated tests / hardening strategy**
- **10% presentation and failure analysis**

Missing logs do not automatically disqualify a team, but they reduce the autonomy/process score.

Undisclosed paid model usage after the reveal may reduce or invalidate the autonomy/process score.

---

## Disqualification and penalties

Automatic disqualification may happen for:

- missing the Friday 12:00 submission deadline;
- using paid model access after the reveal without disclosure;
- manually writing the final program after the reveal;
- submitting code your team did not produce.

Partial scoring penalties may happen for:

- missing logs;
- incomplete model disclosure;
- unclear dependencies;
- missing final report;
- hidden human interventions;
- broken run instructions.

Open-source libraries are allowed as dependencies if disclosed. Copying an existing complete solution to the hidden task is not allowed. Obviously. Somehow we still have to say it.

---

## Questions during the event

Use Slack.

- `#announcements` — official updates and clarifications
- `#help` — general questions
- `#setup` — model, environment, and agent setup questions
- `#public-tests` — public test runner questions after reveal
- `#submissions` — submission questions

If a clarification affects the hidden task or judging, it will be posted for everyone in `#announcements`.

Do not DM organizers for private spec clarifications during the overnight run. That gives your team unfair information, and also we are not trying to become a 24-hour helpdesk staffed by ghosts.

---

## Spirit of the event

This is an experiment.

You are not building features for a sponsor. You are building a system that can do engineering work from a specification, under constraints, with evidence.

If it works, it is exciting.

If it fails, the failure modes will probably be informative and mildly cursed.

Either way: build the agent, document everything, and make the process visible.
