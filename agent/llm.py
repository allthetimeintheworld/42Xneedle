import os
import json
import time
from openai import OpenAI, RateLimitError
from .config import GROQ_API_KEY, MISTRAL_API_KEY, DEEPSEEK_API_KEY, PLANNER_MODEL, LOG_DIR
from datetime import datetime

def log_event(filename, message):
    os.makedirs(LOG_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(os.path.join(LOG_DIR, filename), "a") as f:
        f.write(f"[{timestamp}] {message}\n")

# Initialize clients
groq_client = None
if GROQ_API_KEY:
    groq_client = OpenAI(
        api_key=GROQ_API_KEY,
        base_url="https://api.groq.com/openai/v1",
        max_retries=3,
        timeout=30.0
    )

mistral_client = None
if MISTRAL_API_KEY:
    mistral_client = OpenAI(
        api_key=MISTRAL_API_KEY,
        base_url="https://api.mistral.ai/v1",
        max_retries=3,
        timeout=30.0
    )

deepseek_client = None
if DEEPSEEK_API_KEY:
    deepseek_client = OpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url="https://api.deepseek.com",
        max_retries=3,
        timeout=30.0
    )

def _call_client(client, model, messages, json_mode=True):
    try:
        kwargs = {
            "model": model,
            "messages": messages,
            "temperature": 0.2
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        
        response = client.chat.completions.create(**kwargs)
        return response.choices[0].message.content
    except RateLimitError as e:
        log_event("errors.log", f"Rate limit reached for model {model}: {str(e)}")
        return None
    except Exception as e:
        log_event("errors.log", f"API Call failed for model {model}: {str(e)}")
        return None

def ask_model(prompt, system_instruction, model=PLANNER_MODEL):
    log_event("prompts.log", f"System: {system_instruction}\nUser: {prompt}")
    
    # Ensure "json" is in the prompt for JSON mode
    if "json" not in prompt.lower() and "json" not in system_instruction.lower():
        prompt += "\n\nIMPORTANT: Response must be a valid JSON object."

    messages = [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": prompt}
    ]

    # 1. Try DeepSeek (High Priority for reliability if Groq is limited)
    if deepseek_client:
        content = _call_client(deepseek_client, "deepseek-chat", messages)
        if content: return content

    # 2. Try Groq
    if groq_client:
        content = _call_client(groq_client, model, messages)
        if content: return content

    # 3. Try Mistral Fallback
    if mistral_client:
        log_event("decisions.log", "DeepSeek/Groq failed. Falling back to Mistral.")
        # Use mistral-large-latest as it's their strong model
        content = _call_client(mistral_client, "mistral-large-latest", messages)
        if content: return content

    # 4. Manual Fallback
    print("\n--- ALL API PROVIDERS FAILED OR RATE-LIMITED ---")
    print(f"System: {system_instruction}")
    print(f"User: {prompt}")
    print("--- END PROMPT ---\n")
    return input("Agent Decision (JSON): ")
