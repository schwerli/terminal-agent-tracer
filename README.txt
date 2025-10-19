Terminal Agent Failure Analyzer
================================

Installation:
  pip install -r failure_analysis_requirements.txt

Basic Usage:
  python analyze_agent_failures.py \
    --run-dir <path-to-run-directory> \
    --tasks-dir <path-to-terminal-bench-tasks> \
    --model-provider <openai|anthropic|custom> \
    --model-name <model-name>

Example:
  export OPENAI_API_KEY="your-key"
  python analyze_agent_failures.py \
    --run-dir ../terminal-bench0/runs/2025-09-16__00-48-15/ \
    --tasks-dir /data/terminalbench/terminal-bench/tasks \
    --model-provider openai \
    --model-name gpt-4-turbo-preview \
    --concurrency 5 \
    --output-dir ./results

Test Prompt Format (without API calls):
  python test_new_format.py ../terminal-bench0/runs/2025-09-16__00-48-15/ /data/terminalbench/terminal-bench/tasks

Files:
  - analyze_agent_failures.py  Main script
  - models.py                   Data models
  - llm_providers.py           LLM provider implementations
  - config.py                   Configuration
  - test_extraction.py          Test data extraction without API
  - test_new_format.py          Test new prompt format
  - example_analysis.sh         Example bash script
  - failure_analysis_requirements.txt  Dependencies

What LLM Receives:
  1. Task Information: task ID and full instruction
  2. Test Results: which tests passed/failed
  3. Test Files: actual test code that validates the solution
  4. Official Solution: reference implementation from task definition
  5. Initial Prompt: complete episode-0 prompt
  6. Complete Execution Process: ALL episodes with:
     - Analysis: agent's reasoning
     - Plan: agent's plan
     - Commands: actual commands executed
     - Terminal Output: execution results (merged per episode)

Output Format:
  - analysis_results.jsonl: JSONL format (one JSON per line)
  - analysis_report.md: Markdown report

Arguments:
  --run-dir       Path to run directory (required)
  --tasks-dir     Path to terminal-bench tasks directory (optional, auto-searches if not provided)
  --model-provider  LLM provider: openai, anthropic, custom (required)
  --model-name    Model name (required)
  --api-key       API key (or use environment variable)
  --base-url      Base URL for custom provider
  --concurrency   Number of parallel requests (default: 1)
  --output-dir    Output directory (default: ./analysis_output)
  --max-episodes  Max episodes to include (default: 50)
  --async-mode    Use async mode for better concurrency

Environment Variables:
  OPENAI_API_KEY      OpenAI API key
  ANTHROPIC_API_KEY   Anthropic API key
  CUSTOM_API_KEY      Custom API key
  CUSTOM_API_BASE_URL Custom API base URL

Output:
  - analysis_results.json  Structured JSON results
  - analysis_report.md     Human-readable report

