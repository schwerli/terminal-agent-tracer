"""
Configuration for terminal agent failure analysis.
"""

# Analysis prompt template
ANALYSIS_PROMPT_TEMPLATE = """You are analyzing why a terminal agent (Hermes) failed to complete a task in Terminal Bench.

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

## Analysis Request
Please analyze why the agent failed this task. Provide your response in the following JSON format:

{{
  "root_cause": "A concise explanation of the fundamental reason for failure",
  "agent_mistakes": [
    "Specific mistake 1 (analyze both the agent's analysis and the actual commands executed)",
    "Specific mistake 2",
    ...
  ],
  "analysis_summary": "A comprehensive summary combining the agent's thinking process and actual execution"
}}

Focus on:
1. What went wrong in execution? Analyze both the agent's reasoning (analysis field) and the actual commands.
2. What specific commands or decisions led to failure? Compare with the official solution to identify what should have been done.

Important context:
- The agent cannot see test results during execution
- The agent cannot perform validation checks during the generation phase
- Analyze whether the agent's analysis field correctly understood the situation
- If the agent's analysis was wrong, explain how it led to incorrect commands
- Use the test files to understand what was being validated
- Use the official solution as reference for the correct approach
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

