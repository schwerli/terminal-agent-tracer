"""
Streaming output generator for analysis results.
"""
import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from .models import AnalysisResult, AnalysisReport


class StreamingOutputGenerator:
    """Generate output files with streaming support."""
    
    def __init__(self, output_dir: Path, run_id: str, model_provider: str, model_name: str):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.run_id = run_id
        self.model_provider = model_provider
        self.model_name = model_name
        self.analyzed_at = datetime.now().isoformat()
        
        self.jsonl_file = output_dir / "analysis_results.jsonl"
        self.md_file = output_dir / "analysis_report.md"
        
        self.tasks_analyzed = 0
        self.tasks_resolved = 0
        self.tasks_failed = 0
        self.results = []
        
        # Initialize JSONL file with metadata
        self._initialize_jsonl()
    
    def _initialize_jsonl(self):
        """Initialize JSONL file with metadata line."""
        metadata = {
            "run_id": self.run_id,
            "analyzed_at": self.analyzed_at,
            "model_provider": self.model_provider,
            "model_name": self.model_name,
        }
        with open(self.jsonl_file, 'w') as f:
            f.write(json.dumps(metadata) + '\n')
        
        print(f"Initialized JSONL output: {self.jsonl_file}")
        
        # Initialize Markdown file with header
        self._initialize_markdown()
    
    def append_result(self, result: AnalysisResult):
        """Append a single analysis result immediately to JSONL and print summary."""
        self.results.append(result)
        
        # Update counters
        self.tasks_analyzed += 1
        if result.is_resolved:
            self.tasks_resolved += 1
        else:
            self.tasks_failed += 1
        
        # Write only failed tasks to JSONL
        if not result.is_resolved:
            with open(self.jsonl_file, 'a') as f:
                f.write(json.dumps(result.to_dict()) + '\n')
            print(f"  -> Appended to JSONL: {result.task_id}")
            
            # Print immediate analysis summary
            self._print_task_summary(result)
            
            # Append to Markdown file immediately
            self._append_task_to_markdown(result)
    
    def finalize(self):
        """Finalize the analysis by updating summary statistics."""
        # Update summary section in Markdown
        self._update_markdown_summary()
        
        # Update metadata in JSONL (append final stats)
        final_metadata = {
            "final_stats": {
                "tasks_analyzed": self.tasks_analyzed,
                "tasks_resolved": self.tasks_resolved,
                "tasks_failed": self.tasks_failed
            }
        }
        with open(self.jsonl_file, 'a') as f:
            f.write(json.dumps(final_metadata) + '\n')
        
        print(f"\nAnalysis complete!")
        print(f"  JSONL: {self.jsonl_file}")
        print(f"  Markdown: {self.md_file}")
    
    def _print_task_summary(self, result: AnalysisResult):
        """Print immediate summary for a single task analysis."""
        print("\n" + "="*80)
        print(f"TASK: {result.task_id}")
        print("="*80)
        
        if result.error:
            print(f"ERROR: {result.error}")
            print("="*80 + "\n")
            return
        
        if result.llm_analysis:
            analysis = result.llm_analysis
            print(f"Error Category: {analysis.error_category or 'Unknown'}")
            if analysis.error_subcategory:
                print(f"Error Subcategory: {analysis.error_subcategory}")
            if analysis.error_description:
                print(f"Error Description: {analysis.error_description}")
            print(f"\nRoot Cause:\n{analysis.root_cause}")
            if analysis.analysis:
                print(f"\nAnalysis:\n{analysis.analysis}")
        
        print("="*80 + "\n")
    
    def _initialize_markdown(self):
        """Initialize Markdown file with header and summary placeholder."""
        with open(self.md_file, 'w') as f:
            # Header
            f.write(f"# Terminal Agent Failure Analysis Report\n\n")
            f.write(f"**Run ID:** {self.run_id}\n")
            f.write(f"**Analysis Date:** {self.analyzed_at}\n")
            f.write(f"**Model:** {self.model_provider}/{self.model_name}\n\n")
            
            # Summary placeholder (will be updated in finalize)
            f.write(f"## Summary\n\n")
            f.write(f"- **Total Tasks:** 0\n")
            f.write(f"- **Resolved:** 0\n")
            f.write(f"- **Failed:** 0\n")
            f.write(f"- **Success Rate:** 0.0%\n\n")
            
            # Failed tasks section header
            f.write(f"## Failed Tasks Analysis\n\n")
        
        print(f"Initialized Markdown output: {self.md_file}")
    
    def _append_task_to_markdown(self, result: AnalysisResult):
        """Append a single task analysis to Markdown file immediately."""
        with open(self.md_file, 'a') as f:
            # Count existing failed tasks to get the correct number
            failed_count = sum(1 for r in self.results if not r.is_resolved)
            
            f.write(f"### {failed_count}. {result.task_id}\n\n")
            
            if result.error:
                f.write(f"**Error:** {result.error}\n\n")
                f.write("---\n\n")
                return
            
            if result.llm_analysis:
                analysis = result.llm_analysis
                
                f.write(f"**Error Category:** {analysis.error_category or 'Unknown'}\n\n")
                
                if analysis.error_subcategory:
                    f.write(f"**Error Subcategory:** {analysis.error_subcategory}\n\n")
                
                if analysis.error_description:
                    f.write(f"**Error Description:** {analysis.error_description}\n\n")
                
                f.write(f"**Root Cause:**\n{analysis.root_cause}\n\n")
                
                if analysis.analysis:
                    f.write(f"**Analysis:**\n{analysis.analysis}\n\n")
            
            f.write("---\n\n")
    
    def _update_markdown_summary(self):
        """Update the summary section in Markdown file with final statistics."""
        # Read current content
        with open(self.md_file, 'r') as f:
            content = f.read()
        
        # Find and replace the summary section
        summary_start = content.find("## Summary\n\n")
        if summary_start == -1:
            return
        
        summary_end = content.find("## Failed Tasks Analysis\n\n", summary_start)
        if summary_end == -1:
            return
        
        # Build new summary
        new_summary = f"## Summary\n\n"
        new_summary += f"- **Total Tasks:** {self.tasks_analyzed}\n"
        new_summary += f"- **Resolved:** {self.tasks_resolved}\n"
        new_summary += f"- **Failed:** {self.tasks_failed}\n"
        if self.tasks_analyzed > 0:
            new_summary += f"- **Success Rate:** {self.tasks_resolved / self.tasks_analyzed * 100:.1f}%\n\n"
        else:
            new_summary += f"- **Success Rate:** 0.0%\n\n"
        
        # Replace summary section
        new_content = content[:summary_start] + new_summary + content[summary_end:]
        
        with open(self.md_file, 'w') as f:
            f.write(new_content)

