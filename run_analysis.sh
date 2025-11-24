#!/bin/bash
# Batch analysis script for multiple Miniswe agent trajectories
# Usage: ./run_analysis.sh

set -e

# Configuration
API_KEY="sk-sqB7WzxCtHiNmiz88sMCD8wYgXleHRzB6J8grlSDrltGD6bH"
BASE_URL="http://14.103.68.46/v1"
MODEL_NAME="gpt-4o-mini"
TASKS_DIR="/data/terminalbench/terminal-bench/tasks"
CONCURRENCY=2

# Base directory
cd /data/terminalbench/agent_failure_analysis

# Export API key
export OPENAI_API_KEY="$API_KEY"

echo "Starting batch analysis for Miniswe trajectories..."
echo "Model: $MODEL_NAME"
echo "Base URL: $BASE_URL"
echo "Concurrency: $CONCURRENCY"
echo ""

# Analysis 1: miniswe-c4
echo "==================================="
echo "Analyzing: miniswe-c4"
echo "==================================="
python agents/minisweagent/analyze_failures.py \
  --run-dir "/data/terminalbench/agent_failure_analysis/traj/miniswe-c4" \
  --tasks-dir "$TASKS_DIR" \
  --model-name "$MODEL_NAME" \
  --api-key "$API_KEY" \
  --base-url "$BASE_URL" \
  --concurrency $CONCURRENCY \
  --output-dir ./analysis_results_miniswe_c4

# Analysis 2: miniswe-codex
echo ""
echo "==================================="
echo "Analyzing: miniswe-codex"
echo "==================================="
python agents/minisweagent/analyze_failures.py \
  --run-dir "/data/terminalbench/agent_failure_analysis/traj/miniswe-codex" \
  --tasks-dir "$TASKS_DIR" \
  --model-name "$MODEL_NAME" \
  --api-key "$API_KEY" \
  --base-url "$BASE_URL" \
  --concurrency $CONCURRENCY \
  --output-dir ./analysis_results_miniswe_codex

# Analysis 3: miniswe-dsv3
echo ""
echo "==================================="
echo "Analyzing: miniswe-dsv3"
echo "==================================="
python agents/minisweagent/analyze_failures.py \
  --run-dir "/data/terminalbench/agent_failure_analysis/traj/miniswe-dsv3" \
  --tasks-dir "$TASKS_DIR" \
  --model-name "$MODEL_NAME" \
  --api-key "$API_KEY" \
  --base-url "$BASE_URL" \
  --concurrency $CONCURRENCY \
  --output-dir ./analysis_results_miniswe_dsv3

# Analysis 4: miniswe-gpt5
echo ""
echo "==================================="
echo "Analyzing: miniswe-gpt5"
echo "==================================="
python agents/minisweagent/analyze_failures.py \
  --run-dir "/data/terminalbench/agent_failure_analysis/traj/miniswe-gpt5" \
  --tasks-dir "$TASKS_DIR" \
  --model-name "$MODEL_NAME" \
  --api-key "$API_KEY" \
  --base-url "$BASE_URL" \
  --concurrency $CONCURRENCY \
  --output-dir ./analysis_results_miniswe_gpt5

echo ""
echo "==================================="
echo "All analyses complete!"
echo "==================================="
echo ""
echo "Output directories:"
echo "  - ./analysis_results_miniswe_c4"
echo "  - ./analysis_results_miniswe_codex"
echo "  - ./analysis_results_miniswe_dsv3"
echo "  - ./analysis_results_miniswe_gpt5"
