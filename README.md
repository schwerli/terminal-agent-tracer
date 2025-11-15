# Terminal Agent Failure Analysis

Analyze failures from multiple terminal agents using OpenAI-compatible LLM APIs.

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

## Agent Analysis Commands

### Terminus1 Agent

```bash
cd /data/terminalbench/agent_failure_analysis

export OPENAI_API_KEY="your-api-key"

python agents/terminus1/analyze_failures.py \
  --run-dir "/path/to/terminus1-runs" \
  --tasks-dir "/data/terminalbench/terminal-bench/tasks" \
  --model-name gpt-4o-mini \
  --api-key "$OPENAI_API_KEY" \
  --base-url https://api.chatanywhere.cn/v1 \
  --concurrency 1 \
  --output-dir ./analysis_results_terminus1
```

### Terminus2 Agent

```bash
cd /data/terminalbench/agent_failure_analysis

export OPENAI_API_KEY="your-api-key"

python agents/terminus2/analyze_failures.py \
  --run-dir "/path/to/terminus2-runs" \
  --tasks-dir "/data/terminalbench/terminal-bench/tasks" \
  --model-name gpt-4o-mini \
  --api-key "$OPENAI_API_KEY" \
  --base-url https://api.chatanywhere.cn/v1 \
  --concurrency 1 \
  --output-dir ./analysis_results_terminus2
```

### Hermes Agent

```bash
cd /data/terminalbench/agent_failure_analysis

export OPENAI_API_KEY="your-api-key"

python agents/hermes/analyze_failures.py \
  --run-dir "/path/to/hermes-runs" \
  --tasks-dir "/data/terminalbench/terminal-bench/tasks" \
  --model-name gpt-4o-mini \
  --api-key "$OPENAI_API_KEY" \
  --base-url https://api.chatanywhere.cn/v1 \
  --concurrency 1 \
  --output-dir ./analysis_results_hermes
```

### Miniswe Agent

```bash
cd /data/terminalbench/agent_failure_analysis

export OPENAI_API_KEY="your-api-key"

python agents/minisweagent/analyze_failures.py \
  --run-dir "/path/to/miniswe-c4" \
  --tasks-dir "/data/terminalbench/terminal-bench/tasks" \
  --model-name gpt-4o-mini \
  --api-key "$OPENAI_API_KEY" \
  --base-url https://api.chatanywhere.cn/v1 \
  --concurrency 1 \
  --output-dir ./analysis_results_miniswe
```

## Test Scripts

Each agent has a dedicated test script in the `tests/` directory.

### Test Terminus1

```bash
# Generate prompt for a single task
python tests/test_terminus1.py \
  --run-dir "/path/to/terminus1-runs/task-name" \
  --tasks-dir "/data/terminalbench/terminal-bench/tasks" \
  --mode prompt

# Run analysis on a single task
python tests/test_terminus1.py \
  --run-dir "/path/to/terminus1-runs/task-name" \
  --tasks-dir "/data/terminalbench/terminal-bench/tasks" \
  --mode analyze \
  --api-key "$OPENAI_API_KEY" \
  --base-url https://api.chatanywhere.cn/v1 \
  --model-name gpt-4o-mini
```

### Test Terminus2

```bash
# Generate prompt for a single task
python tests/test_terminus2.py \
  --run-dir "/path/to/terminus2-runs/task-name" \
  --tasks-dir "/data/terminalbench/terminal-bench/tasks" \
  --mode prompt

# Run analysis on a single task
python tests/test_terminus2.py \
  --run-dir "/path/to/terminus2-runs/task-name" \
  --tasks-dir "/data/terminalbench/terminal-bench/tasks" \
  --mode analyze \
  --api-key "$OPENAI_API_KEY" \
  --base-url https://api.chatanywhere.cn/v1 \
  --model-name gpt-4o-mini
```

### Test Hermes

```bash
# Generate prompt for a single task
python tests/test_hermes.py \
  --run-dir "/path/to/hermes-runs/task-name" \
  --tasks-dir "/data/terminalbench/terminal-bench/tasks" \
  --mode prompt

# Run analysis on a single task
python tests/test_hermes.py \
  --run-dir "/path/to/hermes-runs/task-name" \
  --tasks-dir "/data/terminalbench/terminal-bench/tasks" \
  --mode analyze \
  --api-key "$OPENAI_API_KEY" \
  --base-url https://api.chatanywhere.cn/v1 \
  --model-name gpt-4o-mini
```

### Test Miniswe

```bash
# Generate prompt for a single task
python tests/test_miniswe.py \
  --run-dir "/path/to/miniswe-c4/task-name" \
  --tasks-dir "/data/terminalbench/terminal-bench/tasks" \
  --mode prompt

# Run analysis on a single task
python tests/test_miniswe.py \
  --run-dir "/path/to/miniswe-c4/task-name" \
  --tasks-dir "/data/terminalbench/terminal-bench/tasks" \
  --mode analyze \
  --api-key "$OPENAI_API_KEY" \
  --base-url https://api.chatanywhere.cn/v1 \
  --model-name gpt-4o-mini
```

## Architecture

```
agent_failure_analysis/
├── src/                      # Shared components
│   ├── models.py            # Data models
│   ├── llm_providers.py     # OpenAI-compatible LLM provider
│   ├── config.py            # Analysis prompt template and error categories
│   ├── task_extractor.py    # Extract from terminal-bench tasks
│   └── output_generator.py  # Streaming JSONL + Markdown output
├── agents/                   # Agent-specific implementations
│   ├── hermes/              # Hermes agent (response.txt format)
│   ├── terminus1/           # Terminus1 agent (response.json format)
│   ├── terminus2/           # Terminus2 agent (response.txt format)
│   └── minisweagent/        # Miniswe agent (bash blocks from post-agent.txt)
└── tests/                    # Test scripts for each agent
```

## Output

- `analysis_results.jsonl`: Streaming JSONL (one result per line)
- `analysis_report.md`: Human-readable Markdown report with error categories, subcategories, and detailed analysis

## Features

- **Multi-agent support**: Hermes, Terminus1, Terminus2, and Miniswe agents
- **Unified LLM interface**: Single OpenAI-compatible provider for all agents
- **Streaming output**: Results written immediately after analysis
- **Structured error taxonomy**: High-level categories (task_understanding, solution_design, execution_error, agent_framework) with subcategories
- **Complete context**: Includes task definition, tests, solution, and full agent trajectory
