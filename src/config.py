"""
Configuration for terminal agent failure analysis.
"""

# Error category list (high-level categories for failure analysis)
ERROR_CATEGORIES = [
    "task_understanding",  # Misunderstanding the task requirements or goal
    "solution_design",     # Wrong algorithm, tool, or method selection
    "execution_error",     # Path/format errors, incomplete steps, or lost context
    "agent_framework"      # Agent framework issues (parsing errors, stuck on commands, or prompt violations)
]

# Analysis prompt template
ANALYSIS_PROMPT_TEMPLATE = """You are analyzing why a terminal agent failed to complete a task in Terminal Bench, a collection of tasks and an evaluation harness to help agent makers quantify their agents' terminal mastery. Agents can only act by issuing terminal commands; they cannot see test results during execution and cannot perform validation checks while generating actions. You are provided with the following information:

## Task Information
**Task ID:** {task_id}
**Task Instruction:**
{instruction}

## Test Results
{test_results}

## Test Files
{test_files}

## Official Solution (Reference)
{official_solution}

## Initial Prompt
{initial_prompt}

## Agent's Complete Execution Process
{complete_trajectory}

## Error Categories

Here are the current error categories:
{error_categories}

## Analysis Request

Provide analysis in JSON format:

{{
  "error_category": "task_understanding | solution_design | execution_error | agent_framework",
  "error_subcategory": "Specific subcategory name inside the chosen category",
  "error_description": "Brief description of the error",
  "root_cause": "Brief explanation of why the agent failed, find the ROOT cause, not just the symptoms",
  "analysis": "Detailed analysis: what commands were wrong and why, compared to the correct solution"
}}
"""
