"""
Miniswe agent data extractor.

This extractor reads Miniswe C4 trajectories from the `traj/miniswe-c4`
directory layout and converts them into the shared TaskResult/EpisodeData
models used by the analysis pipeline.

Compared to Terminus/Hermes:
- The overall directory structure is the same.
- There is no per-episode JSON in `agent-logs/`.
- We therefore build a single aggregated episode per task using `post-agent.txt`
  (full trajectory) and optional commands parsed from `commands.txt`.
"""
import ast
import json
import traceback
from pathlib import Path
from typing import List, Optional

import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.models import TaskResult, EpisodeData  # type: ignore
from src.task_extractor import extract_task_info  # type: ignore


class MinisweDataExtractor:
    """Extract task data from a Miniswe C4 run directory."""

    def __init__(self, run_dir: Path, tasks_base_dir: Optional[Path] = None):
        self.run_dir = run_dir
        self.tasks_base_dir = tasks_base_dir

    def find_task_directories(self) -> List[Path]:
        """
        Find all task directories in the run.

        Miniswe runs use the same high-level structure as Hermes/Terminus:
        - run_dir/
          - task_id/
            - trial_name/
              - results.json
        or sometimes:
        - run_dir/
          - task_id/
            - results.json
        """
        task_dirs: List[Path] = []

        for item in self.run_dir.iterdir():
            if item.is_dir() and not item.name.startswith("."):
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
        """Extract a complete TaskResult from a Miniswe task directory."""
        try:
            results_file = task_dir / "results.json"
            if not results_file.exists():
                print(f"Warning: No results.json in {task_dir}")
                return None

            # Load results.json
            with open(results_file, "r", encoding="utf-8") as f:
                results_data = json.load(f)

            # Create TaskResult
            task_result = TaskResult(
                task_id=results_data.get("task_id", "unknown"),
                trial_name=results_data.get("trial_name", "unknown"),
                is_resolved=bool(results_data.get("is_resolved", False)),
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
                results_file=str(results_file),
            )

            # Panes output (pre/post agent & tests)
            panes_dir = task_dir / "panes"
            if panes_dir.exists():
                task_result.pre_agent_output = self._read_file(panes_dir / "pre-agent.txt")
                task_result.post_agent_output = self._read_file(panes_dir / "post-agent.txt")
                task_result.post_test_output = self._read_file(panes_dir / "post-test.txt")

            # Build a single episode from post-agent output and commands
            episode = self._build_single_episode(task_dir, task_result)
            if episode:
                task_result.episodes = [episode]

            # Enrich with task definition and official solution
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

    def _build_single_episode(self, task_dir: Path, task: TaskResult) -> Optional[EpisodeData]:
        """
        Build a single EpisodeData object for the whole run.

        Miniswe does not currently store per-episode JSON in agent-logs.
        We therefore:
        - parse commands directly from post-agent.txt bash code blocks
        - attach the full post-agent terminal output as the episode output
        """
        terminal_output = self._filter_terminal_output(task.post_agent_output)
        commands = self._extract_commands_from_post_agent(terminal_output)

        if not commands and not terminal_output:
            # Nothing useful to attach
            return None

        return EpisodeData(
            episode_number=0,
            prompt=None,
            response=None,
            analysis=None,
            plan=None,
            commands=commands or None,
            terminal_output=terminal_output,
        )

    def _extract_commands_from_post_agent(self, text: Optional[str]):
        """
        Extract commands from bash code blocks in post-agent.txt.

        We look for fenced blocks of the form:
        ```bash
        <commands...>
        ```
        and treat the entire block body as a single `keystrokes` string.
        """
        commands = []
        if not text:
            return commands

        in_block = False
        current_lines: list[str] = []

        for line in text.splitlines():
            stripped = line.strip()
            if not in_block and stripped.startswith("```bash"):
                in_block = True
                current_lines = []
                continue
            if in_block and stripped.startswith("```"):
                # End of current bash block
                cmd = "\n".join(current_lines).strip()
                if cmd and self._is_relevant_command_block(cmd):
                    commands.append({"keystrokes": cmd})
                in_block = False
                current_lines = []
                continue
            if in_block:
                current_lines.append(line)

        return commands

    def _filter_terminal_output(self, text: Optional[str]) -> Optional[str]:
        """
        Filter raw post-agent output to remove early setup/download noise.

        We keep only the portion starting from the first Miniswe step header,
        which looks like: \"mini-swe-agent (step N, ...)\".
        """
        if not text:
            return text

        marker = "mini-swe-agent (step"
        idx = text.find(marker)
        if idx != -1:
            return text[idx:]
        return text

    def _is_relevant_command_block(self, text: str) -> bool:
        """
        Heuristic filter for which bash blocks to treat as commands.

        Miniswe trajectories may contain generic shell examples; for analysis
        we only want blocks that are directly related to the task interaction,
        such as running the maze game, exploration scripts, or map creation.
        """
        keywords = [
            "maze_game.sh",
            "maze_explorer.py",
            "explore_maze.sh",
            "systematic_mapper.py",
            "maze_map.txt",
            "/protected/maze_helper.py",
        ]
        return any(k in text for k in keywords)

    def _read_file(self, file_path: Path) -> Optional[str]:
        """Read file content safely."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return None


