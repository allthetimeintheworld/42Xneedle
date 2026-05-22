# 42 Berlin x Needle Agent Hackathon

This is an autonomous coding-agent hackathon. Teams build an agent setup during the day, receive a hidden technical specification in the evening, then use their agent to implement, test, repair, and harden the hidden-task solution overnight.

The reveal materials are intentionally not here yet. Before 20:00 on Thursday, May 21, 2026, `secret_spec/` contains placeholders only. No hidden task spec, public tests, test runner, hidden tests, reference implementation, expected outputs, or private judging scripts are included.

This repository contains the event materials only. Teams should not submit their solutions here. Each team works in its own repository. Register your team repository by **13:00 on Thursday**; see [Teams](#teams).

## What this is

This is not a normal app hackathon. The final artifact matters, but the real project is the agent system: how it reads specs, writes code, runs tests, inspects failures, repairs mistakes, logs decisions, and improves under constrained AI resources.

Paid frontier-model brute force is not the spirit of the challenge. Local, free, and open models are encouraged. All model usage must be disclosed, and logs plus process evidence matter.

## Key dates / rough flow

- Thursday daytime: build and test your coding-agent setup.
- 19:45: agent readiness checkpoint in your own team repository.
- 20:00: hidden spec, public tests, and public runner instructions appear under `secret_spec/`.
- Overnight: agent implementation, testing, repair, and hardening loop.
- Friday: final work, submission, judging, presentations, closing.

See the full schedule in [Rules & Agenda](./RULES_AND_AGENDA.md).

## Start here

1. [Rules & Agenda](./RULES_AND_AGENDA.md)
2. [Agent Setup Spec](./AGENT_SPEC.md)
3. [Submission Requirements](./SUBMISSION.md)
4. [Judging Criteria](./JUDGING_CRITERIA.md)

## Teams

Teams may have **1-4 people**.

Please register your team in Slack `#team-formation` by **13:00 on Thursday**.

Each team must work in its own Git repository. Public repositories are fine. Private repositories are also fine, but organizers/judges must be invited before submission.

The public hackathon repo is only for event materials and reveal materials. Do not push your team solution here. It has enough going on.

Registration format:

```text
Team name:
Members:
Repo URL:
Repo visibility: public/private
Organizer access if private:
```

Teams that do not register by 13:00 may not be included in judging logistics. In other words: please confirm your team exists before asking us to judge its masterpiece.

## Reveal materials

At **20:00 on Thursday, May 21, 2026**, the hidden task materials will be released under:

- [`secret_spec/SECRET_SPEC.md`](./secret_spec/SECRET_SPEC.md)
- [`secret_spec/public_tests/`](./secret_spec/public_tests/)
- [`secret_spec/test_runner/`](./secret_spec/test_runner/)

## What teams should build before 20:00

Before the hidden spec release, teams should build an agent workflow that can:

- read a technical specification;
- create or update source files;
- run shell commands and tests;
- inspect failures;
- patch code;
- repeat the loop without constant hand-holding;
- record prompts, decisions, commands, tests, errors, and human interventions.

Use toy tasks and your own experiments to stress-test the loop. A beautiful architecture that cannot run a test command is still, regrettably, mostly vibes.

## What happens at checkpoint and reveal

At 19:45, teams create a readiness checkpoint in their own team repositories. At 20:00, reveal materials are published under `secret_spec/`:

- `secret_spec/SECRET_SPEC.md`
- `secret_spec/public_tests/`
- `secret_spec/test_runner/`

Teams then use their agent setup to implement the final program, run public tests, inspect failures, patch, rerun, and optionally generate additional self-tests.

Manual intervention is allowed, but it must be logged and disclosed.

## Public tests

Public tests are for iteration and feedback. They are not the final judge. Hidden tests are used for final correctness scoring and are based on the same specification.

When the public tests are released, follow the instructions in [secret_spec/public_tests/README.md](./secret_spec/public_tests/README.md) and [secret_spec/test_runner/README.md](./secret_spec/test_runner/README.md). Do not assume `run_tests.py` exists before reveal. If it is not there, it has not been released. That is not a bug; it is suspense with a filesystem.

## Submission summary

Submissions are due **Friday at 12:00**.

Each team submits a link to its **own team repository**.

Your final submission should include:

- final program;
- `README.md` with setup + run command;
- `agent_manifest.json`;
- `agent_logs/`;
- dependency files, if needed;
- agent code or enough process evidence for judges to understand how the final program was produced.

Use the templates in `templates/`.

Full checklist: [`SUBMISSION.md`](./SUBMISSION.md)

## Questions / Slack channels

Use [Slack](https://join.slack.com/t/42xneedlehackathon/shared_invite/zt-3ysidof2-_1IN5YGPHochMznTYg) for operational questions and updates:

- `#announcements` for official clarifications;
- `#help` for general questions;
- `#setup` for setup, model, and agent environment issues;
- `#public-tests` for public test suite questions.

Build the agent. Let it fight the tests. Report honestly what happened.
