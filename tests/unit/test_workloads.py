"""
Unit tests for Workload Engine and Profile loader.
"""

import pytest
from workloads.engine import WorkloadEngine
from workloads.schemas import TokenWorkloadSpec, ImageWorkloadSpec, PPTWorkloadSpec

def test_single_application_workload():
    config = {
        "application": "chatbot",
        "workload": {
            "input_tokens": {"min": 50, "max": 200},
            "output_tokens": {"min": 20, "max": 100}
        }
    }
    engine = WorkloadEngine(config)
    app_name, spec = engine.next_workload()

    assert app_name == "chatbot"
    assert isinstance(spec, TokenWorkloadSpec)
    assert spec.input_tokens == {"min": 50, "max": 200}

def test_mixed_application_workload():
    config = {
        "scenario": "test_mixed",
        "applications": [
            {"name": "chatbot", "percentage": 70, "workload": {}},
            {"name": "image_generation", "percentage": 30, "workload": {"resolution": "1024x1024"}}
        ]
    }
    engine = WorkloadEngine(config)
    assert engine.is_mixed is True

    samples = [engine.next_workload()[0] for _ in range(100)]
    assert "chatbot" in samples
    assert "image_generation" in samples
