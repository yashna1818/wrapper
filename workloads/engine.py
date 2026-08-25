"""
Workload Engine module.
Generates dynamic workload parameters and selects applications based on single or mixed scenarios.
"""

import os
import yaml
import random
import logging
from typing import Dict, Any, List, Tuple, Optional
from workloads.schemas import (
    WorkloadSpec, TokenWorkloadSpec, ImageWorkloadSpec,
    PPTWorkloadSpec, DocumentWorkloadSpec, MixedWorkloadSpec, ApplicationWeight
)

logger = logging.getLogger(__name__)

class WorkloadEngine:
    def __init__(self, config_dict: Optional[Dict[str, Any]] = None):
        self.config = config_dict or {}
        self.is_mixed = False
        self.single_app_name: Optional[str] = None
        self.single_workload_spec: Optional[WorkloadSpec] = None
        self.mixed_weights: List[Tuple[str, float, Dict[str, Any]]] = []
        
        if config_dict:
            self.configure(config_dict)

    def configure(self, config_dict: Dict[str, Any]) -> None:
        self.config = config_dict
        
        # Check if mixed workload scenario
        if "scenario" in config_dict and "applications" in config_dict:
            self.is_mixed = True
            apps = config_dict["applications"]
            self.mixed_weights = []
            for item in apps:
                app_name = item["name"]
                pct = float(item.get("percentage", 0))
                wl = item.get("workload", {})
                self.mixed_weights.append((app_name, pct, wl))
            logger.info(f"Configured mixed workload scenario '{config_dict.get('scenario')}' with {len(self.mixed_weights)} applications")
        else:
            self.is_mixed = False
            self.single_app_name = config_dict.get("application", "chatbot")
            wl_params = config_dict.get("workload", {})
            self.single_workload_spec = self._build_spec(self.single_app_name, wl_params)
            logger.info(f"Configured single workload for application '{self.single_app_name}'")

    @classmethod
    def from_yaml(cls, yaml_path: str) -> "WorkloadEngine":
        if not os.path.exists(yaml_path):
            raise FileNotFoundError(f"Workload profile not found: {yaml_path}")
        with open(yaml_path, "r") as f:
            data = yaml.safe_load(f)
        return cls(data)

    def _build_spec(self, app_name: str, params: Dict[str, Any]) -> WorkloadSpec:
        name = app_name.lower()
        if name in ("chatbot", "chat"):
            return TokenWorkloadSpec(
                application=app_name,
                input_tokens=params.get("input_tokens", {"min": 100, "max": 1000}),
                output_tokens=params.get("output_tokens", {"min": 50, "max": 500}),
                stream=params.get("stream", False),
                model=params.get("model", "gpt-4o"),
                custom_params=params
            )
        elif name == "rag":
            return TokenWorkloadSpec(
                application=app_name,
                input_tokens=params.get("input_tokens", {"min": 100, "max": 1000}),
                output_tokens=params.get("output_tokens", {"min": 100, "max": 800}),
                custom_params={"top_k": params.get("top_k", 5), **params}
            )
        elif name in ("image_generation", "image", "image_gen"):
            return ImageWorkloadSpec(
                application=app_name,
                resolution=params.get("resolution", "1024x1024"),
                prompt_complexity=params.get("prompt_complexity", "medium"),
                steps=params.get("steps", 30),
                custom_params=params
            )
        elif name in ("ppt_generation", "ppt", "ppt_gen"):
            return PPTWorkloadSpec(
                application=app_name,
                slides=params.get("slides", {"min": 5, "max": 20}),
                include_charts=params.get("include_charts", True),
                custom_params=params
            )
        elif name in ("document_generation", "document", "doc_gen"):
            return DocumentWorkloadSpec(
                application=app_name,
                pages=params.get("pages", {"min": 2, "max": 15}),
                format=params.get("format", "pdf"),
                custom_params=params
            )
        else:
            return WorkloadSpec(application=app_name, custom_params=params)

    def next_workload(self) -> Tuple[str, WorkloadSpec]:
        """
        Sample the next workload item.
        Returns tuple of (application_name, WorkloadSpec).
        """
        if not self.is_mixed:
            app_name = self.single_app_name or "chatbot"
            spec = self.single_workload_spec or self._build_spec(app_name, {})
            return app_name, spec

        # Weighted random choice for mixed workloads
        apps, weights, wl_dicts = zip(*self.mixed_weights)
        chosen_idx = random.choices(range(len(apps)), weights=weights, k=1)[0]
        chosen_app = apps[chosen_idx]
        chosen_wl = wl_dicts[chosen_idx]
        spec = self._build_spec(chosen_app, chosen_wl)
        return chosen_app, spec
