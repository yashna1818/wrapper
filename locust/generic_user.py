"""
Generic Application-Agnostic Locust Load User.
Contains ZERO application-specific code. Interacts purely through GenAIAdapter interface & Registry.
"""

import time
import os
import logging
from locust import HttpUser, task, between
from wrapper.registry import registry
from wrapper.context import RequestContext, synthetic_context
from wrapper.errors import ErrorNormalizer
from adapters import register_default_adapters
from workloads.engine import WorkloadEngine
from config.loader import TestConfig
from locust.listeners import record_genai_event

# Ensure built-in adapters are registered
register_default_adapters()

logger = logging.getLogger(__name__)

class GenAILoadUser(HttpUser):
    """
    Application-agnostic Locust HttpUser.
    Executed manually by the tester via standard CLI:
        locust -f locust/generic_user.py --host http://target-api --application chatbot --profile stress
    """
    wait_time = between(0.5, 2.0)

    def on_start(self):
        # Read config options from Locust CLI environment or defaults
        parsed_opts = getattr(self.environment, "parsed_options", None)
        
        config_file = getattr(parsed_opts, "config_file", "config/test.yaml") if parsed_opts else "config/test.yaml"
        self.config = TestConfig.load(config_file)

        # CLI overrides
        if parsed_opts:
            if getattr(parsed_opts, "application", None):
                self.config.application = parsed_opts.application
            if getattr(parsed_opts, "profile", None):
                self.config.profile = parsed_opts.profile
            if getattr(parsed_opts, "scenario", None):
                self.config.scenario = parsed_opts.scenario

        # Initialize workload engine
        if self.config.scenario:
            scenario_path = os.path.join("workloads", "profiles", f"{self.config.scenario}.yaml")
            if not os.path.exists(scenario_path) and os.path.exists(self.config.scenario):
                scenario_path = self.config.scenario
            if os.path.exists(scenario_path):
                self.workload_engine = WorkloadEngine.from_yaml(scenario_path)
            else:
                self.workload_engine = WorkloadEngine(self.config.raw_config)
        else:
            profile_path = os.path.join("workloads", "profiles", f"{self.config.profile}.yaml")
            if os.path.exists(profile_path):
                self.workload_engine = WorkloadEngine.from_yaml(profile_path)
            else:
                self.workload_engine = WorkloadEngine({"application": self.config.application, "workload": {}})

        self.virtual_user_id = f"vu_{id(self)}"

    @task
    def execute_genai_workload(self):
        # 1. Sample next workload (application name & specification)
        app_name, workload_spec = self.workload_engine.next_workload()

        # 2. Resolve adapter from Application Registry
        try:
            adapter = registry.get(app_name)
        except KeyError as err:
            logger.error(f"Failed to resolve adapter: {err}")
            return

        # 3. Create synthetic request context for data isolation
        ctx = RequestContext(
            test_run_id=self.config.test_run_id or "manual_run_001",
            application=app_name,
            environment=self.config.environment,
            synthetic=True,
            scenario=self.config.scenario or self.config.profile,
            virtual_user_id=self.virtual_user_id
        )

        # 4. Build request through adapter interface
        request = adapter.build_request(workload_spec, context=ctx)

        # 5. Execute request and record latency
        start_time = time.perf_counter()
        raw_response = None
        exception = None
        ttft_ms = None

        with synthetic_context(
            test_run_id=ctx.test_run_id,
            application=app_name,
            environment=ctx.environment,
            synthetic=ctx.synthetic
        ):
            try:
                raw_response = adapter.send_request(request, self.client)
            except Exception as e:
                exception = e

        latency_ms = (time.perf_counter() - start_time) * 1000.0

        # 6. Parse response & extract metrics
        if raw_response is not None and exception is None:
            genai_resp = adapter.parse_response(raw_response, latency_ms, ttft_ms=ttft_ms)
            metric_set = adapter.extract_metrics(genai_resp)
            metric_dict = metric_set.to_dict()

            if not genai_resp.success:
                normalized_err = adapter.normalize_error(
                    genai_resp.error_message, status_code=genai_resp.status_code
                )
                metric_dict["common"]["error_type"] = normalized_err.category.value
                exception = Exception(f"[{normalized_err.category.value}] {genai_resp.error_message}")
        else:
            normalized_err = adapter.normalize_error(exception or "Connection failed")
            metric_dict = {
                "common": {
                    "success": False,
                    "status_code": getattr(raw_response, "status_code", 500) if raw_response else 500,
                    "latency_ms": latency_ms,
                    "error_type": normalized_err.category.value
                },
                "application": {}
            }

        # 7. Record event for Locust stats and observability listeners
        record_genai_event(
            request_type="POST",
            name=f"{app_name.upper()} - {request.endpoint}",
            response_time=latency_ms,
            response_length=getattr(raw_response, "content", b"") and len(raw_response.content) or 0,
            exception=exception,
            context=ctx.to_dict(),
            genai_metrics=metric_dict
        )
