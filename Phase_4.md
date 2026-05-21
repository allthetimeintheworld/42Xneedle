# Phase 4 — Build `model.py`

## Status check before starting

Before opening Codex, confirm:

- [ ] `agent.py` exists and the orchestrator smoke test passes
- [ ] `logger.py` is the real implementation, `test_logger.py` passes
- [ ] `tools.py` is the real implementation, `test_tools.py` passes
- [ ] `python agent.py --spec dummy_spec.md` still exits 0 with the real logger and tools in place
- [ ] `model.py` is still the temporary stub from the setup phase

If any of those are not true, fix them before starting Phase 4.

## Prerequisites — API keys and dependencies

This phase requires real API access. Set this up **before** opening Codex.

### Get a Gemini API key (primary provider)

1. Go to https://aistudio.google.com/apikey
2. Sign in with a Google account
3. Click "Create API key", optionally pick a project, copy the key
4. The key looks like `AIzaSy...` (39 characters)

### Get a Groq API key (fallback provider)

1. Go to https://console.groq.com/keys
2. Sign up (no credit card required)
3. Create a new API key, copy it
4. The key looks like `gsk_...`

### Add the keys to `.env`

Create a `.env` file in your project root:

```
GEMINI_API_KEY=AIzaSy...your_actual_key...
GROQ_API_KEY=gsk_...your_actual_key...
```

Add `.env` to `.gitignore` if it isn't already:

```bash
echo ".env" >> .gitignore
```

**Do not commit the .env file.** Confirm with `git status` that it does not appear in tracked changes.

### Install `python-dotenv`

```bash
pip install python-dotenv
```

Add it to `requirements.txt`:

```
python-dotenv
requests
```

`requests` is also needed; add it now even if it's already installed.

### Test that keys work

Before Codex starts, run a one-liner to confirm each key is valid. This isolates "the key is broken" from "the code is broken" — much easier to debug.

**Gemini:**

```bash
curl -X POST "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=$GEMINI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"contents":[{"parts":[{"text":"Say hi"}]}]}'
```

You should see a JSON response with the model's reply. If you get a 401, 403, or `API_KEY_INVALID`, the key is wrong — fix it now.

**Groq:**

```bash
curl https://api.groq.com/openai/v1/chat/completions \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"llama-3.3-70b-versatile","messages":[{"role":"user","content":"Say hi"}]}'
```

Same expectation — JSON response with a reply. If it fails, fix before continuing.

If you're on Windows or the `$VAR` syntax doesn't work in your shell, paste the actual key in place of the variable.

Only proceed to Codex once both curl calls succeed.

## What you're building in this phase

The model layer — a single function `call_model(system, user, expect_json=False) -> str` that the orchestrator and other modules call to talk to a language model.

Internally it tries Gemini first, retries on rate limits, falls back to Groq if Gemini is broken, parses and validates JSON when asked, and logs everything to `prompts.log`. From the orchestrator's perspective, it's just a function that takes two strings and returns one.

The hard parts are not the API calls. The hard parts are:

- Rate-limit handling without hanging the agent
- JSON extraction from responses wrapped in markdown code fences
- Graceful fallback when one provider goes down
- Not leaking API keys into logs

## Files this phase produces

- `model.py` — replaces the existing stub
- `test_model.py` — verification suite, runnable as `python test_model.py`

No other files modified. `agent.py`, `logger.py`, `tools.py`, `context.py` stay untouched.

## How to run this phase

1. Confirm all prerequisites above are done (API keys work via curl, `.env` exists, dotenv installed).
2. Open a terminal in your project root.
3. Run `codex` to start a CLI session.
4. Paste the brief below as your first message.
5. Codex will ask clarifying questions — answer them.
6. Approve file writes and command executions one at a time for the first session.
7. After Codex declares done, run the verification checks (see "Verification" below).

---

## Codex CLI Brief — Build `model.py`

### Rules for this session

1. The file you build is `model.py` in the current directory. There is already a stub `model.py` in place — replace it entirely.
2. Match the function signature used by `agent.py`. Do not change `agent.py`.
3. Use only `requests` and `python-dotenv` as third-party packages. Both are already installed.
4. Use the existing `logger.py` for logging — import `get_logger` from it.
5. Before declaring done, write a `test_model.py` and run it. The test must include at least one real API call to confirm end-to-end function.
6. After tests pass, re-run `python agent.py --spec dummy_spec.md` to confirm the orchestrator still works.
7. Ask clarifying questions before writing code if anything is ambiguous.

### Task

Build the model layer for an autonomous coding agent. This is the wrapper that lets the rest of the agent talk to a language model without caring which provider is serving the request. It handles provider selection, retries, rate limits, JSON parsing, and logging.

The agent will run for many iterations during a hackathon. Free-tier APIs will rate-limit. The wrapper must absorb that without bringing down the loop.

### Function signature

```python
def call_model(system: str, user: str, expect_json: bool = False) -> str:
    """Call a language model with a system prompt and user prompt. Returns the model's response as a string. If expect_json=True, the response is validated as JSON (with markdown fences stripped) before returning."""
```

Internally also expose (for testing only):

```python
def _call_gemini(system: str, user: str) -> str:
    """Single attempt against Gemini. Raises on any failure."""

def _call_groq(system: str, user: str) -> str:
    """Single attempt against Groq. Raises on any failure."""

def _extract_json(text: str) -> str:
    """Strip markdown code fences and return parseable JSON text. Raises ValueError if no valid JSON is found."""
```

### Provider details

**Primary: Gemini 2.5 Flash**

- Endpoint: `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent`
- Auth: `?key=<GEMINI_API_KEY>` as query parameter
- Request body:
  ```json
  {
    "contents": [{"parts": [{"text": "<user prompt>"}]}],
    "systemInstruction": {"parts": [{"text": "<system prompt>"}]},
    "generationConfig": {"temperature": 0.2, "maxOutputTokens": 4096}
  }
  ```
- Response: `response.json()["candidates"][0]["content"]["parts"][0]["text"]`
- Rate-limit status: 429
- Timeout: 60 seconds per request

**Fallback: Groq with Llama 3.3 70B**

- Endpoint: `https://api.groq.com/openai/v1/chat/completions`
- Auth: `Authorization: Bearer <GROQ_API_KEY>` header
- Request body (OpenAI-compatible):
  ```json
  {
    "model": "llama-3.3-70b-versatile",
    "messages": [
      {"role": "system", "content": "<system prompt>"},
      {"role": "user", "content": "<user prompt>"}
    ],
    "temperature": 0.2,
    "max_tokens": 4096
  }
  ```
- Response: `response.json()["choices"][0]["message"]["content"]`
- Rate-limit status: 429
- Timeout: 60 seconds per request

If `groq` model name `llama-3.3-70b-versatile` returns an error, try `llama-3.1-70b-versatile` as a secondary fallback model. Log the substitution.

### Retry and fallback logic

The control flow inside `call_model`:

```
1. Try Gemini (up to 3 attempts).
   - On 429: sleep with exponential backoff (2s, 4s, 8s), then retry.
   - On other 4xx (auth errors, bad request): log and break to step 2 immediately.
   - On 5xx or network error: sleep 2s, retry. After 3 attempts, break to step 2.
   - On success: go to step 3.
2. Try Groq (up to 3 attempts) with the same retry pattern.
   - If Groq also fails after retries: raise RuntimeError("all providers failed").
3. If expect_json=True: pass response through _extract_json. If parsing fails, retry the entire call_model call once (up to 1 retry). After that, raise ValueError.
4. Return the response text.
```

Total maximum wall time per `call_model` call: roughly 3 minutes (6 attempts × 60s + backoffs). This is fine — the orchestrator has its own per-iteration soft timeout.

### JSON extraction

Language models love to wrap JSON in markdown code fences. `_extract_json` must handle:

- Plain JSON: `{"foo": 1}` → return as-is
- Fenced JSON: ` ```json\n{"foo": 1}\n``` ` → strip fences, return inner
- Fenced without language tag: ` ```\n{"foo": 1}\n``` ` → strip fences
- JSON with leading/trailing whitespace or prose: `Sure, here you go:\n{"foo": 1}\nLet me know if...` → find the first `{` or `[`, find the matching closing `}` or `]`, return that substring

Implementation suggestion:

```python
def _extract_json(text: str) -> str:
    # Strip markdown fences
    text = text.strip()
    if text.startswith("```"):
        # Remove first line (```json or ```)
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        # Remove trailing fence
        if text.rstrip().endswith("```"):
            text = text.rstrip()[:-3]
    text = text.strip()
    
    # Validate it parses
    try:
        json.loads(text)
        return text
    except json.JSONDecodeError:
        # Try finding the first {...} or [...] block
        for start_char, end_char in [("{", "}"), ("[", "]")]:
            start = text.find(start_char)
            if start == -1:
                continue
            # Walk forward to find matching close
            depth = 0
            for i in range(start, len(text)):
                if text[i] == start_char:
                    depth += 1
                elif text[i] == end_char:
                    depth -= 1
                    if depth == 0:
                        candidate = text[start:i+1]
                        try:
                            json.loads(candidate)
                            return candidate
                        except json.JSONDecodeError:
                            break
        raise ValueError(f"could not extract JSON from response: {text[:200]}")
```

### Logging

Use `prompts.log` (and `errors.log` for failures):

```python
from logger import get_logger
prompts_log = get_logger("prompts")
errors_log = get_logger("errors")
```

For each call, log:

- Provider attempted (`gemini` or `groq`) and model name
- System prompt length (chars)
- User prompt length (chars)
- Response length (chars) on success
- A 200-char preview of system prompt, user prompt, and response (truncated cleanly, not mid-word if avoidable)
- Total duration in seconds
- Whether `expect_json` was true and whether JSON parsing succeeded

**Do not log API keys.** Confirm by reading back the log file in your test: no string starting with `AIzaSy` or `gsk_` should appear anywhere.

For full prompts and responses (which are long), write them to per-call files in `agent_logs/calls/`:

```
agent_logs/calls/2026-05-22T20-05-14_gemini_001.txt
```

Format:

```
=== SYSTEM ===
<full system prompt>

=== USER ===
<full user prompt>

=== RESPONSE ===
<full response>

=== META ===
provider: gemini
model: gemini-2.5-flash
duration_s: 1.84
status: success
```

Number the files sequentially within a session (use a module-level counter starting at 1). This gives judges full evidence of what the model saw and said without bloating the main log.

### Configuration loading

At module import time:

```python
from dotenv import load_dotenv
load_dotenv()

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

if not GEMINI_API_KEY and not GROQ_API_KEY:
    raise RuntimeError("no API keys found — set GEMINI_API_KEY and/or GROQ_API_KEY in .env")
```

If only one key is set, the other provider is simply unavailable — log a warning at import time and skip that provider in `call_model`. Don't crash.

### Test file: `test_model.py`

Write tests using `unittest`. Two categories:

**Unit tests (no network)** — must always run:

1. `_extract_json` with plain JSON
2. `_extract_json` with markdown-fenced JSON
3. `_extract_json` with fenced JSON without language tag
4. `_extract_json` with prose-wrapped JSON
5. `_extract_json` with no JSON at all (raises ValueError)
6. `_extract_json` with nested objects/arrays
7. Confirm no API key strings appear in any log file after the unit tests run

**Integration tests (require network and valid keys)**:

8. `call_model("You are helpful", "Say hello in one word", expect_json=False)` returns a non-empty string.
9. `call_model("Respond only with JSON", 'Return {"ok": true}', expect_json=True)` returns valid JSON.
10. Confirm a file was created in `agent_logs/calls/` for each call.

If `GEMINI_API_KEY` and `GROQ_API_KEY` are both missing in the environment, skip the integration tests with `unittest.skip` rather than failing them — this lets the unit tests still serve as a smoke check.

The test file should be runnable as `python test_model.py` and exit 0 on success.

### What this file must NOT do

- Must not import any third-party packages other than `requests` and `python-dotenv`.
- Must not write outside `agent_logs/`.
- Must not modify `agent.py` or any other module.
- Must not log API keys, ever, anywhere.
- Must not hardcode API keys — always read from environment.
- Must not retry forever on rate limits — cap at 3 attempts per provider.
- Must not use threading or async.
- Must not catch and ignore exceptions silently — log to `errors.log` before re-raising or falling back.

### Definition of done

- `model.py` exists, `call_model` signature matches.
- `test_model.py` exists. Unit tests pass. Integration tests pass when keys are present.
- One real call to Gemini succeeds end-to-end.
- One real call to Groq succeeds end-to-end (test by temporarily setting `GEMINI_API_KEY=""` in the environment for one test run).
- `agent_logs/prompts.log` contains structured entries.
- `agent_logs/calls/` contains per-call detail files.
- No API key strings appear anywhere in `agent_logs/`.
- `python agent.py --spec dummy_spec.md` still exits 0 with the real `model.py` in place.
- File length: 200–350 lines.

---

## Verification (you, after Codex finishes)

Do not skip these.

1. **Run the unit tests**:
   ```bash
   python test_model.py
   ```
   All tests pass, including integration tests.

2. **Manual call from a Python REPL**:
   ```bash
   python -c "from model import call_model; print(call_model('Be concise.', 'What is 2+2?'))"
   ```
   You should see a brief response like "4" or "2+2 equals 4".

3. **Test JSON mode**:
   ```bash
   python -c "from model import call_model; print(call_model('Respond only in JSON.', 'Return a JSON object with key answer set to 4.', expect_json=True))"
   ```
   You should see something parseable as JSON: `{"answer": 4}` or similar.

4. **Test fallback** — temporarily break Gemini and confirm Groq kicks in:
   ```bash
   GEMINI_API_KEY="invalid" python -c "from model import call_model; print(call_model('Be concise.', 'Say hi'))"
   ```
   Should still work via Groq. Check `agent_logs/errors.log` for the Gemini failure and `agent_logs/prompts.log` for the Groq success.

5. **Confirm no key leakage**:
   ```bash
   grep -r "AIzaSy\|gsk_" agent_logs/
   ```
   Should return nothing. If it returns anything, fix `model.py` before continuing — this is a security bug.

6. **Run the orchestrator smoke test**:
   ```bash
   rm -rf agent_logs state.json
   python agent.py --spec dummy_spec.md
   ```
   The agent now uses the real model. The stub model always returned `"stop"` immediately — the real model might actually try to do work. The smoke test may now make more iterations, or fail in interesting new ways (the model might try to call tools that aren't yet primed by the still-stubbed `context.py`). That's expected. As long as it exits without crashing, you're good.

7. **Inspect a real prompts.log entry**:
   ```bash
   cat agent_logs/prompts.log
   ls agent_logs/calls/
   cat agent_logs/calls/$(ls agent_logs/calls/ | head -1)
   ```
   You should see real prompts and responses. Sanity-check that the model is being asked sensible questions (this also tells you whether your stub `context.py` is producing reasonable prompts — Phase 5 will improve them).

## What can go wrong in this phase

- **"API_KEY_INVALID"**: your `.env` is wrong, or `load_dotenv()` isn't being called, or you have an extra space in the key. Re-run the curl test from the prerequisites section to isolate.

- **"all providers failed" on the first call**: usually a network issue or both keys are wrong. Check `agent_logs/errors.log` for the underlying HTTP error.

- **JSON extraction fails on responses that look fine**: the model returned something like `Here's your answer:\n\n{"foo": 1}\n\nLet me know if you need more.` The extractor should handle this — if it doesn't, paste the actual response into Codex and ask for a fix.

- **Rate limits hit during testing**: free tiers usually allow 10–15 requests per minute. If you're hammering the API in tests, slow down or insert `time.sleep(1)` between integration tests.

- **`agent.py` smoke test now does weird things**: expected. The real model isn't bound to the same canned `"stop"` response the stub returned. It may try to read files, list directories, or run tests. With a stubbed `context.py`, the prompts are weak — so its decisions may be erratic. This is normal and will improve once Phase 5 lands.

- **API key in a log file**: stop immediately, fix `model.py`, delete the log file, regenerate keys (the leaked ones are now compromised). Check that no log statement uses `f"... {GEMINI_API_KEY} ..."` directly.

## After Phase 4

Once `model.py` is solid and the orchestrator smoke test still passes:

- **Phase 5** is `context.py` — the prompt builder. This is the module that determines whether the agent makes good decisions or thrashes. Save the hardest one for when everything else is reliable.
- **Phase 6** is the end-to-end dry run on a real dummy spec, with all real modules in place. This is where you discover the actual quality of your agent and have time to tune prompts before the 19:45 checkpoint.

You're more than halfway through the build. Keep going.
