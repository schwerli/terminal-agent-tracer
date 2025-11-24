#!/usr/bin/env python3
"""
OpenHands Agent Failure Analysis Script.

Analyzes failed tasks from OpenHands runs on Terminal Bench, using an
OpenAI-compatible LLM API to provide detailed failure analysis.

The key difference from other agents is how we build the complete
trajectory:
- We read the OpenHands session JSON under each task's `sessions/` dir.
- We normalize it into a compact sequence of steps where each step keeps:
  - only `id` and `args` for action entries
  - only `content` and `extras` for observation entries, paired via `cause`
- The normalized steps are serialized as JSON Lines and attached as the
  single episode's `terminal_output`, which is then fed into the
  `complete_trajectory` section of the analysis prompt.
"""

import argparse
import sys
import traceback
from pathlib import Path
from typing import List

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.models import TaskResult  # type: ignore
from src.llm_providers import get_provider, LLMProvider  # type: ignore
from src.output_generator import StreamingOutputGenerator  # type: ignore
from agents.terminus2.analyze_failures import (  # type: ignore
    FailureAnalyzer,
    AnalysisPromptBuilder,
)
from agents.openhands.data_extractor import OpenHandsDataExtractor


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze OpenHands agent failures using an OpenAI-compatible LLM API"
    )

    parser.add_argument(
        "--run-dir",
        required=True,
        help="Path to OpenHands run directory (traj/openhands)",
    )
    parser.add_argument(
        "--tasks-dir",
        required=True,
        help="Path to terminal-bench tasks directory",
    )
    parser.add_argument(
        "--model-provider",
        required=False,
        help="Ignored (for backward compatibility)",
    )
    parser.add_argument(
        "--model-name",
        required=True,
        help="Model name",
    )
    parser.add_argument("--api-key", help="API key (or use environment variable)")
    parser.add_argument(
        "--base-url",
        help="Base URL for OpenAI-compatible API provider",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=1,
        help="Number of parallel API requests (default: 1)",
    )
    parser.add_argument(
        "--output-dir",
        default="./analysis_output",
        help="Output directory (default: ./analysis_output)",
    )

    args = parser.parse_args()

    run_dir = Path(args.run_dir)
    tasks_dir = Path(args.tasks_dir)

    if not run_dir.exists():
        print(f"Error: Run directory not found: {run_dir}")
        sys.exit(1)

    if not tasks_dir.exists():
        print(f"Error: Tasks directory not found: {tasks_dir}")
        sys.exit(1)

    # Extract data
    print(f"Extracting data from: {run_dir}")
    print(f"Using tasks directory: {tasks_dir}")
    extractor = OpenHandsDataExtractor(run_dir, tasks_dir)

    task_dirs = extractor.find_task_directories()
    print(f"Found {len(task_dirs)} task directories")

    tasks: List[TaskResult] = []
    for task_dir in task_dirs:
        task_result = extractor.extract_task_result(task_dir)
        if task_result:
            tasks.append(task_result)

    print(f"Successfully extracted {len(tasks)} tasks")
    resolved_count = sum(1 for t in tasks if t.is_resolved)
    failed_count = len(tasks) - resolved_count
    print(f"- Resolved: {resolved_count}")
    print(f"- Failed: {failed_count}")

    if failed_count == 0:
        print("No failed tasks to analyze!")
        return

    # Initialize LLM provider (single OpenAI-compatible provider)
    provider: LLMProvider = get_provider(
        provider_name="openai",  # ignored
        model_name=args.model_name,
        api_key=args.api_key,
        base_url=args.base_url,
    )

    # Initialize streaming output generator
    output_dir = Path(args.output_dir)
    output_generator = StreamingOutputGenerator(
        output_dir=output_dir,
        run_id=run_dir.name,
        model_provider="openai-compatible",
        model_name=args.model_name,
    )

    # Analyze failures with streaming output
    analyzer = FailureAnalyzer(provider, output_generator, args.concurrency)
    analyzer.analyze_tasks_sync(tasks)

    # Finalize output
    output_generator.finalize()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nAnalysis interrupted by user")
        sys.exit(1)
    except Exception as e:  # pragma: no cover - defensive
        print(f"Error: {e}")
        traceback.print_exc()
        sys.exit(1)


