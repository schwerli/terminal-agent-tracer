#!/usr/bin/env python3
"""
Test script to show the prompt format without calling LLM APIs.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

def main():
    """Test the prompt format."""
    if len(sys.argv) < 4:
        print("Usage: python test_new_format.py <agent_type> <run_directory> <tasks_directory>")
        print("Example: python test_new_format.py hermes /path/to/run /path/to/terminal-bench/tasks")
        print("Agent types: hermes, terminus")
        sys.exit(1)
    
    agent_type = sys.argv[1].lower()
    run_dir = Path(sys.argv[2])
    tasks_dir = Path(sys.argv[3])
    
    if not run_dir.exists():
        print(f"Error: Directory not found: {run_dir}")
        sys.exit(1)
    
    if not tasks_dir.exists():
        print(f"Error: Tasks directory not found: {tasks_dir}")
        sys.exit(1)
    
    print(f"Testing {agent_type} prompt format with data from: {run_dir}\n")
    
    # Import appropriate extractor and prompt builder
    if agent_type == "hermes":
        from agents.hermes.data_extractor import HermesDataExtractor as DataExtractor
        from agents.hermes.analyze_failures import AnalysisPromptBuilder
    elif agent_type == "terminus":
        from agents.terminus.data_extractor import TerminusDataExtractor as DataExtractor
        from agents.terminus.analyze_failures import AnalysisPromptBuilder
    else:
        print(f"Unknown agent type: {agent_type}")
        sys.exit(1)
    
    # Create extractor
    extractor = DataExtractor(run_dir, tasks_dir)
    
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

