import json


def call_model(system, user, expect_json=False):
    """Stub: returns a canned 'stop' decision so the loop exits after 1 iteration."""
    if "planning" in system.lower() or "plan" in user.lower()[:200]:
        return json.dumps({"steps": ["step 1: stub", "step 2: stub"]})
    return json.dumps({
        "action": "stop",
        "args": {"reason": "stub model - exiting immediately"},
        "reasoning": "stub call_model always stops"
    })
