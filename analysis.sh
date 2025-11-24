#!/bin/bash


python agents/openhands/analyze_failures.py \
  --run-dir "/share/yaoyifan/data/terminal_result/openhands_c4" \
  --tasks-dir "/share/lihan/terminal-bench/tasks" \
  --model-name app-4lj8uu-1757909116059641172 \
  --api-key "$WQ_API_KEY" \
  --base-url http://wanqing.internal/api/agent/v1/apps \
  --concurrency 2 \
  --output-dir ./analysis_results_openhands_c4

python agents/openhands/analyze_failures.py \
  --run-dir "/share/yaoyifan/data/terminal_result/openhands_coder" \
  --tasks-dir "/share/lihan/terminal-bench/tasks" \
  --model-name app-4lj8uu-1757909116059641172 \
  --api-key "$WQ_API_KEY" \
  --base-url http://wanqing.internal/api/agent/v1/apps \
  --concurrency 2 \
  --output-dir ./analysis_results_openhands_coder

python agents/openhands/analyze_failures.py \
  --run-dir "/share/yaoyifan/data/terminal_result/openhands_gpt4.1" \
  --tasks-dir "/share/lihan/terminal-bench/tasks" \
  --model-name app-4lj8uu-1757909116059641172 \
  --api-key "$WQ_API_KEY" \
  --base-url http://wanqing.internal/api/agent/v1/apps \
  --concurrency 2 \
  --output-dir ./analysis_results_openhands_gpt4_1

python agents/openhands/analyze_failures.py \
  --run-dir "/share/yaoyifan/data/terminal_result/openhands_v3" \
  --tasks-dir "/share/lihan/terminal-bench/tasks" \
  --model-name app-4lj8uu-1757909116059641172 \
  --api-key "$WQ_API_KEY" \
  --base-url http://wanqing.internal/api/agent/v1/apps \
  --concurrency 2 \
  --output-dir ./analysis_results_openhands_v3