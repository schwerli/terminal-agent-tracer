"""
Configuration for terminal agent failure analysis.
"""

# Error category list (will be dynamically updated)
ERROR_CATEGORIES = [
    "incorrect_algorithm_choice",
    "missing_validation_step",
    "wrong_file_path",
    "incomplete_exploration",
    "premature_task_completion",
    "command_syntax_error",
    "misunderstanding_requirements",
    "incorrect_output_format",
    "missing_error_handling",
    "logic_error_in_implementation"
]

# Analysis prompt template
ANALYSIS_PROMPT_TEMPLATE = """You are analyzing why a terminal agent failed to complete a task in Terminal Bench.

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

Please analyze why the agent failed this task. **Trace back to the earliest decision error.**

Provide your response in the following JSON format:

{{
  "earliest_error_command": "The specific command where the error first occurred",
  "error_category": "Choose from the list above, or create a NEW category if none fit",
  "new_category_created": "If you created a new category, provide it here (otherwise null)",
  "root_cause": "A concise explanation of the fundamental reason for failure, focusing on the earliest mistake",
  "agent_mistakes": [
    "Specific mistake 1 (analyze both the agent's analysis and the actual commands executed)",
    "Specific mistake 2",
    ...
  ],
  "analysis_summary": "A comprehensive summary tracing the error from its earliest occurrence"
}}

Focus on:
1. **Trace backwards**: Start from the failure and work backwards to find the FIRST mistake
2. **Identify the earliest error**: Which episode and which command first introduced the problem?
3. **Categorize the error**: Does it match one of the existing categories, or do you need to create a new one?
4. Compare with the official solution to identify what should have been done differently

Important context:
- The agent cannot see test results during execution
- The agent cannot perform validation checks during the generation phase
- Find the ROOT cause, not just the symptoms
"""

# Model configurations
DEFAULT_MODELS = {
    "openai": "gpt-4-turbo-preview",
    "anthropic": "claude-3-opus-20240229",
    "custom": "custom-model"
}

# API endpoints
API_ENDPOINTS = {
    "openai": "https://api.openai.com/v1",
    "anthropic": "https://api.anthropic.com/v1",
    "custom": "http://localhost:8000/v1"
}

# Rate limiting
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds
RATE_LIMIT_DELAY = 1  # seconds between requests

# Output settings
MAX_EPISODES_TO_INCLUDE = 50  # Maximum episodes to include in analysis (show all by default)
MAX_TERMINAL_OUTPUT_CHARS = 10000  # Maximum terminal output characters
TRUNCATION_MESSAGE = "\n... [OUTPUT TRUNCATED] ...\n"
MAX_INITIAL_PROMPT_CHARS = 5000  # Maximum characters for initial prompt

