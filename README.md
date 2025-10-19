# Terminal Agent Failure Analyzer

Analyze why Hermes terminal agent failed to solve tasks in Terminal Bench using LLM APIs.

## Features

- **Complete Execution Analysis**: Extract prompts, responses, commands, and terminal output
- **Test & Solution Comparison**: Compare agent's approach with official solutions and test files
- **Multi-Provider Support**: OpenAI, Anthropic, or custom OpenAI-compatible APIs
- **Parallel Processing**: Configurable concurrency for faster analysis
- **Dual Output Format**: JSONL for data processing and Markdown for human readability

## Quick Start

### Installation

```bash
pip install -r failure_analysis_requirements.txt
```

### Basic Usage

```bash
# Analyze failed tasks
python analyze_agent_failures.py \
  --run-dir /path/to/runs/2025-09-16__00-48-15/ \
  --model-provider custom \
  --model-name gpt-4 \
  --api-key YOUR_API_KEY \
  --base-url https://api.example.com/v1 \
  --concurrency 3 \
  --output-dir ./results
```

### Test Single Task

```bash
# Test with one task before running full analysis
python analyze_one_task.py \
  /path/to/runs/2025-09-16__00-48-15/ \
  custom \
  gpt-4 \
  YOUR_API_KEY \
  https://api.example.com/v1
```

## What Gets Analyzed

The analyzer provides LLM with comprehensive context:

1. **Task Information**: Full task description and requirements
2. **Test Results**: Which tests passed/failed
3. **Test Files**: Actual test code that validates solutions
4. **Official Solution**: Reference implementation for comparison
5. **Agent's Thinking Process**: All episodes with:
   - Analysis: Agent's reasoning at each step
   - Plan: Agent's intended actions
   - Commands: Actual commands executed
   - Terminal Output: Execution results (per episode)

## Output Format

### JSONL Output (`analysis_results.jsonl`)
- Line 1: Metadata (run info, model, statistics)
- Subsequent lines: One JSON object per failed task

### Markdown Report (`analysis_report.md`)
- Summary statistics
- Per-task failure analysis with root cause and mistakes
- Human-readable format

## Configuration

Environment variables:
- `OPENAI_API_KEY`: For OpenAI provider
- `ANTHROPIC_API_KEY`: For Anthropic provider
- `CUSTOM_API_KEY`: For custom provider

## Command-Line Options

```
--run-dir         Path to run directory (required)
--model-provider  LLM provider: openai, anthropic, custom (required)
--model-name      Model name (required)
--api-key         API key (or use environment variable)
--base-url        Base URL for custom API
--concurrency     Parallel requests (default: 1)
--output-dir      Output directory (default: ./analysis_output)
--max-episodes    Max episodes to include (default: 50)
```

## Architecture

- **analyze_agent_failures.py**: Main analysis script
- **models.py**: Data models for tasks and analysis results
- **llm_providers.py**: Abstract LLM interface with multiple implementations
- **config.py**: Configuration and prompt templates
- **analyze_one_task.py**: Test script for single task
- **test_extraction.py**: Verify data extraction without API calls

## Example Workflow

```bash
# 1. Test data extraction (no API calls)
python test_extraction.py /path/to/runs/

# 2. Test with one task
python analyze_one_task.py /path/to/runs/ openai gpt-4 YOUR_KEY

# 3. Run full analysis with parallel processing
python analyze_agent_failures.py \
  --run-dir /path/to/runs/ \
  --model-provider openai \
  --model-name gpt-4 \
  --concurrency 5 \
  --output-dir ./analysis_results

# 4. Check results
cat ./analysis_results/analysis_report.md
```

## Important Notes

- The analyzer respects API rate limits with configurable delays
- Start with low concurrency (1-3) to avoid rate limiting
- Agent cannot see test results during execution (this is noted in analysis)
- Test files and official solutions help identify what should have been done

## License

See LICENSE file for details.
