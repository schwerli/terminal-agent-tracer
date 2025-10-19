#!/usr/bin/env python3
"""
Terminal Agent Failure Analysis Script

Analyzes failed tasks from Hermes terminal agent runs on Terminal Bench,
using LLM APIs to provide detailed failure analysis.
"""
import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import traceback

from models import (
    TaskResult, EpisodeData, AnalysisResult, 
    AnalysisReport, LLMAnalysis
)
from llm_providers import get_provider, LLMProvider
from config import (
    ANALYSIS_PROMPT_TEMPLATE, 
    MAX_EPISODES_TO_INCLUDE,
    MAX_TERMINAL_OUTPUT_CHARS,
    MAX_INITIAL_PROMPT_CHARS,
    TRUNCATION_MESSAGE,
    RATE_LIMIT_DELAY
)


class DataExtractor:
    """Extract task data from run directory."""
    
    def __init__(self, run_dir: Path, tasks_base_dir: Optional[Path] = None):
        self.run_dir = run_dir
        # Try to find tasks directory
        if tasks_base_dir:
            self.tasks_base_dir = tasks_base_dir
        else:
            # Try to find it relative to common locations
            candidates = [
                Path("/data/terminalbench/terminal-bench/tasks"),
                Path("../terminal-bench/tasks"),
                Path("./terminal-bench/tasks"),
            ]
            self.tasks_base_dir = None
            for candidate in candidates:
                if candidate.exists():
                    self.tasks_base_dir = candidate
                    break
    
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
                self._extract_task_definition_and_solution(task_result)
            
            return task_result
            
        except Exception as e:
            print(f"Error extracting task from {task_dir}: {e}")
            traceback.print_exc()
            return None
    
    def _extract_episode(self, episode_dir: Path, episode_num: int) -> Optional[EpisodeData]:
        """Extract data from a single episode."""
        try:
            prompt_file = episode_dir / "prompt.txt"
            response_file = episode_dir / "response.txt"
            
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
            import ast
            commands_content = self._read_file(commands_file)
            if not commands_content or not task.post_agent_output:
                return
            
            # Parse commands.txt - it contains Python list/string representations
            lines = commands_content.strip().split('\n')
            
            # Split terminal output by episodes based on command count
            # The terminal output shows commands executed in sequence
            terminal_lines = task.post_agent_output.split('\n')
            
            current_line_idx = 0
            for episode in task.episodes:
                if not episode.commands or len(episode.commands) == 0:
                    continue
                
                # Collect terminal output for this episode's commands
                episode_output_lines = []
                commands_count = len(episode.commands)
                
                # Try to extract corresponding output from terminal
                # This is a heuristic - collect output until we see the next command prompt or reasonable break
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
            # If parsing fails, just skip terminal output assignment
    
    def _extract_task_definition_and_solution(self, task: TaskResult):
        """Extract task definition and official solution from tasks directory."""
        try:
            if not self.tasks_base_dir:
                return
            
            task_dir = self.tasks_base_dir / task.task_id
            if not task_dir.exists():
                return
            
            # Extract task.yaml
            task_yaml = task_dir / "task.yaml"
            if task_yaml.exists():
                task.task_definition = self._read_file(task_yaml)
            
            # Extract solution.sh
            solution_file = task_dir / "solution.sh"
            if solution_file.exists():
                task.official_solution = self._read_file(solution_file)
            
            # Extract test files
            tests_dir = task_dir / "tests"
            if tests_dir.exists():
                test_files = []
                for test_file in tests_dir.glob("*.py"):
                    content = self._read_file(test_file)
                    if content:
                        test_files.append(f"=== {test_file.name} ===\n{content}")
                if test_files:
                    task.test_file_content = "\n\n".join(test_files)
        
        except Exception as e:
            print(f"Warning: Could not extract task definition/solution: {e}")


class AnalysisPromptBuilder:
    """Build analysis prompts for LLM."""
    
    def __init__(self, max_episodes: int = MAX_EPISODES_TO_INCLUDE):
        self.max_episodes = max_episodes
    
    def build_prompt(self, task: TaskResult) -> str:
        """Build analysis prompt from task data."""
        # Format test results
        test_results = self._format_test_results(task.parser_results)
        
        # Format test files
        test_files = self._format_test_files(task)
        
        # Format official solution
        official_solution = self._format_official_solution(task)
        
        # Get initial prompt (episode 0)
        initial_prompt = self._format_initial_prompt(task)
        
        # Get complete trajectory (all episodes with terminal output merged)
        complete_trajectory = self._format_complete_trajectory(task)
        
        # Build prompt
        prompt = ANALYSIS_PROMPT_TEMPLATE.format(
            task_id=task.task_id,
            instruction=task.instruction[:2000],  # Limit instruction length
            test_results=test_results,
            test_files=test_files,
            official_solution=official_solution,
            initial_prompt=initial_prompt,
            complete_trajectory=complete_trajectory
        )
        
        return prompt
    
    def _format_test_results(self, parser_results: Dict[str, str]) -> str:
        """Format test results for prompt."""
        if not parser_results:
            return "No test results available."
        
        lines = []
        for test_name, result in parser_results.items():
            status = "✓ PASSED" if result == "passed" else "✗ FAILED"
            lines.append(f"- {test_name}: {status}")
        
        return "\n".join(lines)
    
    def _format_test_files(self, task: TaskResult) -> str:
        """Format test files for prompt."""
        if not task.test_file_content:
            return "No test files available."
        
        # Limit test file content to avoid huge prompts
        content = task.test_file_content
        max_chars = 3000
        if len(content) > max_chars:
            content = content[:max_chars] + "\n... [TEST FILES TRUNCATED] ..."
        
        return content
    
    def _format_official_solution(self, task: TaskResult) -> str:
        """Format official solution for prompt."""
        if not task.official_solution:
            return "No official solution available."
        
        # Limit solution length
        solution = task.official_solution
        max_chars = 5000
        if len(solution) > max_chars:
            solution = solution[:max_chars] + "\n... [SOLUTION TRUNCATED] ..."
        
        return solution
    
    def _format_initial_prompt(self, task: TaskResult) -> str:
        """Format initial prompt (episode 0)."""
        if not task.episodes or len(task.episodes) == 0:
            return "No episode data available."
        
        episode = task.episodes[0]
        if episode.prompt:
            # Limit prompt length to avoid too long context
            prompt_text = episode.prompt
            if len(prompt_text) > MAX_INITIAL_PROMPT_CHARS:
                prompt_text = prompt_text[:MAX_INITIAL_PROMPT_CHARS] + "\n... [PROMPT TRUNCATED] ..."
            return prompt_text
        
        return "No initial prompt available."
    
    def _format_complete_trajectory(self, task: TaskResult) -> str:
        """Format complete agent thinking and execution trajectory."""
        if not task.episodes:
            return "No episodes available."
        
        lines = []
        
        for ep in task.episodes:
            lines.append("---")  # Separator between episodes
            
            if ep.analysis:
                lines.append(f"**Analysis:** {ep.analysis}")
            
            if ep.plan:
                lines.append(f"**Plan:** {ep.plan}")
            
            if ep.commands:
                lines.append(f"**Commands:**")
                # Show all commands
                for i, cmd in enumerate(ep.commands, 1):
                    if isinstance(cmd, dict) and 'keystrokes' in cmd:
                        keystrokes = cmd['keystrokes'].replace('\n', '\\n')
                        lines.append(f"{i}. {keystrokes}")
            
            # Add terminal output if available
            if ep.terminal_output and ep.terminal_output.strip():
                lines.append(f"\n**Terminal Output:**")
                lines.append(ep.terminal_output.strip())
            
            lines.append("")  # Empty line
        
        return "\n".join(lines)
    


class FailureAnalyzer:
    """Main failure analyzer."""
    
    def __init__(self, provider: LLMProvider, concurrency: int = 1):
        self.provider = provider
        self.concurrency = concurrency
        self.prompt_builder = AnalysisPromptBuilder()
    
    async def analyze_task_async(self, task: TaskResult) -> AnalysisResult:
        """Analyze a single task asynchronously."""
        try:
            # Build prompt
            prompt = self.prompt_builder.build_prompt(task)
            
            # Get analysis from LLM
            response = await self.provider.analyze(prompt)
            
            # Parse response
            llm_analysis = self._parse_llm_response(response)
            
            return AnalysisResult(
                task_id=task.task_id,
                is_resolved=task.is_resolved,
                llm_analysis=llm_analysis,
                metadata={
                    "trial_name": task.trial_name,
                    "failure_mode": task.failure_mode,
                    "total_episodes": len(task.episodes),
                    "total_input_tokens": task.total_input_tokens,
                    "total_output_tokens": task.total_output_tokens
                }
            )
        except Exception as e:
            print(f"Error analyzing task {task.task_id}: {e}")
            return AnalysisResult(
                task_id=task.task_id,
                is_resolved=task.is_resolved,
                error=str(e),
                metadata={"trial_name": task.trial_name}
            )
    
    def analyze_task_sync(self, task: TaskResult) -> AnalysisResult:
        """Analyze a single task synchronously."""
        try:
            # Build prompt
            prompt = self.prompt_builder.build_prompt(task)
            
            # Get analysis from LLM
            response = self.provider.analyze_sync(prompt)
            
            # Parse response
            llm_analysis = self._parse_llm_response(response)
            
            return AnalysisResult(
                task_id=task.task_id,
                is_resolved=task.is_resolved,
                llm_analysis=llm_analysis,
                metadata={
                    "trial_name": task.trial_name,
                    "failure_mode": task.failure_mode,
                    "total_episodes": len(task.episodes),
                    "total_input_tokens": task.total_input_tokens,
                    "total_output_tokens": task.total_output_tokens
                }
            )
        except Exception as e:
            print(f"Error analyzing task {task.task_id}: {e}")
            return AnalysisResult(
                task_id=task.task_id,
                is_resolved=task.is_resolved,
                error=str(e),
                metadata={"trial_name": task.trial_name}
            )
    
    def _parse_llm_response(self, response: str) -> LLMAnalysis:
        """Parse LLM response into structured format."""
        try:
            # Try to extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                data = json.loads(json_str)
                
                return LLMAnalysis(
                    root_cause=data.get("root_cause", ""),
                    agent_mistakes=data.get("agent_mistakes", []),
                    analysis_summary=data.get("analysis_summary", ""),
                    raw_response=response
                )
            else:
                # Fallback: use entire response as summary
                return LLMAnalysis(
                    root_cause="Could not parse structured response",
                    agent_mistakes=[],
                    analysis_summary=response,
                    raw_response=response
                )
        except Exception as e:
            print(f"Error parsing LLM response: {e}")
            return LLMAnalysis(
                root_cause="Error parsing response",
                agent_mistakes=[],
                analysis_summary=response,
                raw_response=response
            )
    
    async def analyze_tasks_async(self, tasks: List[TaskResult]) -> List[AnalysisResult]:
        """Analyze multiple tasks with concurrency control."""
        semaphore = asyncio.Semaphore(self.concurrency)
        
        async def analyze_with_semaphore(task: TaskResult) -> AnalysisResult:
            async with semaphore:
                result = await self.analyze_task_async(task)
                await asyncio.sleep(RATE_LIMIT_DELAY)
                return result
        
        tasks_to_analyze = [task for task in tasks if not task.is_resolved]
        print(f"Analyzing {len(tasks_to_analyze)} failed tasks...")
        
        results = await asyncio.gather(*[analyze_with_semaphore(task) for task in tasks_to_analyze])
        return results
    
    def analyze_tasks_sync(self, tasks: List[TaskResult]) -> List[AnalysisResult]:
        """Analyze multiple tasks synchronously or with thread pool."""
        tasks_to_analyze = [task for task in tasks if not task.is_resolved]
        print(f"Analyzing {len(tasks_to_analyze)} failed tasks...")
        
        if self.concurrency == 1:
            # Sequential processing
            results = []
            for i, task in enumerate(tasks_to_analyze):
                print(f"Analyzing task {i+1}/{len(tasks_to_analyze)}: {task.task_id}")
                result = self.analyze_task_sync(task)
                results.append(result)
            return results
        else:
            # Parallel processing with thread pool
            with ThreadPoolExecutor(max_workers=self.concurrency) as executor:
                results = list(executor.map(self.analyze_task_sync, tasks_to_analyze))
            return results


class OutputGenerator:
    """Generate output files."""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_jsonl(self, report: AnalysisReport, filename: str = "analysis_results.jsonl"):
        """Generate JSONL output file (one JSON per line)."""
        output_file = self.output_dir / filename
        with open(output_file, 'w') as f:
            # Write metadata line
            metadata = {
                "run_id": report.run_id,
                "analyzed_at": report.analyzed_at,
                "model_provider": report.model_provider,
                "model_name": report.model_name,
                "tasks_analyzed": report.tasks_analyzed,
                "tasks_resolved": report.tasks_resolved,
                "tasks_failed": report.tasks_failed
            }
            f.write(json.dumps(metadata) + '\n')
            
            # Write each analysis result as a separate line
            for result in report.results:
                if not result.is_resolved:  # Only write failed tasks
                    f.write(json.dumps(result.to_dict()) + '\n')
        print(f"JSONL report saved to: {output_file}")
    
    def generate_markdown(self, report: AnalysisReport, filename: str = "analysis_report.md"):
        """Generate Markdown report."""
        output_file = self.output_dir / filename
        
        with open(output_file, 'w') as f:
            # Header
            f.write(f"# Terminal Agent Failure Analysis Report\n\n")
            f.write(f"**Run ID:** {report.run_id}\n")
            f.write(f"**Analysis Date:** {report.analyzed_at}\n")
            f.write(f"**Model:** {report.model_provider}/{report.model_name}\n\n")
            
            # Summary
            f.write(f"## Summary\n\n")
            f.write(f"- **Total Tasks:** {report.tasks_analyzed}\n")
            f.write(f"- **Resolved:** {report.tasks_resolved}\n")
            f.write(f"- **Failed:** {report.tasks_failed}\n")
            f.write(f"- **Success Rate:** {report.tasks_resolved / report.tasks_analyzed * 100:.1f}%\n\n")
            
            # Failed tasks
            f.write(f"## Failed Tasks Analysis\n\n")
            
            failed_results = [r for r in report.results if not r.is_resolved]
            
            for i, result in enumerate(failed_results, 1):
                f.write(f"### {i}. {result.task_id}\n\n")
                
                if result.error:
                    f.write(f"**Error:** {result.error}\n\n")
                    continue
                
                if result.llm_analysis:
                    analysis = result.llm_analysis
                    
                    f.write(f"**Root Cause:**\n{analysis.root_cause}\n\n")
                    
                    if analysis.agent_mistakes:
                        f.write(f"**Agent Mistakes:**\n")
                        for mistake in analysis.agent_mistakes:
                            f.write(f"- {mistake}\n")
                        f.write("\n")
                    
                    if analysis.analysis_summary:
                        f.write(f"**Analysis Summary:**\n{analysis.analysis_summary}\n\n")
                
                f.write("---\n\n")
        
        print(f"Markdown report saved to: {output_file}")


async def main_async(args):
    """Main async execution."""
    run_dir = Path(args.run_dir)
    
    if not run_dir.exists():
        print(f"Error: Run directory not found: {run_dir}")
        sys.exit(1)
    
    # Extract data
    print(f"Extracting data from: {run_dir}")
    extractor = DataExtractor(run_dir)
    task_dirs = extractor.find_task_directories()
    print(f"Found {len(task_dirs)} task directories")
    
    tasks = []
    for task_dir in task_dirs:
        task_result = extractor.extract_task_result(task_dir)
        if task_result:
            tasks.append(task_result)
    
    print(f"Successfully extracted {len(tasks)} tasks")
    resolved_count = sum(1 for t in tasks if t.is_resolved)
    failed_count = len(tasks) - resolved_count
    print(f"- Resolved: {resolved_count}")
    print(f"- Failed: {failed_count}")
    
    if failed_count == 0:
        print("No failed tasks to analyze!")
        return
    
    # Initialize LLM provider
    provider = get_provider(
        args.model_provider,
        args.model_name,
        args.api_key,
        args.base_url
    )
    
    # Analyze failures
    analyzer = FailureAnalyzer(provider, args.concurrency)
    analysis_results = await analyzer.analyze_tasks_async(tasks)
    
    # Create report
    report = AnalysisReport(
        run_id=run_dir.name,
        analyzed_at=datetime.now().isoformat(),
        model_provider=args.model_provider,
        model_name=args.model_name,
        tasks_analyzed=len(tasks),
        tasks_resolved=resolved_count,
        tasks_failed=failed_count,
        results=analysis_results
    )
    
    # Generate outputs
    output_dir = Path(args.output_dir)
    generator = OutputGenerator(output_dir)
    generator.generate_jsonl(report)
    generator.generate_markdown(report)
    
    print(f"\nAnalysis complete!")


def main_sync(args):
    """Main synchronous execution."""
    run_dir = Path(args.run_dir)
    
    if not run_dir.exists():
        print(f"Error: Run directory not found: {run_dir}")
        sys.exit(1)
    
    # Extract data
    print(f"Extracting data from: {run_dir}")
    tasks_base_dir = Path(args.tasks_dir) if args.tasks_dir else None
    extractor = DataExtractor(run_dir, tasks_base_dir)
    
    if extractor.tasks_base_dir:
        print(f"Using tasks directory: {extractor.tasks_base_dir}")
    else:
        print("Warning: Could not find terminal-bench tasks directory. Test files and solutions will not be included.")
    
    task_dirs = extractor.find_task_directories()
    print(f"Found {len(task_dirs)} task directories")
    
    tasks = []
    for task_dir in task_dirs:
        task_result = extractor.extract_task_result(task_dir)
        if task_result:
            tasks.append(task_result)
    
    print(f"Successfully extracted {len(tasks)} tasks")
    resolved_count = sum(1 for t in tasks if t.is_resolved)
    failed_count = len(tasks) - resolved_count
    print(f"- Resolved: {resolved_count}")
    print(f"- Failed: {failed_count}")
    
    if failed_count == 0:
        print("No failed tasks to analyze!")
        return
    
    # Initialize LLM provider
    provider = get_provider(
        args.model_provider,
        args.model_name,
        args.api_key,
        args.base_url
    )
    
    # Analyze failures
    analyzer = FailureAnalyzer(provider, args.concurrency)
    analysis_results = analyzer.analyze_tasks_sync(tasks)
    
    # Create report
    report = AnalysisReport(
        run_id=run_dir.name,
        analyzed_at=datetime.now().isoformat(),
        model_provider=args.model_provider,
        model_name=args.model_name,
        tasks_analyzed=len(tasks),
        tasks_resolved=resolved_count,
        tasks_failed=failed_count,
        results=analysis_results
    )
    
    # Generate outputs
    output_dir = Path(args.output_dir)
    generator = OutputGenerator(output_dir)
    generator.generate_jsonl(report)
    generator.generate_markdown(report)
    
    print(f"\nAnalysis complete!")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze terminal agent failures using LLM APIs"
    )
    
    parser.add_argument(
        "--run-dir",
        required=True,
        help="Path to run directory (e.g., terminal-bench0/runs/2025-09-16__00-48-15/)"
    )
    
    parser.add_argument(
        "--model-provider",
        required=True,
        choices=["openai", "anthropic", "custom"],
        help="LLM provider to use"
    )
    
    parser.add_argument(
        "--model-name",
        required=True,
        help="Model name (e.g., gpt-4, claude-3-opus-20240229)"
    )
    
    parser.add_argument(
        "--api-key",
        help="API key (or use environment variable)"
    )
    
    parser.add_argument(
        "--base-url",
        help="Base URL for custom API provider"
    )
    
    parser.add_argument(
        "--concurrency",
        type=int,
        default=1,
        help="Number of parallel API requests (default: 1 for sequential)"
    )
    
    parser.add_argument(
        "--output-dir",
        default="./analysis_output",
        help="Output directory for results (default: ./analysis_output)"
    )
    
    parser.add_argument(
        "--max-episodes",
        type=int,
        default=MAX_EPISODES_TO_INCLUDE,
        help=f"Maximum episodes to include in analysis (default: {MAX_EPISODES_TO_INCLUDE})"
    )
    
    parser.add_argument(
        "--tasks-dir",
        help="Path to terminal-bench tasks directory (e.g., /path/to/terminal-bench/tasks). If not provided, will search common locations."
    )
    
    parser.add_argument(
        "--async-mode",
        action="store_true",
        help="Use async mode (default: sync mode)"
    )
    
    args = parser.parse_args()
    
    # Update max episodes if specified
    if args.max_episodes != MAX_EPISODES_TO_INCLUDE:
        import config
        config.MAX_EPISODES_TO_INCLUDE = args.max_episodes
    
    try:
        if args.async_mode:
            asyncio.run(main_async(args))
        else:
            main_sync(args)
    except KeyboardInterrupt:
        print("\nAnalysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

