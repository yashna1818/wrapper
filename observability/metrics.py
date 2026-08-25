"""
Prometheus Observability metrics registry.
Tracks GenAI load testing counters and histograms across applications and status categories.
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

try:
    from prometheus_client import Counter, Histogram, CollectorRegistry, REGISTRY

    GENAI_REQUESTS_TOTAL = Counter(
        "genai_requests_total",
        "Total number of GenAI load test requests",
        ["application", "status_code", "error_category"],
    )

    GENAI_LATENCY_SECONDS = Histogram(
        "genai_request_duration_seconds",
        "GenAI request latency in seconds",
        ["application", "status"],
        buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0)
    )

    GENAI_TTFT_SECONDS = Histogram(
        "genai_time_to_first_token_seconds",
        "Time to first token (TTFT) in seconds",
        ["application"],
        buckets=(0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0)
    )

    GENAI_TOKENS_TOTAL = Counter(
        "genai_tokens_total",
        "Total tokens processed",
        ["application", "token_type"]
    )
    PROMETHEUS_AVAILABLE = True
except Exception as e:
    PROMETHEUS_AVAILABLE = False
    logger.warning(f"Prometheus client not active: {e}")

class ObservabilityMetrics:
    @staticmethod
    def record(app_name: str, response_dict: Dict[str, Any]) -> None:
        if not PROMETHEUS_AVAILABLE:
            return
        try:
            common = response_dict.get("common", {})
            success = common.get("success", False)
            status_code = str(common.get("status_code", 500))
            error_cat = common.get("error_type", "NONE" if success else "UNKNOWN")
            latency_sec = (common.get("latency_ms", 0.0) or 0.0) / 1000.0

            GENAI_REQUESTS_TOTAL.labels(
                application=app_name,
                status_code=status_code,
                error_category=error_cat
            ).inc()

            GENAI_LATENCY_SECONDS.labels(
                application=app_name,
                status="success" if success else "failure"
            ).observe(latency_sec)

            ttft_ms = common.get("time_to_first_token_ms")
            if ttft_ms is not None and ttft_ms > 0:
                GENAI_TTFT_SECONDS.labels(application=app_name).observe(ttft_ms / 1000.0)

            in_tokens = common.get("input_tokens")
            out_tokens = common.get("output_tokens")
            if in_tokens:
                GENAI_TOKENS_TOTAL.labels(application=app_name, token_type="prompt").inc(in_tokens)
            if out_tokens:
                GENAI_TOKENS_TOTAL.labels(application=app_name, token_type="completion").inc(out_tokens)

        except Exception as ex:
            logger.debug(f"Failed to record Prometheus metric: {ex}")
