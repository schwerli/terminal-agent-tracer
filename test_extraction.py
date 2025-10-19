#!/usr/bin/env python3
"""
Test script to verify data extraction without calling LLM APIs.
"""
import sys
from pathlib import Path

# Import from local modules
from analyze_agent_failures import DataExtractor, AnalysisPromptBuilder


def main():
    """Test data extraction functionality."""
    if len(sys.argv) < 2:
        print("Usage: python test_extraction.py <run_directory>")
        print("Example: python test_extraction.py terminal-bench0/runs/2025-09-16__00-48-15/")
        sys.exit(1)
    
    run_dir = Path(sys.argv[1])
    
    if not run_dir.exists():
        print(f"Error: Directory not found: {run_dir}")
        sys.exit(1)
    
    print(f"Testing data extraction from: {run_dir}\n")
    
    # Create extractor
    extractor = DataExtractor(run_dir)
    
    # Find task directories
    print("Finding task directories...")
    task_dirs = extractor.find_task_directories()
    print(f"Found {len(task_dirs)} task directories\n")
    
    # Extract first few tasks
    print("Extracting task data...")
    tasks = []
    for i, task_dir in enumerate(task_dirs[:5]):  # Test with first 5 tasks
        print(f"  Extracting: {task_dir.name}")
        task_result = extractor.extract_task_result(task_dir)
        if task_result:
            tasks.append(task_result)
            print(f"    - Task ID: {task_result.task_id}")
            print(f"    - Resolved: {task_result.is_resolved}")
            print(f"    - Episodes: {len(task_result.episodes)}")
            test_count = len(task_result.parser_results) if task_result.parser_results else 0
            print(f"    - Test results: {test_count} tests")
    
    print(f"\nSuccessfully extracted {len(tasks)} tasks")
    
    # Test prompt building for first failed task
    failed_tasks = [t for t in tasks if not t.is_resolved]
    if failed_tasks:
        print(f"\nTesting prompt building for first failed task...")
        prompt_builder = AnalysisPromptBuilder()
        prompt = prompt_builder.build_prompt(failed_tasks[0])
        
        print(f"\nGenerated prompt preview (first 500 chars):")
        print("=" * 80)
        print(prompt[:500])
        print("...")
        print("=" * 80)
        print(f"\nFull prompt length: {len(prompt)} characters")
    else:
        print("\nNo failed tasks found to test prompt building")
    
    print("\nData extraction test complete!")


if __name__ == "__main__":
    main()

