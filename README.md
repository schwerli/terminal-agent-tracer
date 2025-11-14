# Terminal Agent Failure Analysis

Analyze failures from multiple terminal agents (Hermes, Terminus/C4) using LLM APIs.

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Hermes Agent Analysis

```bash
# Test prompt format
python tests/test_new_format.py hermes \
  /path/to/hermes-runs \
  /path/to/terminal-bench/tasks

# Run full analysis
export WQ_API_KEY="your-api-key"
python agents/hermes/analyze_failures.py \
  --run-dir /path/to/hermes-runs \
  --tasks-dir /path/to/terminal-bench/tasks \
  --model-provider custom \
  --model-name app-4lj8uu-1757909116059641172 \
  --api-key "$WQ_API_KEY" \
  --base-url http://wanqing.internal/api/agent/v1/apps \
  --concurrency 1 \
  --output-dir ./analysis_results
```

### Terminus (C4) Agent Analysis

```bash
# Test prompt format
python tests/test_new_format.py terminus \
  /path/to/c4-traj \
  /path/to/terminal-bench/tasks

# Run full analysis
export WQ_API_KEY="your-api-key"
python agents/terminus/analyze_failures.py \
  --run-dir /path/to/c4-traj \
  --tasks-dir /path/to/terminal-bench/tasks \
  --model-provider custom \
  --model-name app-4lj8uu-1757909116059641172 \
  --api-key "$WQ_API_KEY" \
  --base-url http://wanqing.internal/api/agent/v1/apps \
  --concurrency 1 \
  --output-dir ./analysis_results
```

## Test Scripts

### Test Data Extraction

```bash
python tests/test_extraction.py hermes \
  /path/to/runs \
  /path/to/terminal-bench/tasks

python tests/test_extraction.py terminus \
  /path/to/runs \
  /path/to/terminal-bench/tasks
```

### Test Prompt Generation

```bash
python tests/test_new_format.py hermes \
  /path/to/runs \
  /path/to/terminal-bench/tasks

python tests/test_new_format.py terminus \
  /path/to/runs \
  /path/to/terminal-bench/tasks
```

### Test Single Task Analysis

```bash
python tests/analyze_one_task.py hermes \
  /path/to/runs \
  /path/to/terminal-bench/tasks \
  custom \
  app-4lj8uu-1757909116059641172 \
  "$WQ_API_KEY" \
  http://wanqing.internal/api/agent/v1/apps

python tests/analyze_one_task.py terminus \
  /path/to/runs \
  /path/to/terminal-bench/tasks \
  custom \
  app-4lj8uu-1757909116059641172 \
  "$WQ_API_KEY" \
  http://wanqing.internal/api/agent/v1/apps
```

## Architecture

```
agent_failure_analysis/
├── src/                      # Shared components
│   ├── models.py            # Data models
│   ├── llm_providers.py     # LLM providers (OpenAI, Anthropic, Custom)
│   ├── config.py            # Prompts and error categories
│   ├── task_extractor.py    # Extract from terminal-bench tasks
│   └── output_generator.py  # Streaming JSONL + Markdown output
├── agents/                   # Agent-specific extractors
│   ├── hermes/              # Hermes agent (response.txt)
│   └── terminus/            # Terminus/C4 agent (response.json)
└── tests/                    # Test scripts
```

## Output

- `analysis_results.jsonl`: Streaming JSONL (one result per line)
- `analysis_report.md`: Human-readable Markdown report

## Features

- **Multi-agent support**: Hermes and Terminus (C4) agents
- **Streaming output**: Results written immediately after analysis
- **Error tracking**: Traces back to earliest error command
- **Dynamic error categories**: Creates new categories as needed
- **Complete context**: Includes task definition, tests, solution, and full agent trajectory

