"""
OpenHands agent data extractor.

This extractor reads OpenHands trajectories from the `traj/openhands`
directory layout and converts them into the shared TaskResult/EpisodeData
models used by the analysis pipeline.

Compared to Terminus/Hermes/Miniswe:
- We only have a single session JSON file per task in `sessions/`.
- That JSON file is a list of events with different shapes.
- We normalize it into a compact sequence of action/observation pairs:
  - For each event with an `action` field (id >= 1), we keep only:
    - `id`
    - `args` (as-is)
  - For each event with an `observation` and `cause` field, we keep only:
    - `content`
    - `extras`
    and attach it to the action whose `id == cause`.
The normalized list is serialized as text and attached to a single
EpisodeData.terminal_output so it can be fed directly into the
`complete_trajectory` section of the analysis prompt.
"""

from __future__ import annotations

import json
import traceback
from pathlib import Path
from typing import List, Optional, Dict, Any

import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.models import TaskResult, EpisodeData  # type: ignore
from src.task_extractor import extract_task_info  # type: ignore


class OpenHandsDataExtractor:
    """Extract task data from an OpenHands run directory."""

    def __init__(self, run_dir: Path, tasks_base_dir: Optional[Path] = None):
        self.run_dir = run_dir
        self.tasks_base_dir = tasks_base_dir

    def find_task_directories(self) -> List[Path]:
        """
        Find all task directories in the run.

        OpenHands runs use the same high-level structure as other agents:
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
        """Extract a complete TaskResult from an OpenHands task directory."""
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

            # Attach normalized OpenHands trajectory as a single episode
            sessions_dir = task_dir / "sessions"
            normalized_traj = self._build_normalized_openhands_traj(sessions_dir)
            if normalized_traj:
                episode = EpisodeData(
                    episode_number=0,
                    prompt=None,
                    response=None,
                    analysis=None,
                    plan=None,
                    commands=None,
                    terminal_output=normalized_traj,
                )
                task_result.episodes = [episode]

            # Enrich with task definition and official solution if tasks_base_dir is given
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

    def _build_normalized_openhands_traj(self, sessions_dir: Path) -> Optional[str]:
        """
        Load the main OpenHands session JSON and normalize it into a compact
        sequence of action/observation pairs.
        """
        if not sessions_dir.exists():
            return None

        # Heuristic: pick the largest top-level JSON file in sessions_dir
        json_files = [
            p
            for p in sessions_dir.glob("*.json")
            if p.is_file()
        ]
        if not json_files:
            return None

        main_file = max(json_files, key=lambda p: p.stat().st_size)

        try:
            with open(main_file, "r", encoding="utf-8") as f:
                events = json.load(f)
        except Exception as e:
            print(f"Error reading OpenHands session JSON {main_file}: {e}")
            return None

        if not isinstance(events, list):
            return None

        actions: Dict[int, Dict[str, Any]] = {}
        observations: Dict[int, Dict[str, Any]] = {}

        for event in events:
            if not isinstance(event, dict):
                continue
            event_id = event.get("id")
            if event_id is None or not isinstance(event_id, int):
                continue
            if event_id == 0:
                # Skip system prompt
                continue

            # Action entries: have an "action" field
            if "action" in event:
                args = event.get("args", {})
                # Only keep id and args
                actions[event_id] = {
                    "id": event_id,
                    "args": args,
                }

            # Observation entries: have "observation" and "cause"
            if "observation" in event and "cause" in event:
                cause = event.get("cause")
                if not isinstance(cause, int):
                    continue
                # Only keep content and extras
                obs = {
                    "content": event.get("content"),
                    "extras": event.get("extras"),
                }
                # Prefer the first observation for a given cause
                observations.setdefault(cause, obs)

        if not actions:
            return None

        # Build sorted list of steps
        steps = []
        for action_id in sorted(actions.keys()):
            step: Dict[str, Any] = {
                "id": action_id,
                "args": actions[action_id]["args"],
            }
            obs = observations.get(action_id)
            if obs is not None:
                step["observation"] = obs
            steps.append(step)

        if not steps:
            return None

        # Serialize as JSON Lines (one compact JSON object per line)
        lines = [json.dumps(step, ensure_ascii=False) for step in steps]
        return "\n".join(lines)


