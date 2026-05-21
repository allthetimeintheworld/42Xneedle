import json
import re

def parse_action(response_str):
    """
    Cleans and parses a JSON response from the LLM.
    Handles markdown blocks and ensures the result is a dictionary with an 'action' key.
    """
    clean_response = response_str.strip()
    
    # 1. Extract JSON from potential markdown blocks
    if "```" in clean_response:
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", clean_response, re.DOTALL)
        if match:
            clean_response = match.group(1)
        else:
            # Fallback: strip lines that look like markdown delimiters
            lines = [l for l in clean_response.split("\n") if not l.strip().startswith("```")]
            clean_response = "\n".join(lines).strip()

    # 2. Attempt JSON parse
    try:
        decision = json.loads(clean_response)
        if not isinstance(decision, dict):
            return None, "Response was not a JSON object (must be a dictionary)."
        
        # 3. Structural Validation (Goal-Stable Requirement)
        if "action" not in decision:
            return None, "Missing 'action' key in JSON object."
        
        return decision, None
        
    except json.JSONDecodeError as e:
        return None, f"JSON Decode Error: {str(e)} at line {e.lineno}, col {e.colno}"
    except Exception as e:
        return None, f"Unexpected Parsing Error: {str(e)}"
