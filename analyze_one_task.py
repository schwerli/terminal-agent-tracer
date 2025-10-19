#!/usr/bin/env python3
"""
Analyze a single task for testing purposes.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from analyze_agent_failures import DataExtractor, FailureAnalyzer, AnalysisPromptBuilder
from llm_providers import get_provider


def main():
    if len(sys.argv) < 5:
        print("Usage: python analyze_one_task.py <run_dir> <model_provider> <model_name> <api_key> [base_url] [tasks_dir]")
        print("Example: python analyze_one_task.py /data/terminalbench/terminal-bench0/runs/2025-09-16__00-48-15/ custom gpt-5 sk-xxx https://api.chatanywhere.tech/v1 /data/terminalbench/terminal-bench/tasks")
        sys.exit(1)
    
    run_dir = Path(sys.argv[1])
    model_provider = sys.argv[2]
    model_name = sys.argv[3]
    api_key = sys.argv[4]
    base_url = sys.argv[5] if len(sys.argv) > 5 else None
    tasks_dir = Path(sys.argv[6]) if len(sys.argv) > 6 else None
    
    print(f"Extracting tasks from: {run_dir}")
    extractor = DataExtractor(run_dir, tasks_dir)
    
    if extractor.tasks_base_dir:
        print(f"Using tasks directory: {extractor.tasks_base_dir}")
    else:
        print("Warning: No tasks directory found")
    
    task_dirs = extractor.find_task_directories()
    print(f"Found {len(task_dirs)} task directories\n")
    
    # Find first failed task
    failed_task = None
    for task_dir in task_dirs:
        task_result = extractor.extract_task_result(task_dir)
        if task_result and not task_result.is_resolved:
            failed_task = task_result
            break
    
    if not failed_task:
        print("No failed tasks found!")
        return
    
    print(f"Testing with failed task: {failed_task.task_id}")
    print(f"Number of episodes: {len(failed_task.episodes)}")
    print(f"Test results: {failed_task.parser_results}\n")
    
    # Create provider
    print(f"Initializing LLM provider: {model_provider}/{model_name}")
    provider = get_provider(model_provider, model_name, api_key, base_url)
    
    # Analyze
    print("Sending analysis request to LLM...\n")
    analyzer = FailureAnalyzer(provider, concurrency=1)
    result = analyzer.analyze_task_sync(failed_task)
    
    if result.error:
        print(f"Error: {result.error}")
    elif result.llm_analysis:
        print("="*80)
        print("ANALYSIS RESULT")
        print("="*80)
        print(f"\nTask: {result.task_id}")
        print(f"\nRoot Cause:\n{result.llm_analysis.root_cause}")
        print(f"\nAgent Mistakes:")
        for i, mistake in enumerate(result.llm_analysis.agent_mistakes, 1):
            print(f"{i}. {mistake}")
        print(f"\nAnalysis Summary:\n{result.llm_analysis.analysis_summary}")
        print("="*80)
    else:
        print("No analysis returned")
    
    print("\nTest complete!")


if __name__ == "__main__":
    main()

