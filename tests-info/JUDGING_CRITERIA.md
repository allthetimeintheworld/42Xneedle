# Judging Criteria

Judging is based on both the final result and the process that produced it.

This is not a normal coding contest where only the final program matters. It is also not a theater contest where beautiful logs can fully compensate for broken code. Annoyingly, both things matter.

## Scoring breakdown

| Category | Weight |
|---|---:|
| Hidden test score | 40% |
| Public test score / final public performance | 20% |
| Agent autonomy and process evidence | 20% |
| Self-generated tests / hardening strategy | 10% |
| Presentation and failure analysis | 10% |

---

## 1. Hidden test score — 40%

The hidden test suite is the main correctness score.

Hidden tests are based on the same hidden specification as the public tests. They do **not** test secret extra rules or undefined behavior.

They may, however, combine rules more aggressively than the public tests.

This category measures whether your final program generalizes beyond the visible public tests.

Correctness matters. The agent is the project, but the final program still has to do the job. We are romantic about process, not delusional about output.

---

## 2. Public test score / final public performance — 20%

The public test suite is released after the hidden task reveal and is available for iteration.

Judges may look at:

- final public score;
- public score progression over time;
- which categories improved;
- whether the agent used public failures as feedback;
- whether fixes caused regressions.

A final public score is useful. A score progression showing steady autonomous repair is even more useful.

If your score jumps from 12/150 to 120/150 with no logs, no commits, and no explanation, that is not impressive. That is suspicious with better branding.

---

## 3. Agent autonomy and process evidence — 20%

This category measures whether you built a real agent workflow, not just a human-operated code generator.

Judges may inspect:

- the 19:45 checkpoint commit or tag;
- commits after the hidden task release;
- diff between checkpoint and final submission;
- agent code;
- prompts;
- command history;
- public test run history;
- logs;
- model disclosure;
- human intervention log;
- final report.

Strong evidence includes:

- timestamped logs;
- clear prompts;
- repeated implementation-test-repair loops;
- public test failures influencing later changes;
- small targeted patches;
- recovery from failed approaches;
- transparent human interventions;
- consistent commit history.

Weak evidence includes:

- missing logs;
- vague logs;
- one giant final commit;
- no prompts;
- no test history;
- unexplained polished final code;
- hidden human intervention.

Human intervention is allowed when disclosed. Hidden intervention is where trust goes to die in a ditch.

---

## 4. Self-generated tests / hardening strategy — 10%

Teams are encouraged to go beyond the public tests.

Good self-generated tests are:

- derived from the hidden specification;
- targeted at meaningful behavior;
- used to catch regressions;
- connected to known failure categories;
- documented in logs or final report.

Less useful:

- random input spam without a clear oracle;
- tests not connected to the spec;
- tests generated but never run;
- tests that only confirm already-working trivial cases.

This category rewards teams whose agents tried to harden the solution instead of merely chasing public test points like a caffeinated squirrel.

---

## 5. Presentation and failure analysis — 10%

The final presentation should explain the agent system and what happened during the overnight run.

Judges want to hear about:

- agent architecture;
- model(s) used;
- tools available to the agent;
- prompting strategy;
- test loop;
- public score progression;
- major failures;
- recovery attempts;
- human interventions;
- final result;
- what you would improve.

Do not spend the whole presentation walking through implementation details of the final program.

The final program matters, but the agent is the project.

Clear failure analysis counts. “It broke and then we panicked” is honest, but not yet analysis. Add what broke, why, what you tried, and what you learned.

---

## Notes on scoring

A manually written final program with poor process evidence may lose significant process points.

A weaker final program with strong agent architecture, clear logs, and honest failure analysis can still score well in process categories.

Correctness still matters. Process still matters. This is the whole annoying point.

Small differences in test score may be outweighed by much stronger autonomy evidence.

Large differences in test score probably will not be outweighed by nice storytelling. This is a hackathon, not a redemption arc.

---

## Penalties

Teams may lose points for:

- missing logs;
- missing model disclosure;
- unclear or inaccessible repository;
- missing 19:45 checkpoint;
- missing final commit hash;
- unclear setup instructions;
- undisclosed human interventions;
- undisclosed paid model usage;
- final program that cannot be run by judges.

Serious rule violations may lead to disqualification, especially:

- using prohibited paid model access after the hidden task release;
- manually writing the final program after the reveal;
- submitting work copied from another team or external source;
- missing the Friday 12:00 submission deadline.

---

## Repository evidence

Final judging uses the team repository submitted by Friday 12:00.

Teams must provide:

- repository URL;
- 19:45 checkpoint commit or tag;
- final submission commit hash;
- final public score;
- exact command to run the final program.

If the repository is private, judges must have access before the submission deadline.

If judges cannot access your repo, they cannot judge your repo. Computers are literal like that, the little monsters.
