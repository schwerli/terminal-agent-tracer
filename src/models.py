"""
Data models for terminal agent failure analysis.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime


@dataclass
class EpisodeData:
    """Data from a single episode of agent execution."""
    episode_number: int
    prompt: Optional[str] = None
    response: Optional[Dict[str, Any]] = None
    analysis: Optional[str] = None
    plan: Optional[str] = None
    commands: Optional[List[Dict[str, Any]]] = None
    terminal_output: Optional[str] = None  # Terminal output for this episode's commands


@dataclass
class TaskResult:
    """Complete result data for a single task."""
    task_id: str
    trial_name: str
    is_resolved: bool
    failure_mode: str
    instruction: str
    parser_results: Dict[str, str]
    
    # Execution data
    episodes: List[EpisodeData] = field(default_factory=list)
    terminal_output: Optional[str] = None
    pre_agent_output: Optional[str] = None
    post_agent_output: Optional[str] = None
    post_test_output: Optional[str] = None
    
    # Task definition and solution
    task_definition: Optional[str] = None  # From task.yaml
    official_solution: Optional[str] = None  # From solution.sh
    test_file_content: Optional[str] = None  # From tests/ directory
    
    # Metadata
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    trial_started_at: Optional[str] = None
    trial_ended_at: Optional[str] = None
    agent_started_at: Optional[str] = None
    agent_ended_at: Optional[str] = None
    test_started_at: Optional[str] = None
    test_ended_at: Optional[str] = None
    
    # File paths
    task_directory: Optional[str] = None
    results_file: Optional[str] = None


@dataclass
class LLMAnalysis:
    """Analysis result from LLM."""
    error_category: Optional[str] = None
    error_subcategory: Optional[str] = None
    error_description: Optional[str] = None
    root_cause: str = ""
    analysis: str = ""
    raw_response: Optional[str] = None


@dataclass
class AnalysisResult:
    """Complete analysis result for a task."""
    task_id: str
    is_resolved: bool
    llm_analysis: Optional[LLMAnalysis] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "task_id": self.task_id,
            "is_resolved": self.is_resolved,
            "metadata": self.metadata
        }
        
        if self.llm_analysis:
            result["llm_analysis"] = {
                "error_category": self.llm_analysis.error_category,
                "error_subcategory": self.llm_analysis.error_subcategory,
                "error_description": self.llm_analysis.error_description,
                "root_cause": self.llm_analysis.root_cause,
                "analysis": self.llm_analysis.analysis
            }
        
        if self.error:
            result["error"] = self.error
        
        return result


@dataclass
class AnalysisReport:
    """Complete analysis report for a run."""
    run_id: str
    analyzed_at: str
    model_provider: str
    model_name: str
    tasks_analyzed: int
    tasks_resolved: int
    tasks_failed: int
    results: List[AnalysisResult] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "run_id": self.run_id,
            "analyzed_at": self.analyzed_at,
            "model_provider": self.model_provider,
            "model_name": self.model_name,
            "tasks_analyzed": self.tasks_analyzed,
            "tasks_resolved": self.tasks_resolved,
            "tasks_failed": self.tasks_failed,
            "failures": [r.to_dict() for r in self.results if not r.is_resolved]
        }

