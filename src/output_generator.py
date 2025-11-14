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
    
    def append_result(self, result: AnalysisResult):
        """Append a single analysis result immediately to JSONL."""
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
    
    def finalize(self):
        """Generate final markdown report."""
        self._generate_markdown()
        
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
    
    def _generate_markdown(self):
        """Generate Markdown report."""
        with open(self.md_file, 'w') as f:
            # Header
            f.write(f"# Terminal Agent Failure Analysis Report\n\n")
            f.write(f"**Run ID:** {self.run_id}\n")
            f.write(f"**Analysis Date:** {self.analyzed_at}\n")
            f.write(f"**Model:** {self.model_provider}/{self.model_name}\n\n")
            
            # Summary
            f.write(f"## Summary\n\n")
            f.write(f"- **Total Tasks:** {self.tasks_analyzed}\n")
            f.write(f"- **Resolved:** {self.tasks_resolved}\n")
            f.write(f"- **Failed:** {self.tasks_failed}\n")
            if self.tasks_analyzed > 0:
                f.write(f"- **Success Rate:** {self.tasks_resolved / self.tasks_analyzed * 100:.1f}%\n\n")
            
            # Failed tasks
            f.write(f"## Failed Tasks Analysis\n\n")
            
            failed_results = [r for r in self.results if not r.is_resolved]
            
            for i, result in enumerate(failed_results, 1):
                f.write(f"### {i}. {result.task_id}\n\n")
                
                if result.error:
                    f.write(f"**Error:** {result.error}\n\n")
                    continue
                
                if result.llm_analysis:
                    analysis = result.llm_analysis
                    
                    f.write(f"**Error Category:** {analysis.error_category or 'Unknown'}\n\n")
                    
                    if analysis.new_category_created:
                        f.write(f"**New Category Created:** {analysis.new_category_created}\n\n")
                    
                    if analysis.earliest_error_command:
                        f.write(f"**Earliest Error Command:**\n```\n{analysis.earliest_error_command}\n```\n\n")
                    
                    f.write(f"**Root Cause:**\n{analysis.root_cause}\n\n")
                    
                    if analysis.agent_mistakes:
                        f.write(f"**Agent Mistakes:**\n")
                        for mistake in analysis.agent_mistakes:
                            f.write(f"- {mistake}\n")
                        f.write("\n")
                    
                    if analysis.analysis_summary:
                        f.write(f"**Analysis Summary:**\n{analysis.analysis_summary}\n\n")
                
                f.write("---\n\n")

