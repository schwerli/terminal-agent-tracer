"""
Task definition and solution extractor from terminal-bench tasks directory.
"""
from pathlib import Path
from typing import Optional, Tuple
from dataclasses import dataclass


@dataclass
class TaskInfo:
    """Information extracted from terminal-bench tasks directory."""
    task_definition: Optional[str] = None
    official_solution: Optional[str] = None
    test_file_content: Optional[str] = None


def extract_task_info(task_id: str, tasks_base_dir: Path) -> TaskInfo:
    """
    Extract task definition, solution, and test files from terminal-bench tasks directory.
    
    Args:
        task_id: Task identifier
        tasks_base_dir: Path to terminal-bench/tasks directory
        
    Returns:
        TaskInfo with extracted content
    """
    info = TaskInfo()
    
    try:
        task_dir = tasks_base_dir / task_id
        if not task_dir.exists():
            return info
        
        # Extract task.yaml
        task_yaml = task_dir / "task.yaml"
        if task_yaml.exists():
            info.task_definition = _read_file(task_yaml)
        
        # Extract solution.sh
        solution_file = task_dir / "solution.sh"
        if solution_file.exists():
            info.official_solution = _read_file(solution_file)
        
        # Extract test files
        tests_dir = task_dir / "tests"
        if tests_dir.exists():
            test_files = []
            for test_file in tests_dir.glob("*.py"):
                content = _read_file(test_file)
                if content:
                    test_files.append(f"=== {test_file.name} ===\n{content}")
            if test_files:
                info.test_file_content = "\n\n".join(test_files)
    
    except Exception as e:
        print(f"Warning: Could not extract task info for {task_id}: {e}")
    
    return info


def _read_file(file_path: Path) -> Optional[str]:
    """Read file content safely."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None

