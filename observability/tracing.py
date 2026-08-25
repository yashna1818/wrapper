"""
OpenTelemetry Tracing integration module.
Manages span generation and correlation of test_run_id -> Locust request -> API -> RAG -> LLM response.
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

try:
    from opentelemetry import trace
    from opentelemetry.trace import Status, StatusCode
    tracer = trace.get_tracer("genai.loadtest.wrapper", "1.0.0")
    OTEL_AVAILABLE = True
except Exception as e:
    OTEL_AVAILABLE = False
    logger.warning(f"OpenTelemetry API not available: {e}")

class ObservabilityTracer:
    @staticmethod
    def start_span(name: str, attributes: Optional[Dict[str, Any]] = None):
        """
        Start an OpenTelemetry span if available, otherwise return a dummy context manager.
        """
        if OTEL_AVAILABLE:
            span = tracer.start_span(name)
            if attributes:
                for k, v in attributes.items():
                    if v is not None:
                        span.set_attribute(str(k), str(v))
            return span
        return DummySpan()

class DummySpan:
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
    def set_attribute(self, key: str, value: Any):
        pass
    def set_status(self, status):
        pass
