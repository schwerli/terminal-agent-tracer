#!/bin/bash

python agents/terminus2/analyze_failures.py \
  --run-dir "/share/yaoyifan/data/terminal_result/te2_c4" \
  --tasks-dir "/share/lihan/terminal-bench/tasks" \
  --model-name app-4lj8uu-1757909116059641172 \
  --api-key "$WQ_API_KEY" \
  --base-url http://wanqing.internal/api/agent/v1/apps \
  --concurrency 2 \
  --output-dir ./analysis_results_te2_c4

python agents/terminus2/analyze_failures.py \
  --run-dir "/share/yaoyifan/data/terminal_result/te2_coder" \
  --tasks-dir "/share/lihan/terminal-bench/tasks" \
  --model-name app-4lj8uu-1757909116059641172 \
  --api-key "$WQ_API_KEY" \
  --base-url http://wanqing.internal/api/agent/v1/apps \
  --concurrency 2 \
  --output-dir ./analysis_results_te2_coder

python agents/terminus2/analyze_failures.py \
  --run-dir "/share/yaoyifan/data/terminal_result/te2_v3" \
  --tasks-dir "/share/lihan/terminal-bench/tasks" \
  --model-name app-4lj8uu-1757909116059641172 \
  --api-key "$WQ_API_KEY" \
  --base-url http://wanqing.internal/api/agent/v1/apps \
  --concurrency 2 \
  --output-dir ./analysis_results_te2_v3