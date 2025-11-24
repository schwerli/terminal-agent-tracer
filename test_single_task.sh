#!/bin/bash
# Test script for analyzing a single task
# Usage: ./test_single_task.sh

set -e

# Configuration
API_KEY="sk-sqB7WzxCtHiNmiz88sMCD8wYgXleHRzB6J8grlSDrltGD6bH"
BASE_URL="http://14.103.68.46/v1"
MODEL_NAME="gpt-4o-mini"
TASKS_DIR="/data/terminalbench/terminal-bench/tasks"

# Test with a single task from miniswe-c4
TEST_TASK_DIR="/data/terminalbench/agent_failure_analysis/traj/miniswe-c4/blind-maze-explorer-algorithm"

# Base directory
cd /data/terminalbench/agent_failure_analysis

# Export API key
export OPENAI_API_KEY="$API_KEY"

echo "Testing single task analysis..."
echo "Task directory: $TEST_TASK_DIR"
echo "Model: $MODEL_NAME"
echo "Base URL: $BASE_URL"
echo ""

# Step 1: Generate prompt only (to verify extraction works)
echo "==================================="
echo "Step 1: Generating prompt"
echo "==================================="
python tests/test_miniswe.py \
  --run-dir "$TEST_TASK_DIR" \
  --tasks-dir "$TASKS_DIR" \
  --mode prompt \
  | head -n 100

echo ""
echo "Prompt generation successful!"
echo ""

# Step 2: Run full analysis
echo "==================================="
echo "Step 2: Running full analysis"
echo "==================================="
python tests/test_miniswe.py \
  --run-dir "$TEST_TASK_DIR" \
  --tasks-dir "$TASKS_DIR" \
  --mode analyze \
  --api-key "$API_KEY" \
  --base-url "$BASE_URL" \
  --model-name "$MODEL_NAME"

echo ""
echo "==================================="
echo "Test complete!"
echo "==================================="
echo "Check output in: ./test_output_miniswe/"

