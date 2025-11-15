"""
Terminus2 agent data extractor - extracts from response.txt format.
"""
import json
import traceback
from pathlib import Path
from typing import List, Optional, Dict, Any

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.models import TaskResult, EpisodeData
from src.task_extractor import extract_task_info


class Terminus2DataExtractor:
    """Extract task data from Terminus2 agent run directory."""
    
    def __init__(self, run_dir: Path, tasks_base_dir: Optional[Path] = None):
        self.run_dir = run_dir
        self.tasks_base_dir = tasks_base_dir
    
    def find_task_directories(self) -> List[Path]:
        """Find all task directories in the run."""
        task_dirs = []
        
        for item in self.run_dir.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                # Look for subdirectories with results.json
                for subitem in item.iterdir():
                    if subitem.is_dir():
                        results_file = subitem / "results.json"
                        if results_file.exists():
                            task_dirs.append(subitem)
                        break
                # Also check if the directory itself has results.json
                results_file = item / "results.json"
                if results_file.exists():
                    task_dirs.append(item)
        
        return sorted(task_dirs)
    
    def extract_task_result(self, task_dir: Path) -> Optional[TaskResult]:
        """Extract complete task result from directory."""
        try:
            results_file = task_dir / "results.json"
            if not results_file.exists():
                print(f"Warning: No results.json in {task_dir}")
                return None
            
            # Load results.json
            with open(results_file, 'r') as f:
                results_data = json.load(f)
            
            # Create TaskResult
            task_result = TaskResult(
                task_id=results_data.get("task_id", "unknown"),
                trial_name=results_data.get("trial_name", "unknown"),
                is_resolved=results_data.get("is_resolved", False),
                failure_mode=results_data.get("failure_mode", "unknown"),
                instruction=results_data.get("instruction", ""),
                parser_results=results_data.get("parser_results", {}),
                total_input_tokens=results_data.get("total_input_tokens", 0),
                total_output_tokens=results_data.get("total_output_tokens", 0),
                trial_started_at=results_data.get("trial_started_at"),
                trial_ended_at=results_data.get("trial_ended_at"),
                agent_started_at=results_data.get("agent_started_at"),
                agent_ended_at=results_data.get("agent_ended_at"),
                test_started_at=results_data.get("test_started_at"),
                test_ended_at=results_data.get("test_ended_at"),
                task_directory=str(task_dir),
                results_file=str(results_file)
            )
            
            # Extract episodes
            agent_logs_dir = task_dir / "agent-logs"
            if agent_logs_dir.exists():
                episodes = []
                for episode_dir in sorted(agent_logs_dir.iterdir()):
                    if episode_dir.is_dir() and episode_dir.name.startswith("episode-"):
                        episode_num = int(episode_dir.name.split("-")[1])
                        episode_data = self._extract_episode(episode_dir, episode_num)
                        if episode_data:
                            episodes.append(episode_data)
                task_result.episodes = sorted(episodes, key=lambda e: e.episode_number)
            
            # Extract panes output
            panes_dir = task_dir / "panes"
            if panes_dir.exists():
                task_result.pre_agent_output = self._read_file(panes_dir / "pre-agent.txt")
                task_result.post_agent_output = self._read_file(panes_dir / "post-agent.txt")
                task_result.post_test_output = self._read_file(panes_dir / "post-test.txt")
            
            # Parse commands and assign terminal output to episodes
            commands_file = task_dir / "commands.txt"
            if commands_file.exists() and task_result.post_agent_output:
                self._assign_terminal_output_to_episodes(task_result, commands_file)
            
            # Extract task definition and solution if available
            if self.tasks_base_dir:
                task_info = extract_task_info(task_result.task_id, self.tasks_base_dir)
                task_result.task_definition = task_info.task_definition
                task_result.official_solution = task_info.official_solution
                task_result.test_file_content = task_info.test_file_content
            
            return task_result
            
        except Exception as e:
            print(f"Error extracting task from {task_dir}: {e}")
            traceback.print_exc()
            return None
    
    def _extract_episode(self, episode_dir: Path, episode_num: int) -> Optional[EpisodeData]:
        """Extract data from a single episode (Hermes format: response.txt with JSON)."""
        try:
            prompt_file = episode_dir / "prompt.txt"
            response_file = episode_dir / "response.txt"  # Hermes uses response.txt
            
            prompt = self._read_file(prompt_file) if prompt_file.exists() else None
            
            response_data = None
            analysis = None
            plan = None
            commands = None
            
            if response_file.exists():
                response_text = self._read_file(response_file)
                try:
                    response_data = json.loads(response_text)
                    analysis = response_data.get("analysis")
                    plan = response_data.get("plan")
                    commands = response_data.get("commands", [])
                except json.JSONDecodeError:
                    # Response might not be JSON
                    pass
            
            return EpisodeData(
                episode_number=episode_num,
                prompt=prompt,
                response=response_data,
                analysis=analysis,
                plan=plan,
                commands=commands
            )
        except Exception as e:
            print(f"Error extracting episode {episode_num}: {e}")
            return None
    
    def _read_file(self, file_path: Path) -> Optional[str]:
        """Read file content safely."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return None
    
    def _assign_terminal_output_to_episodes(self, task: TaskResult, commands_file: Path):
        """Parse commands.txt and assign terminal output to episodes."""
        try:
            commands_content = self._read_file(commands_file)
            if not commands_content or not task.post_agent_output:
                return
            
            terminal_lines = task.post_agent_output.split('\n')
            
            current_line_idx = 0
            for episode in task.episodes:
                if not episode.commands or len(episode.commands) == 0:
                    continue
                
                episode_output_lines = []
                search_start = current_line_idx
                
                for cmd in episode.commands:
                    if isinstance(cmd, dict) and 'keystrokes' in cmd:
                        keystroke = cmd['keystrokes'].strip()
                        # Find this command in terminal output
                        for i in range(search_start, len(terminal_lines)):
                            if keystroke.replace('\\n', '').replace('\n', '') in terminal_lines[i]:
                                # Found command, collect output
                                j = i
                                while j < len(terminal_lines) and j < i + 50:  # Max 50 lines per command
                                    episode_output_lines.append(terminal_lines[j])
                                    j += 1
                                    # Break if we see next command or prompt
                                    if j < len(terminal_lines) and ('root@' in terminal_lines[j] or '>' in terminal_lines[j]):
                                        break
                                current_line_idx = j
                                search_start = j
                                break
                
                if episode_output_lines:
                    episode.terminal_output = '\n'.join(episode_output_lines)
            
        except Exception as e:
            print(f"Warning: Could not parse commands.txt: {e}")

