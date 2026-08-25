"""
Request context and synthetic data isolation context manager.
Ensures load-testing traffic is explicitly flagged to prevent pollution of
production conversation history, RL/fine-tuning datasets, Redis state, or analytics.
"""

import contextvars
import uuid
from dataclasses import dataclass, field
from typing import Dict, Any, Optional

@dataclass
class RequestContext:
    test_run_id: str = field(default_factory=lambda: f"test_{uuid.uuid4().hex[:8]}")
    application: str = "generic"
    environment: str = "load_test"
    synthetic: bool = True
    scenario: str = "default"
    virtual_user_id: str = field(default_factory=lambda: f"vu_{uuid.uuid4().hex[:6]}")
    custom_metadata: Dict[str, Any] = field(default_factory=dict)

    def to_headers(self, header_prefix: str = "X-Test-") -> Dict[str, str]:
        """
        Generate standardized HTTP headers for production-data protection and tracing.
        """
        headers = {
            f"{header_prefix}Run-ID": self.test_run_id,
            f"{header_prefix}Application": self.application,
            f"{header_prefix}Environment": self.environment,
            "X-Synthetic-Request": "true" if self.synthetic else "false",
            f"{header_prefix}Virtual-User-ID": self.virtual_user_id,
            f"{header_prefix}Scenario": self.scenario,
        }
        for k, v in self.custom_metadata.items():
            headers[f"{header_prefix}Meta-{k}"] = str(v)
        return headers

    def to_dict(self) -> Dict[str, Any]:
        return {
            "test_run_id": self.test_run_id,
            "application": self.application,
            "environment": self.environment,
            "synthetic": self.synthetic,
            "scenario": self.scenario,
            "virtual_user_id": self.virtual_user_id,
            "custom_metadata": self.custom_metadata,
        }


# Contextvar to hold the current request context for async/threaded executions
_CURRENT_CONTEXT: contextvars.ContextVar[Optional[RequestContext]] = contextvars.ContextVar(
    "current_request_context", default=None
)

def get_current_context() -> RequestContext:
    ctx = _CURRENT_CONTEXT.get()
    if ctx is None:
        ctx = RequestContext()
        _CURRENT_CONTEXT.set(ctx)
    return ctx

def set_current_context(ctx: RequestContext) -> None:
    _CURRENT_CONTEXT.set(ctx)

class synthetic_context:
    """
    Context manager for scoping synthetic load test requests.
    Example:
        with synthetic_context(test_run_id="stress_001", application="chatbot"):
            adapter.send_request(...)
    """
    def __init__(self, **kwargs):
        self.new_ctx = RequestContext(**kwargs)
        self.token = None

    def __enter__(self) -> RequestContext:
        self.token = _CURRENT_CONTEXT.set(self.new_ctx)
        return self.new_ctx

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.token is not None:
            _CURRENT_CONTEXT.reset(self.token)
