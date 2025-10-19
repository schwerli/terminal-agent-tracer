#!/bin/bash

# Example script for running terminal agent failure analysis

# Configuration
RUN_DIR="/data/terminalbench/terminal-bench0/runs/2025-09-16__00-48-15"
TASKS_DIR="/data/terminalbench/terminal-bench/tasks"

# Set your API key (choose one)
# export OPENAI_API_KEY="your-openai-key-here"
# export ANTHROPIC_API_KEY="your-anthropic-key-here"

# Example 1: Basic analysis with OpenAI GPT-4 (sequential)
echo "Example 1: Sequential analysis with GPT-4"
python analyze_agent_failures.py \
  --run-dir "$RUN_DIR" \
  --tasks-dir "$TASKS_DIR" \
  --model-provider openai \
  --model-name gpt-4-turbo-preview \
  --output-dir ./analysis_output_gpt4

# Example 2: Parallel analysis with Claude (concurrency=3)
echo "Example 2: Parallel analysis with Claude"
python analyze_agent_failures.py \
  --run-dir "$RUN_DIR" \
  --tasks-dir "$TASKS_DIR" \
  --model-provider anthropic \
  --model-name claude-3-opus-20240229 \
  --concurrency 3 \
  --output-dir ./analysis_output_claude

# Example 3: Custom API provider
echo "Example 3: Custom API provider"
python analyze_agent_failures.py \
  --run-dir "$RUN_DIR" \
  --tasks-dir "$TASKS_DIR" \
  --model-provider custom \
  --model-name gpt-5 \
  --base-url https://api.chatanywhere.tech/v1 \
  --api-key YOUR_CUSTOM_KEY \
  --output-dir ./analysis_output_custom

# Example 4: High concurrency with async mode
echo "Example 4: High concurrency async mode"
python analyze_agent_failures.py \
  --run-dir "$RUN_DIR" \
  --tasks-dir "$TASKS_DIR" \
  --model-provider openai \
  --model-name gpt-4 \
  --concurrency 10 \
  --async-mode \
  --output-dir ./analysis_output_async

echo "Analysis complete! Check the output directories for results."

