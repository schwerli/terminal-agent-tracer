#!/usr/bin/env python3
"""
Test script to show the new prompt format without calling LLM APIs.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from analyze_agent_failures import DataExtractor, AnalysisPromptBuilder


def main():
    """Test the new prompt format."""
    if len(sys.argv) < 2:
        print("Usage: python test_new_format.py <run_directory> [tasks_directory]")
        print("Example: python test_new_format.py /data/terminalbench/terminal-bench0/runs/2025-09-16__00-48-15/ /data/terminalbench/terminal-bench/tasks")
        sys.exit(1)
    
    run_dir = Path(sys.argv[1])
    tasks_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    
    if not run_dir.exists():
        print(f"Error: Directory not found: {run_dir}")
        sys.exit(1)
    
    print(f"Testing new format with data from: {run_dir}\n")
    
    # Create extractor
    extractor = DataExtractor(run_dir, tasks_dir)
    
    if extractor.tasks_base_dir:
        print(f"Using tasks directory: {extractor.tasks_base_dir}\n")
    
    # Find task directories
    task_dirs = extractor.find_task_directories()
    print(f"Found {len(task_dirs)} task directories\n")
    
    # Extract first failed task
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
    print(f"Number of episodes: {len(failed_task.episodes)}\n")
    
    # Build prompt
    prompt_builder = AnalysisPromptBuilder()
    prompt = prompt_builder.build_prompt(failed_task)
    
    # Show prompt structure
    print("=" * 80)
    print("GENERATED PROMPT FOR LLM")
    print("=" * 80)
    print(prompt)
    print("=" * 80)
    print(f"\nTotal prompt length: {len(prompt)} characters")
    print(f"\nThis prompt will be sent to the LLM for analysis.")


if __name__ == "__main__":
    main()

