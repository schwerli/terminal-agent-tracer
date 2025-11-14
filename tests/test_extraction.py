#!/usr/bin/env python3
"""
Test script to verify data extraction without calling LLM APIs.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

def main():
    """Test data extraction functionality."""
    if len(sys.argv) < 4:
        print("Usage: python test_extraction.py <agent_type> <run_directory> <tasks_directory>")
        print("Example: python test_extraction.py hermes /path/to/run /path/to/terminal-bench/tasks")
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
    
    print(f"Testing {agent_type} data extraction from: {run_dir}\n")
    
    # Import appropriate extractor
    if agent_type == "hermes":
        from agents.hermes.data_extractor import HermesDataExtractor as DataExtractor
    elif agent_type == "terminus":
        from agents.terminus.data_extractor import TerminusDataExtractor as DataExtractor
    else:
        print(f"Unknown agent type: {agent_type}")
        sys.exit(1)
    
    # Create extractor
    extractor = DataExtractor(run_dir, tasks_dir)
    
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
    print("\nData extraction test complete!")


if __name__ == "__main__":
    main()

