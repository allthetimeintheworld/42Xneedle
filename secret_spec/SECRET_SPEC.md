# Task: Robust Factorial Utility

## Goal
Implement a factorial function in `src/math_utils.py`.

## Requirements
- The function must be named `factorial`.
- It must take a single integer `n`.
- For `n >= 0`, return the factorial.
- For `n < 0`, it MUST raise a `ValueError` with the message "Factorial not defined for negative numbers".
- Create a test file `tests/test_math_utils.py` that uses `pytest`.
- The tests should cover:
  - Base case: `factorial(0) == 1`
  - Normal case: `factorial(5) == 120`
  - Error case: `factorial(-1)` raises `ValueError`.

## Final Action
Run the tests. If they pass, commit the code with the message "feat: add factorial utility" and stop.
