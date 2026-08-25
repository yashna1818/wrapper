"""
Test Configuration Loader.
Parses YAML configuration files and environment variable secrets into unified settings.
"""

import os
import yaml
from dataclasses import dataclass, field
from typing import Dict, Any, Optional

@dataclass
class TestConfig:
    application: str = "chatbot"
    profile: str = "normal"
    scenario: Optional[str] = None
    target_host: str = "http://localhost:8000"
    api_key: Optional[str] = None
    test_run_id: Optional[str] = None
    environment: str = "load_test"
    header_prefix: str = "X-Test-"
    raw_config: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def load(cls, config_path: Optional[str] = None) -> "TestConfig":
        config_data: Dict[str, Any] = {}
        if config_path and os.path.exists(config_path):
            with open(config_path, "r") as f:
                config_data = yaml.safe_load(f) or {}

        # Environment variable overrides
        target_host = os.getenv("GENAI_TARGET_HOST") or config_data.get("target_host", "http://localhost:8000")
        api_key = os.getenv("GENAI_API_KEY") or config_data.get("api_key")
        app_name = os.getenv("GENAI_APPLICATION") or config_data.get("application", "chatbot")
        profile = os.getenv("GENAI_PROFILE") or config_data.get("profile", "normal")
        scenario = os.getenv("GENAI_SCENARIO") or config_data.get("scenario")
        test_run_id = os.getenv("GENAI_TEST_RUN_ID") or config_data.get("test_run_id")

        return cls(
            application=app_name,
            profile=profile,
            scenario=scenario,
            target_host=target_host,
            api_key=api_key,
            test_run_id=test_run_id,
            environment=config_data.get("environment", "load_test"),
            header_prefix=config_data.get("header_prefix", "X-Test-"),
            raw_config=config_data
        )
