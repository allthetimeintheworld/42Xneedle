import json
from ..llm import log_event

def parse_action(response_str):
    # Clean response string if model uses markdown blocks
    clean_response = response_str.strip()
    if "```" in clean_response:
        # Extract content between ```json and ``` or just ``` and ```
        import re
        match = re.search(r"```(?:json)?\s*(.*?)\s*```", clean_response, re.DOTALL)
        if match:
            clean_response = match.group(1)
        else:
            # Fallback: remove lines starting with ```
            lines = clean_response.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            clean_response = "\n".join(lines).strip()
    
    try:
        decision = json.loads(clean_response)
        if not isinstance(decision, dict):
            return None, "Response was not a JSON object (a dictionary)."
        if "action" not in decision:
            return None, "Missing 'action' key in JSON."
        return decision, None
    except Exception as e:
        return None, str(e)
