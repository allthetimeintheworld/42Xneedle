# Agent Setup Architectural Overview

This document outlines the architecture and workflow for the autonomous agent setup designed for the hackathon.

## Core Objective
To create a reliable, iterative loop that can transform a technical specification into a verified implementation through continuous feedback from test results and error logs.

## Components

### 1. Specification Parser
- **Input:** Markdown files from `secret_spec/`.
- **Function:** Extracts key requirements, CLI behavior, formats, and constraints.

### 2. Planner
- **Function:** Breaks down the high-level task into incremental, testable milestones.
- **Output:** A sequence of sub-tasks for implementation.

### 3. Implementation Engine
- **Tools:** `write_file`, `replace`, `run_shell_command`.
- **Strategy:** Surgical edits to existing files and creation of new modules following identified patterns.

### 4. Verification Loop (Test Runner)
- **Execution:** Runs project-specific test suites (e.g., `pytest`, `npm test`, custom shell scripts).
- **Feedback:** Captures `stdout`, `stderr`, and exit codes for analysis.

### 5. Failure Analyzer & Repair Agent
- **Function:** Parses test failures to categorize errors (e.g., logic, formatting, environment).
- **Strategy:** Proposes and applies targeted fixes based on failure context.

### 6. Logging & Audit System
- **Directory:** `agent_logs/`
- **Files:**
    - `prompts.log`: Full history of model interactions.
    - `decisions.log`: High-level strategic choices and reasoning.
    - `commands.log`: Record of all shell commands executed.
    - `test_runs.log`: Detailed output from test executions.
    - `errors.log`: Tracebacks and systemic failures.
    - `human_interventions.log`: Manual corrections or restarts.
    - `final_report.md`: Summary of the agent's performance and final state.

## Operational Workflow
1. **Bootstrap:** Agent reads `secret_spec/SECRET_SPEC.md`.
2. **Strategy:** Agent generates an initial implementation plan.
3. **Execution:**
    - Perform atomic code change.
    - Run validation tests.
    - If failed: Analyze -> Repair -> Re-test.
    - If passed: Advance to next milestone.
4. **Finalization:** Generate `final_report.md` and ensure all logs are flushed.

## Model Usage
- Adheres strictly to the "Free/Local/Open" model constraints after the hidden task release.
- Orchestration logic is designed to be model-agnostic.
