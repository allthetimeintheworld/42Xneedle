def build_context(state):
    return ("You are a stub.", f"Iteration {state['iteration']}")


def build_planning_prompt(spec_text):
    return ("You are a planner stub.", f"Plan for: {spec_text[:100]}")


def summarize_trajectory(recent_actions):
    return f"summary of {len(recent_actions)} actions"
