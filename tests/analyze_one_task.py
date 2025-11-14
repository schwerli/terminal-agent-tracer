#!/usr/bin/env python3
"""
Analyze a single task for testing purposes.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

def main():
    if len(sys.argv) < 7:
        print("Usage: python analyze_one_task.py <agent_type> <run_dir> <tasks_dir> <model_provider> <model_name> <api_key> [base_url]")
        print("Example: python analyze_one_task.py hermes /path/to/run /path/to/tasks custom app-xxx sk-xxx http://api.example.com/v1")
        print("Agent types: hermes, terminus")
        sys.exit(1)
    
    agent_type = sys.argv[1].lower()
    run_dir = Path(sys.argv[2])
    tasks_dir = Path(sys.argv[3])
    model_provider = sys.argv[4]
    model_name = sys.argv[5]
    api_key = sys.argv[6]
    base_url = sys.argv[7] if len(sys.argv) > 7 else None
    
    # Import appropriate extractor and analyzer
    if agent_type == "hermes":
        from agents.hermes.data_extractor import HermesDataExtractor as DataExtractor
        from agents.hermes.analyze_failures import FailureAnalyzer, AnalysisPromptBuilder
    elif agent_type == "terminus":
        from agents.terminus.data_extractor import TerminusDataExtractor as DataExtractor
        from agents.terminus.analyze_failures import FailureAnalyzer, AnalysisPromptBuilder
    else:
        print(f"Unknown agent type: {agent_type}")
        sys.exit(1)
    
    from src.llm_providers import get_provider
    from src.output_generator import StreamingOutputGenerator
    
    print(f"Extracting tasks from: {run_dir}")
    extractor = DataExtractor(run_dir, tasks_dir)
    
    task_dirs = extractor.find_task_directories()
    print(f"Found {len(task_dirs)} task directories\n")
    
    # Find first failed task
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
    print(f"Number of episodes: {len(failed_task.episodes)}")
    print(f"Test results: {failed_task.parser_results}\n")
    
    # Create provider
    print(f"Initializing LLM provider: {model_provider}/{model_name}")
    provider = get_provider(model_provider, model_name, api_key, base_url)
    
    # Create mock output generator (for single task test)
    output_dir = Path("./test_output")
    output_generator = StreamingOutputGenerator(
        output_dir=output_dir,
        run_id="test",
        model_provider=model_provider,
        model_name=model_name
    )
    
    # Analyze
    print("Sending analysis request to LLM...\n")
    analyzer = FailureAnalyzer(provider, output_generator, concurrency=1)
    result = analyzer.analyze_task_sync(failed_task)
    
    if result.error:
        print(f"Error: {result.error}")
    elif result.llm_analysis:
        print("="*80)
        print("ANALYSIS RESULT")
        print("="*80)
        print(f"\nTask: {result.task_id}")
        print(f"\nError Category: {result.llm_analysis.error_category}")
        if result.llm_analysis.earliest_error_command:
            print(f"\nEarliest Error Command:\n{result.llm_analysis.earliest_error_command}")
        print(f"\nRoot Cause:\n{result.llm_analysis.root_cause}")
        print(f"\nAgent Mistakes:")
        for i, mistake in enumerate(result.llm_analysis.agent_mistakes, 1):
            print(f"{i}. {mistake}")
        print(f"\nAnalysis Summary:\n{result.llm_analysis.analysis_summary}")
        print("="*80)
    else:
        print("No analysis returned")
    
    print("\nTest complete!")


if __name__ == "__main__":
    main()

