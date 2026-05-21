# Phase 5 — Build `context.py`

## Why this phase is different

The previous four phases were plumbing. This one is product.

Your orchestrator, tools, model wrapper, and logger are all generic — they would work for any agentic coding task. `context.py` is where the agent's *behavior* lives. The system prompt determines whether the model uses the test suite as feedback or guesses. The tool descriptions determine whether it reads files before editing them or hallucinates content. The trajectory summary determines whether it remembers what it tried 10 iterations ago.

Anthropic's own published advice: the single highest-leverage thing you can do for an agent's performance is prompt-engineer its tool descriptions and system prompt. Spend disproportionate time here.

This phase has no clever architecture. It is mostly writing — careful, opinionated writing that teaches the model how to behave.

## Status check before starting

- [ ] `agent.py`, `logger.py`, `tools.py`, `model.py` are all real implementations (no stubs left)
- [ ] All four module tests pass
- [ ] `python agent.py --spec dummy_spec.md` runs end-to-end without crashing
- [ ] `context.py` is still the temporary stub
- [ ] You have at least one successful `call_model` round-trip logged in `agent_logs/prompts.log` from Phase 4 verification

If any of those are not true, fix them first.

## What you're building

The context layer — three functions that build the prompts the model sees on every call:

- `build_planning_prompt(spec_text)` — used once at startup to break the spec into steps
- `build_context(state)` — used on every iteration to ask the model "what should I do next?"
- `summarize_trajectory(recent_actions)` — used to compress old history when the action log grows past 8 entries

These functions assemble the strings that determine whether your agent thrashes or makes steady progress. They are the product surface of your agent.

## Files this phase produces

- `context.py` — replaces the existing stub
- `test_context.py` — verification suite, runnable as `python test_context.py`
- `prompts/` — directory containing the prompt templates as separate `.txt` files (easier to edit than Python multiline strings)

No other files modified.

## Design principles (from Anthropic's published guidance)

These principles shape every decision below. Re-read them before tuning prompts.

1. **Gather → act → verify, in a loop.** The model should always be in one of three modes. Tell it so explicitly. Tell it that running tests is the verification step and that it must run tests after meaningful changes.

2. **Tool descriptions are prompt engineering.** Each tool description should read like an onboarding doc for a new engineer: when to use it, when not to, what to expect back, what pitfalls to avoid.

3. **Return meaningful context, not raw dumps.** When the prompt includes test output, file lists, or trajectory history, summarize aggressively. The model has limited context. Every token included in the prompt is a token not available for reasoning.

4. **Educational errors.** When something failed, the prompt should explain *why* and *what to try differently*, not just report the failure.

5. **One decision per turn.** Reinforce that the model picks exactly one action. Do not let it try to chain multiple actions in a single response — the orchestrator does not support it, and the model's reasoning degrades when it tries to plan too far ahead.

## How to run this phase

Phase 5 is different from earlier phases — Codex can scaffold the code, but the prompt content itself is iterative. The recommended workflow:

1. Have Codex generate the scaffolding (function structure, prompt file loading, JSON schema for outputs).
2. You hand-write the actual prompt content in `prompts/system.txt`, `prompts/decide.txt`, `prompts/plan.txt`. These are the leverage points.
3. Run the agent against `dummy_spec.md` and watch the logs.
4. Read what the model actually says and does. Tune the prompts. Re-run.
5. Repeat until the agent behaves well on the dummy spec.

Plan for 2-3 hours on this phase, with at least one hour spent on tuning rather than coding.

---

## Codex CLI Brief — Build `context.py` scaffolding

### Rules for this session

1. The file you build is `context.py` in the current directory. There is already a stub `context.py` in place — replace it entirely.
2. Match the function signatures used by `agent.py`. Do not change `agent.py`.
3. No third-party dependencies. Standard library only.
4. Use the existing `logger.py` for any logging needed — import `get_logger` from it.
5. Create a `prompts/` subdirectory and load prompt templates from `.txt` files inside it. Do not embed long prompt strings as Python multiline strings — they belong in editable files.
6. Write a `test_context.py` that confirms the functions return sensibly-shaped output. Do not test prompt *quality* in unit tests — that is tuned by hand.
7. Ask clarifying questions before writing code if anything is ambiguous.

### Task

Build the context-building layer for an autonomous coding agent. These functions assemble the prompts the model sees. They do not call the model directly — they return `(system_prompt, user_prompt)` tuples that the orchestrator passes to `call_model`.

### Function signatures

```python
def build_planning_prompt(spec_text: str) -> tuple[str, str]:
    """Build the (system, user) prompts for the initial planning call. Returns prompts that ask the model to break the spec into 5-10 ordered steps. The model is expected to respond with JSON of shape {"steps": ["step 1", "step 2", ...]}."""

def build_context(state: dict) -> tuple[str, str]:
    """Build the (system, user) prompts for the per-iteration decide call. Returns prompts that contain the spec, the plan, the current files in workspace/, the last test result, and the recent action history. The model is expected to respond with a JSON decision of shape {"action": "...", "args": {...}, "reasoning": "..."}."""

def summarize_trajectory(recent_actions: list[dict]) -> str:
    """Take a list of action records (the structure used in state['recent_actions']) and return a short prose summary. Called when the recent_actions list grows past 8 entries; the oldest entries are summarized and prepended to state['older_trajectory_summary']."""
```

### Prompt template files

Create `prompts/` directory with three files:

- `prompts/system.txt` — the system prompt used for both planning and decide calls. Loaded once at module import. Around 400-600 words.
- `prompts/plan.txt` — the user-side template for the planning call. Contains a `{spec_text}` placeholder. Around 100-200 words.
- `prompts/decide.txt` — the user-side template for the decide call. Contains placeholders for `{spec_section}`, `{plan_section}`, `{workspace_section}`, `{last_test_section}`, `{trajectory_section}`. Around 200-400 words.

These files will be hand-edited by the human after Codex creates them. **Generate sensible starting content based on the guidance below, but assume the human will rewrite them.** Make them easy to find and edit.

### Content for `prompts/system.txt`

Write a system prompt that establishes the agent's role and behavior. Include all of these elements explicitly:

- **Role**: "You are an autonomous coding agent. You are working on the task described in the spec. You operate in a loop: each turn, you pick exactly one action, and the orchestrator executes it. After execution, you see the result and pick the next action."

- **Workflow rhythm**: Describe the gather-act-verify loop. State that the model should typically read or list before editing, edit incrementally, and run tests after each meaningful change. State that running tests is the primary feedback signal and that the model must not declare a task complete without test confirmation.

- **Available tools**: List the six actions (read_file, edit_file, list_dir, run_shell, run_tests, stop) with opinionated descriptions. For each, say *when to use it* and *when not to*. Example for `edit_file`: "Use to create or overwrite files in workspace/. The content argument replaces the entire file — there is no partial edit. Before editing an existing file, you MUST first call read_file on it; the orchestrator will reject edits to files you have not just read. Do not edit the spec file or test files — they are read-only."

- **Output format**: Specify the JSON decision schema. Be explicit: "You must respond with a single JSON object and nothing else. No prose before or after. No markdown code fences. The object must have keys `action`, `args`, `reasoning`. The action must be one of: read_file, edit_file, list_dir, run_shell, run_tests, stop. The reasoning field should be 1-3 sentences explaining why this action is the right next step."

- **Constraints**: State the source-of-truth rule. "The spec file is the source of truth. The public tests are the feedback signal. If you discover that the tests and the spec disagree, do not invent a third interpretation — flag it in your reasoning and stop. Do not add features the spec does not ask for. Do not edit tests."

- **Anti-patterns**: A short list of things not to do. "Do not edit a file you have not just read. Do not propose the same change twice when it failed the first time — diagnose the failure differently before retrying. Do not declare done until tests pass. Do not chain multiple actions in one response — pick one."

### Content for `prompts/plan.txt`

The planning prompt is simpler. It asks the model to read the spec and produce a list of concrete steps. Template content:

```
Read the following technical specification. Break it into 5 to 10 concrete, ordered implementation steps that an agent can execute one at a time.

Each step should be a single, actionable engineering task — for example, "create a CLI entry point in main.py that parses --input and --output flags," not "implement the program."

Order the steps so that earlier steps enable later ones. Put the minimal working version first; add edge cases and error handling later. Make running the public test suite one of the steps.

Respond with a JSON object of exactly this shape — no prose, no markdown fences, no extra keys:

{"steps": ["step 1", "step 2", "step 3", ...]}

The specification:

{spec_text}
```

### Content for `prompts/decide.txt`

The per-iteration decide prompt is the most carefully assembled. It contains five labeled sections so the model can find what it needs. Template:

```
You are continuing work on the task. Below is the current state.

=== SPEC (source of truth) ===
{spec_section}

=== PLAN ===
{plan_section}

=== WORKSPACE ===
{workspace_section}

=== LAST TEST RESULT ===
{last_test_section}

=== RECENT ACTIONS ===
{trajectory_section}

Pick the single best next action. Respond with a JSON object only:

{"action": "...", "args": {...}, "reasoning": "..."}
```

### Section builders

Implement helper functions to build each section. These determine *what* the model sees and are where most of the per-iteration intelligence lives.

**`_build_spec_section(state)`**: If the spec is under 1500 characters, include it in full. Otherwise, include only the first 500 chars and the last 300 chars, with a note in between: `[... spec truncated, full version at {spec_path} — call read_file if needed ...]`.

Wait — the spec is outside `workspace/` and `read_file` is sandboxed. Resolve this by always including the full spec if it fits in ~2000 tokens, and truncating only above that. For a hackathon task the spec will likely fit. Add a TODO comment if you implement truncation, noting that the human may want to adjust thresholds after seeing the actual spec size.

**`_build_plan_section(state)`**: List the plan with the current step marked. Format:

```
Step 1: <text>  [done]
Step 2: <text>  [done]
Step 3: <text>  [<-- current]
Step 4: <text>
Step 5: <text>
```

The orchestrator updates `state["current_step_index"]` — but in v1 it does not auto-advance. Marking steps as `[done]` is aspirational; for now mark the step at `current_step_index` as `[<-- current]` and leave others unmarked. Note this in a TODO so the human can decide whether to add auto-advancement.

**`_build_workspace_section(state)`**: List files in `workspace/` with their sizes. Format:

```
workspace/
├── main.py (412 bytes)
├── utils.py (1.2 KB)
└── tests/
    └── test_main.py (876 bytes)
```

If `workspace/` is empty, say `(empty — no files created yet)`. Cap the listing at 30 entries; if more, show first 30 and note `... and N more files`.

**`_build_last_test_section(state)`**: If no test has been run yet, say `(no test run yet — call run_tests to get feedback)`. Otherwise show:

```
Last test run: 7 passed, 3 failed, 0 errors

Failures (first 3):
<failure_summary content>
```

The failure_summary already comes pre-truncated from `tools.run_tests`.

**`_build_trajectory_section(state)`**: Combine `state["older_trajectory_summary"]` (if non-empty) with one-line summaries of `state["recent_actions"]`. Format each recent action as:

```
iter 5: edit_file workspace/main.py — wrote 412 bytes (success)
iter 6: run_tests — 5 passed, 2 failed
iter 7: read_file workspace/main.py — read 412 chars
```

If `older_trajectory_summary` is non-empty, prepend it as a block:

```
Earlier in this session:
<older_trajectory_summary>

Recent actions:
<formatted recent actions>
```

### `summarize_trajectory` implementation

When called by the orchestrator with a list of old action records, this function should produce a short prose summary (target ~200 chars, max ~500). Two implementation options — pick the simpler one:

**Option A (preferred): deterministic summary.** No model call. Walk the action list and produce a counting summary:

```
"Earlier: 8 actions. Edited 3 files (main.py, utils.py, cli.py). Ran tests 2 times, last result: 4 passed, 3 failed. Read 5 files. 1 guardrail rejection."
```

**Option B (only if A proves insufficient): call the model.** Pass the action list as JSON to `call_model` with a prompt asking for a one-paragraph summary. This costs an API call per compression event and adds latency, so prefer Option A.

Build Option A. Leave a comment in the code noting that Option B exists if the human wants to try it.

### Logging

Log each prompt build to `prompts.log`:

```
get_logger("prompts").info(f"built decide prompt: spec={len(spec_section)} plan={len(plan_section)} workspace={len(workspace_section)} test={len(last_test_section)} traj={len(trajectory_section)} total={len(user_prompt)} chars")
```

This lets the human see prompt size trends over iterations and spot when something is bloating.

### Test file: `test_context.py`

Use `unittest`. Tests should confirm:

1. `build_planning_prompt(spec)` returns a tuple of two non-empty strings, both contain the spec text.
2. `build_planning_prompt(spec)` user prompt contains the literal string `"steps"` (so the model knows the expected output key).
3. `build_context(state)` returns a tuple of two non-empty strings for a freshly initialized state.
4. `build_context(state)` user prompt contains all five section headers (`=== SPEC ===` etc.).
5. With a state containing 3 recent actions, the trajectory section includes all three.
6. With a state containing a `last_test_result`, the test section includes the pass/fail counts.
7. With an empty `last_test_result`, the test section contains the "no test run yet" message.
8. `summarize_trajectory([])` returns an empty string or a short "no actions" sentence (don't crash).
9. `summarize_trajectory(actions)` with 5 action records returns a non-empty string under 500 chars.
10. Prompt templates load correctly — confirm `prompts/system.txt`, `prompts/plan.txt`, `prompts/decide.txt` exist after module import.

Do not test prompt *quality* in unit tests. Quality is tuned by hand in the next step.

### What this file must NOT do

- Must not import any third-party packages.
- Must not call `call_model` directly (except possibly inside `summarize_trajectory` if Option B is chosen — but you are building Option A).
- Must not write outside `prompts/` and `agent_logs/`.
- Must not modify `agent.py` or any other module.
- Must not embed long prompts as Python string literals — they go in `prompts/*.txt`.
- Must not exceed 250 lines for `context.py` itself (prompts live in separate files).

### Definition of done

- `context.py` exists, three public functions implemented.
- `prompts/system.txt`, `prompts/plan.txt`, `prompts/decide.txt` exist with sensible starter content.
- `test_context.py` exists and passes.
- `python agent.py --spec dummy_spec.md` runs end-to-end and produces a coherent series of model decisions (not necessarily correct decisions — the dummy spec may not be solvable on the first try, and the prompts have not been tuned yet).
- File length: 150–250 lines for `context.py`. Prompt files total another 500-1000 words.

---

## After Codex finishes — the tuning phase

This is where the real work of Phase 5 happens. Codex produces the scaffolding; you produce the behavior.

### Step 1: Run the agent and read the logs

```bash
rm -rf agent_logs state.json workspace/*
python agent.py --spec dummy_spec.md
```

Then open each of these files and read them carefully:

- `agent_logs/decisions.log` — every action the model picked
- `agent_logs/prompts.log` — every prompt sent
- `agent_logs/calls/` — the per-call detail files with full prompts and responses
- `state.json` — final state including recent_actions and any failures

Do not skip this reading step. Watch what the model actually does, in its own words. This is what tuning is informed by.

### Step 2: Identify the patterns that need fixing

Common patterns you will probably see in the first run, and how to fix each:

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Model edits files without reading them first → guardrail rejections | `system.txt` doesn't emphasize read-before-edit strongly enough | Add an explicit warning in `system.txt` and a reminder in `decide.txt` |
| Model never calls `run_tests` | System prompt doesn't establish testing as the verification step | Strengthen the verification language in `system.txt`; add "after every meaningful edit, run tests" |
| Model declares `stop` before tests pass | `stop` action description is too permissive | Tighten `stop` description: "Only call after run_tests shows all tests passing" |
| Model returns JSON wrapped in markdown fences | Output format instruction is not emphatic enough | Add "no markdown code fences" to system prompt explicitly |
| Model writes unrelated code (extra features) | Spec adherence not stressed | Add "do not add features the spec does not request" to system prompt |
| Model loops on the same failure | Repeat detector triggers, but model doesn't change approach | Add to system prompt: "If your last action failed, diagnose why before retrying. Do not propose the same change twice." |
| Model edits the wrong file | Workspace section doesn't make existing file purposes clear | Improve `_build_workspace_section` to show file purposes if a comment header exists |
| Trajectory section is too verbose | One-line summaries too long | Tighten the format string in `_build_trajectory_section` |

### Step 3: Edit the prompt files directly

The prompt files are plain text. Edit them in your editor. Re-run the agent. Repeat.

Do not edit prompts inside `context.py` — that's why they were moved to text files. The whole point is that you can iterate on prompts without touching Python code.

### Step 4: Stop tuning when

You've hit the point of diminishing returns when:

- The model reads before editing on its own
- It runs tests after meaningful changes
- It stops when tests pass, not before
- Guardrail rejections are rare (under 1 per 10 iterations)
- The trajectory section in the prompt stays under ~800 chars across a 20-iteration run

If you hit those four, you're done with Phase 5. Save the final prompts and move on.

If you cannot get the agent to behave well on a simple dummy spec within ~2 hours of tuning, the issue is probably not the prompts. Reread the orchestrator logic, the tool implementations, and the model wrapper for bugs. Bad agent behavior is more often a code bug than a prompt bug.

## What can go wrong in this phase

- **Prompts work great on Gemini but fail on Groq (or vice versa).** Different models have different formatting tolerances. Test on both providers; keep the prompts compatible with both. Llama models often need stricter "respond only with JSON" instructions.

- **Prompt files grow to thousands of words.** This is a smell. Long prompts dilute attention. Keep the system prompt under ~600 words. If you need to add more, you probably need to remove something else.

- **The model gets confused by the trajectory section.** Trajectory should be brief and chronological. If your formatting is dense or out-of-order, simplify it. Sometimes a numbered list reads better than an indented tree.

- **You tune prompts to dummy spec quirks.** If the dummy spec is simple, you might be fitting the prompts to it. Test on a different dummy spec before declaring done.

- **Lost track of which prompt version produced which behavior.** Commit your prompt files to git after each tuning session. `git log prompts/` becomes your tuning history.

## After Phase 5

You now have all real modules in place. Phase 6 is the end-to-end dry run and prep for the 19:45 checkpoint:

- Write a more realistic dummy spec than the smoke-test one
- Run the agent against it
- Watch the agent solve (or fail to solve) a real-feeling problem
- Fix any remaining issues
- Write `agent_manifest.json` and `README.md`
- Practice the 19:45 checkpoint commit flow
- Practice the 20:00 reveal flow

Phase 5 is the leverage point. Phase 6 is the dress rehearsal.
