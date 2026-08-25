"""
Extensible Workload Specs & Dataclasses.
Defines application-agnostic workload parameters for single and mixed application scenarios.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Union

@dataclass
class TokenRange:
    min: int = 100
    max: int = 1000

@dataclass
class WorkloadSpec:
    application: str
    custom_params: Dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        if hasattr(self, key):
            val = getattr(self, key)
            if val is not None:
                return val
        return self.custom_params.get(key, default)

@dataclass
class TokenWorkloadSpec(WorkloadSpec):
    input_tokens: Union[Dict[str, int], TokenRange] = field(default_factory=lambda: {"min": 100, "max": 1000})
    output_tokens: Union[Dict[str, int], TokenRange] = field(default_factory=lambda: {"min": 50, "max": 500})
    stream: bool = False
    model: str = "gpt-4o"

@dataclass
class ImageWorkloadSpec(WorkloadSpec):
    resolution: str = "1024x1024"
    prompt_complexity: str = "medium"
    steps: int = 30

@dataclass
class PPTWorkloadSpec(WorkloadSpec):
    slides: Union[Dict[str, int], TokenRange] = field(default_factory=lambda: {"min": 5, "max": 20})
    include_charts: bool = True

@dataclass
class DocumentWorkloadSpec(WorkloadSpec):
    pages: Union[Dict[str, int], TokenRange] = field(default_factory=lambda: {"min": 2, "max": 15})
    format: str = "pdf"

@dataclass
class ApplicationWeight:
    name: str
    percentage: float
    workload: Dict[str, Any] = field(default_factory=dict)

@dataclass
class MixedWorkloadSpec:
    scenario: str
    applications: List[ApplicationWeight] = field(default_factory=list)
