#!/usr/bin/env python3
"""
Test script for Miniswe agent analysis.

Usage:
  # Generate prompt only
  python tests/test_miniswe.py --run-dir /path/to/task --tasks-dir /path/to/tasks --mode prompt

  # Run full analysis
  python tests/test_miniswe.py --run-dir /path/to/task --tasks-dir /path/to/tasks --mode analyze \
    --api-key KEY --base-url URL --model-name MODEL
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.minisweagent.data_extractor import MinisweDataExtractor
from agents.terminus1.analyze_failures import AnalysisPromptBuilder, FailureAnalyzer
from src.llm_providers import get_provider
from src.output_generator import StreamingOutputGenerator


def main():
    parser = argparse.ArgumentParser(description="Test Miniswe agent analysis")
    parser.add_argument("--run-dir", required=True, help="Path to single task directory")
    parser.add_argument("--tasks-dir", required=True, help="Path to terminal-bench tasks")
    parser.add_argument("--mode", required=True, choices=["prompt", "analyze"], help="Test mode")
    parser.add_argument("--api-key", help="API key (required for analyze mode)")
    parser.add_argument("--base-url", help="Base URL (required for analyze mode)")
    parser.add_argument("--model-name", default="gpt-4o-mini", help="Model name")
    
    args = parser.parse_args()
    
    run_dir = Path(args.run_dir)
    tasks_dir = Path(args.tasks_dir)
    
    if not run_dir.exists():
        print(f"Error: Directory not found: {run_dir}")
        sys.exit(1)
    
    # Extract task data
    extractor = MinisweDataExtractor(run_dir, tasks_dir)
    task_dirs = extractor.find_task_directories()
    
    if not task_dirs:
        print(f"Error: No task directories found in {run_dir}")
        sys.exit(1)
    
    task_result = extractor.extract_task_result(task_dirs[0])
    if not task_result:
        print("Error: Failed to extract task result")
        sys.exit(1)
    
    print(f"Extracted task: {task_result.task_id}")
    print(f"  Resolved: {task_result.is_resolved}")
    print(f"  Episodes: {len(task_result.episodes)}")
    
    # Build prompt
    builder = AnalysisPromptBuilder()
    prompt = builder.build_prompt(task_result)
    
    if args.mode == "prompt":
        print("\n" + "="*80)
        print("GENERATED PROMPT")
        print("="*80)
        print(prompt)
        print("="*80)
        print(f"\nPrompt length: {len(prompt)} characters")
    
    elif args.mode == "analyze":
        if not args.api_key or not args.base_url:
            print("Error: --api-key and --base-url required for analyze mode")
            sys.exit(1)
        
        print("\nRunning LLM analysis...")
        provider = get_provider("openai", args.model_name, args.api_key, args.base_url)
        
        output_dir = Path("./test_output_miniswe")
        output_generator = StreamingOutputGenerator(
            output_dir=output_dir,
            run_id=task_result.task_id,
            model_provider="openai-compatible",
            model_name=args.model_name
        )
        
        analyzer = FailureAnalyzer(provider, output_generator, concurrency=1)
        result = analyzer.analyze_task_sync(task_result)
        output_generator.append_result(result)
        output_generator.finalize()
        
        print(f"\nAnalysis complete!")
        print(f"  Output: {output_dir}")


if __name__ == "__main__":
    main()

