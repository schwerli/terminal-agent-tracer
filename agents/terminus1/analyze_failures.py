#!/usr/bin/env python3
"""
Terminus (C4) Agent Failure Analysis Script

Analyzes failed tasks from Terminus (C4) terminal agent runs on Terminal Bench,
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

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.models import TaskResult, AnalysisResult, LLMAnalysis
from src.llm_providers import get_provider, LLMProvider
from src.config import (
    ANALYSIS_PROMPT_TEMPLATE,
    ERROR_CATEGORIES,
    MAX_EPISODES_TO_INCLUDE,
    MAX_TERMINAL_OUTPUT_CHARS,
    MAX_INITIAL_PROMPT_CHARS,
    TRUNCATION_MESSAGE,
    RATE_LIMIT_DELAY
)
from src.output_generator import StreamingOutputGenerator
from data_extractor import TerminusDataExtractor


class AnalysisPromptBuilder:
    """Build analysis prompts for LLM."""
    
    def __init__(self, max_episodes: int = MAX_EPISODES_TO_INCLUDE):
        self.max_episodes = max_episodes
    
    def build_prompt(self, task: TaskResult) -> str:
        """Build analysis prompt from task data."""
        test_results = self._format_test_results(task.parser_results)
        test_files = self._format_test_files(task)
        official_solution = self._format_official_solution(task)
        initial_prompt = self._format_initial_prompt(task)
        complete_trajectory = self._format_complete_trajectory(task)
        error_categories_text = "\n".join([f"- {cat}" for cat in ERROR_CATEGORIES])
        
        prompt = ANALYSIS_PROMPT_TEMPLATE.format(
            task_id=task.task_id,
            instruction=task.instruction[:2000],
            test_results=test_results,
            test_files=test_files,
            official_solution=official_solution,
            initial_prompt=initial_prompt,
            complete_trajectory=complete_trajectory,
            error_categories=error_categories_text
        )
        
        return prompt
    
    def _format_test_results(self, parser_results: Dict[str, str]) -> str:
        if not parser_results:
            return "No test results available."
        lines = []
        for test_name, result in parser_results.items():
            status = "✓ PASSED" if result == "passed" else "✗ FAILED"
            lines.append(f"- {test_name}: {status}")
        return "\n".join(lines)
    
    def _format_test_files(self, task: TaskResult) -> str:
        if not task.test_file_content:
            return "No test files available."
        content = task.test_file_content
        max_chars = 3000
        if len(content) > max_chars:
            content = content[:max_chars] + "\n... [TEST FILES TRUNCATED] ..."
        return content
    
    def _format_official_solution(self, task: TaskResult) -> str:
        if not task.official_solution:
            return "No official solution available."
        solution = task.official_solution
        max_chars = 5000
        if len(solution) > max_chars:
            solution = solution[:max_chars] + "\n... [SOLUTION TRUNCATED] ..."
        return solution
    
    def _format_initial_prompt(self, task: TaskResult) -> str:
        if not task.episodes or len(task.episodes) == 0:
            return "No episode data available."
        episode = task.episodes[0]
        if episode.prompt:
            prompt_text = episode.prompt
            if len(prompt_text) > MAX_INITIAL_PROMPT_CHARS:
                prompt_text = prompt_text[:MAX_INITIAL_PROMPT_CHARS] + "\n... [PROMPT TRUNCATED] ..."
            return prompt_text
        return "No initial prompt available."
    
    def _format_complete_trajectory(self, task: TaskResult) -> str:
        if not task.episodes:
            return "No episodes available."
        lines = []
        for ep in task.episodes:
            lines.append("---")
            if ep.analysis:
                lines.append(f"**Analysis:** {ep.analysis}")
            if ep.plan:
                lines.append(f"**Plan:** {ep.plan}")
            if ep.commands:
                lines.append(f"**Commands:**")
                for i, cmd in enumerate(ep.commands, 1):
                    if isinstance(cmd, dict) and 'keystrokes' in cmd:
                        keystrokes = cmd['keystrokes'].replace('\n', '\\n')
                        lines.append(f"{i}. {keystrokes}")
            if ep.terminal_output and ep.terminal_output.strip():
                lines.append(f"\n**Terminal Output:**")
                lines.append(ep.terminal_output.strip())
            lines.append("")
        return "\n".join(lines)


class FailureAnalyzer:
    """Main failure analyzer."""
    
    def __init__(self, provider: LLMProvider, output_generator: StreamingOutputGenerator, concurrency: int = 1):
        self.provider = provider
        self.output_generator = output_generator
        self.concurrency = concurrency
        self.prompt_builder = AnalysisPromptBuilder()
    
    def analyze_task_sync(self, task: TaskResult) -> AnalysisResult:
        """Analyze a single task synchronously."""
        try:
            prompt = self.prompt_builder.build_prompt(task)
            response = self.provider.analyze_sync(prompt)
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
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                data = json.loads(json_str)
                
                llm_analysis = LLMAnalysis(
                    earliest_error_command=data.get("earliest_error_command"),
                    error_category=data.get("error_category"),
                    new_category_created=data.get("new_category_created"),
                    root_cause=data.get("root_cause", ""),
                    agent_mistakes=data.get("agent_mistakes", []),
                    analysis_summary=data.get("analysis_summary", ""),
                    raw_response=response
                )
                
                # Add new category to global list if created
                if llm_analysis.new_category_created:
                    import src.config
                    if llm_analysis.new_category_created not in src.config.ERROR_CATEGORIES:
                        src.config.ERROR_CATEGORIES.append(llm_analysis.new_category_created)
                        print(f"New error category added: {llm_analysis.new_category_created}")
                
                return llm_analysis
            else:
                return LLMAnalysis(
                    earliest_error_command=None,
                    error_category="parse_error",
                    new_category_created=None,
                    root_cause="Could not parse structured response",
                    agent_mistakes=[],
                    analysis_summary=response,
                    raw_response=response
                )
        except Exception as e:
            print(f"Error parsing LLM response: {e}")
            return LLMAnalysis(
                earliest_error_command=None,
                error_category="parse_error",
                new_category_created=None,
                root_cause="Error parsing response",
                agent_mistakes=[],
                analysis_summary=response,
                raw_response=response
            )
    
    def analyze_tasks_sync(self, tasks: List[TaskResult]):
        """Analyze multiple tasks synchronously with streaming output."""
        tasks_to_analyze = [task for task in tasks if not task.is_resolved]
        print(f"Analyzing {len(tasks_to_analyze)} failed tasks...")
        
        for i, task in enumerate(tasks_to_analyze):
            print(f"Analyzing task {i+1}/{len(tasks_to_analyze)}: {task.task_id}")
            result = self.analyze_task_sync(task)
            self.output_generator.append_result(result)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze Terminus (C4) agent failures using LLM APIs"
    )
    
    parser.add_argument("--run-dir", required=True, help="Path to run directory")
    parser.add_argument("--tasks-dir", required=True, help="Path to terminal-bench tasks directory")
    parser.add_argument("--model-provider", required=True, choices=["openai", "anthropic", "custom"], help="LLM provider")
    parser.add_argument("--model-name", required=True, help="Model name")
    parser.add_argument("--api-key", help="API key (or use environment variable)")
    parser.add_argument("--base-url", help="Base URL for custom API provider")
    parser.add_argument("--concurrency", type=int, default=1, help="Number of parallel API requests (default: 1)")
    parser.add_argument("--output-dir", default="./analysis_output", help="Output directory (default: ./analysis_output)")
    
    args = parser.parse_args()
    
    run_dir = Path(args.run_dir)
    tasks_dir = Path(args.tasks_dir)
    
    if not run_dir.exists():
        print(f"Error: Run directory not found: {run_dir}")
        sys.exit(1)
    
    if not tasks_dir.exists():
        print(f"Error: Tasks directory not found: {tasks_dir}")
        sys.exit(1)
    
    # Extract data
    print(f"Extracting data from: {run_dir}")
    print(f"Using tasks directory: {tasks_dir}")
    extractor = TerminusDataExtractor(run_dir, tasks_dir)
    
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
    provider = get_provider(args.model_provider, args.model_name, args.api_key, args.base_url)
    
    # Initialize streaming output generator
    output_dir = Path(args.output_dir)
    output_generator = StreamingOutputGenerator(
        output_dir=output_dir,
        run_id=run_dir.name,
        model_provider=args.model_provider,
        model_name=args.model_name
    )
    
    # Analyze failures with streaming output
    analyzer = FailureAnalyzer(provider, output_generator, args.concurrency)
    analyzer.analyze_tasks_sync(tasks)
    
    # Finalize output
    output_generator.finalize()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nAnalysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
        sys.exit(1)

