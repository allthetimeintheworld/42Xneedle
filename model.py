import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

from logger import get_logger


load_dotenv()

GEMINI_MODEL = "gemini-2.5-flash"
GROQ_MODELS = ("llama-3.3-70b-versatile", "llama-3.1-70b-versatile")
GEMINI_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent"
)
GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"
TIMEOUT_S = 60
MAX_ATTEMPTS = 3

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

_call_counter = 0


def _preview(text: str, limit: int = 200) -> str:
    compact = str(text).replace("\n", "\\n")
    if len(compact) <= limit:
        return compact
    cut = compact[:limit]
    if " " in cut:
        cut = cut.rsplit(" ", 1)[0]
    return cut + "..."


def _sanitize_error(message: object) -> str:
    text = str(message)
    if GEMINI_API_KEY:
        text = text.replace(GEMINI_API_KEY, "[REDACTED_GEMINI_API_KEY]")
    if GROQ_API_KEY:
        text = text.replace(GROQ_API_KEY, "[REDACTED_GROQ_API_KEY]")
    text = re.sub(r"key=AIza[^\s)'\">]+", "key=[REDACTED_GEMINI_API_KEY]", text)
    text = re.sub(r"gsk_[A-Za-z0-9_-]+", "[REDACTED_GROQ_API_KEY]", text)
    return text


def _timestamp_for_file() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S")


def _write_call_file(
    provider: str,
    model: str,
    system: str,
    user: str,
    response: str,
    duration_s: float,
    status: str,
) -> None:
    global _call_counter
    _call_counter += 1
    calls_dir = Path("agent_logs/calls")
    calls_dir.mkdir(parents=True, exist_ok=True)
    path = calls_dir / f"{_timestamp_for_file()}_{provider}_{_call_counter:03d}.txt"
    path.write_text(
        "\n".join(
            [
                "=== SYSTEM ===",
                system,
                "",
                "=== USER ===",
                user,
                "",
                "=== RESPONSE ===",
                response,
                "",
                "=== META ===",
                f"provider: {provider}",
                f"model: {model}",
                f"duration_s: {duration_s:.3f}",
                f"status: {status}",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _log_success(
    provider: str,
    model: str,
    system: str,
    user: str,
    response: str,
    duration_s: float,
    expect_json: bool,
    json_ok: bool,
) -> None:
    get_logger("prompts").info(
        "provider=%s model=%s system_len=%s user_len=%s response_len=%s "
        "duration_s=%.3f expect_json=%s json_ok=%s system_preview=%s "
        "user_preview=%s response_preview=%s",
        provider,
        model,
        len(system),
        len(user),
        len(response),
        duration_s,
        expect_json,
        json_ok,
        _preview(system),
        _preview(user),
        _preview(response),
    )


def _response_error(response: requests.Response) -> RuntimeError:
    try:
        detail = response.json()
    except ValueError:
        detail = response.text[:500]
    return RuntimeError(f"HTTP {response.status_code}: {detail}")


def _call_gemini(system: str, user: str) -> str:
    """Single attempt against Gemini. Raises on any failure."""
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not set")

    body = {
        "contents": [{"parts": [{"text": user}]}],
        "systemInstruction": {"parts": [{"text": system}]},
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 4096},
    }
    try:
        response = requests.post(
            GEMINI_ENDPOINT,
            params={"key": GEMINI_API_KEY},
            json=body,
            timeout=TIMEOUT_S,
        )
    except requests.RequestException as exc:
        raise RuntimeError(_sanitize_error(exc)) from exc
    if response.status_code >= 400:
        raise _response_error(response)
    data = response.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]


def _call_groq_model(system: str, user: str, model: str) -> str:
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is not set")

    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.2,
        "max_tokens": 4096,
    }
    try:
        response = requests.post(
            GROQ_ENDPOINT,
            headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
            json=body,
            timeout=TIMEOUT_S,
        )
    except requests.RequestException as exc:
        raise RuntimeError(_sanitize_error(exc)) from exc
    if response.status_code >= 400:
        raise _response_error(response)
    data = response.json()
    return data["choices"][0]["message"]["content"]


def _call_groq(system: str, user: str) -> str:
    """Single attempt against Groq. Raises on any failure."""
    last_error = None
    for model in GROQ_MODELS:
        try:
            return _call_groq_model(system, user, model)
        except Exception as exc:
            last_error = exc
            if model != GROQ_MODELS[-1]:
                get_logger("errors").error(
                    "groq model failed model=%s; trying model=%s error=%s",
                    model,
                    GROQ_MODELS[-1],
                    _sanitize_error(exc),
                )
    raise RuntimeError(f"Groq failed: {_sanitize_error(last_error)}")


def _extract_json(text: str) -> str:
    """Strip markdown fences and return parseable JSON text."""
    value = text.strip()
    if value.startswith("```"):
        value = value.split("\n", 1)[1] if "\n" in value else value[3:]
        if value.rstrip().endswith("```"):
            value = value.rstrip()[:-3]
    value = value.strip()

    try:
        json.loads(value)
        return value
    except json.JSONDecodeError:
        pass

    for start_char, end_char in [("{", "}"), ("[", "]")]:
        start = value.find(start_char)
        if start == -1:
            continue
        depth = 0
        in_string = False
        escaped = False
        for i in range(start, len(value)):
            char = value[i]
            if escaped:
                escaped = False
                continue
            if char == "\\":
                escaped = True
                continue
            if char == '"':
                in_string = not in_string
                continue
            if in_string:
                continue
            if char == start_char:
                depth += 1
            elif char == end_char:
                depth -= 1
                if depth == 0:
                    candidate = value[start:i + 1]
                    try:
                        json.loads(candidate)
                        return candidate
                    except json.JSONDecodeError:
                        break
    raise ValueError(f"could not extract JSON from response: {value[:200]}")


def _offline_response(system: str, user: str, expect_json: bool) -> str:
    get_logger("errors").error("no API keys found; using offline smoke-test fallback")
    lowered = f"{system}\n{user}".lower()
    is_planning_prompt = (
        "break it into 5 to 10 concrete" in lowered
        or "respond with a json object of exactly this shape" in lowered
        and '"steps"' in lowered
    )
    if expect_json and is_planning_prompt:
        return json.dumps({"steps": ["offline planning fallback"]})
    if expect_json:
        return json.dumps(
            {
                "action": "stop",
                "args": {"reason": "offline model fallback - no API keys configured"},
                "reasoning": "No provider API keys were available in the environment.",
            }
        )
    return "offline model fallback - no API keys configured"


def _provider_attempts(system: str, user: str):
    if GEMINI_API_KEY:
        yield "gemini", GEMINI_MODEL, _call_gemini
    else:
        get_logger("errors").error("Gemini unavailable: GEMINI_API_KEY is not set")

    if GROQ_API_KEY:
        yield "groq", GROQ_MODELS[0], _call_groq
    else:
        get_logger("errors").error("Groq unavailable: GROQ_API_KEY is not set")


def _call_provider(provider: str, model: str, fn, system: str, user: str) -> str:
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            return fn(system, user)
        except Exception as exc:
            message = _sanitize_error(exc)
            get_logger("errors").error(
                "provider=%s model=%s attempt=%s failed error=%s",
                provider,
                model,
                attempt,
                message,
            )
            is_rate_limit = "HTTP 429" in message or "rate" in message.lower()
            is_client_error = bool(re.search(r"HTTP 4\d\d", message)) and not is_rate_limit
            if is_client_error:
                break
            if attempt < MAX_ATTEMPTS:
                time.sleep((2 ** attempt) if is_rate_limit else 2)
    raise RuntimeError(f"{provider} failed after retries")


def _call_model_once(system: str, user: str, expect_json: bool) -> str:
    if not GEMINI_API_KEY and not GROQ_API_KEY:
        start = time.monotonic()
        response = _offline_response(system, user, expect_json)
        duration = time.monotonic() - start
        _log_success("offline", "none", system, user, response, duration, expect_json, expect_json)
        _write_call_file("offline", "none", system, user, response, duration, "success")
        return response

    last_error = None
    for provider, model, fn in _provider_attempts(system, user):
        start = time.monotonic()
        try:
            response = _call_provider(provider, model, fn, system, user)
            duration = time.monotonic() - start
            json_ok = False
            if expect_json:
                response = _extract_json(response)
                json_ok = True
            _log_success(provider, model, system, user, response, duration, expect_json, json_ok)
            _write_call_file(provider, model, system, user, response, duration, "success")
            return response
        except Exception as exc:
            last_error = exc
            get_logger("errors").error("provider=%s exhausted error=%s", provider, _sanitize_error(exc))
    raise RuntimeError(f"all providers failed: {_sanitize_error(last_error)}")


def call_model(system: str, user: str, expect_json: bool = False) -> str:
    """Call a language model and return the response string."""
    json_error = None
    for attempt in range(2 if expect_json else 1):
        try:
            response = _call_model_once(system, user, expect_json)
            if expect_json:
                return _extract_json(response)
            return response
        except ValueError as exc:
            json_error = exc
            get_logger("errors").error("JSON extraction failed attempt=%s error=%s", attempt + 1, exc)
    if json_error:
        raise json_error
    raise RuntimeError("all providers failed")
