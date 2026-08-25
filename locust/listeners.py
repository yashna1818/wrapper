"""
Locust Event Listeners for GenAI metric tracking and summary logging.
Correlates Locust http statistics with GenAI tokens, TTFT, and normalized error categories.
"""

import time
import logging
from collections import defaultdict
from locust import events
from wrapper.errors import ErrorCategory
from observability.metrics import ObservabilityMetrics
from observability.logging import setup_structured_logging

logger = setup_structured_logging()

# Aggregated run stats
_STATS = {
    "requests": 0,
    "successes": 0,
    "failures": 0,
    "total_input_tokens": 0,
    "total_output_tokens": 0,
    "ttft_list": [],
    "error_categories": defaultdict(int)
}

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    logger.info("GenAI Load Test run starting...")
    _STATS["requests"] = 0
    _STATS["successes"] = 0
    _STATS["failures"] = 0
    _STATS["total_input_tokens"] = 0
    _STATS["total_output_tokens"] = 0
    _STATS["ttft_list"] = []
    _STATS["error_categories"].clear()

def record_genai_event(
    request_type: str,
    name: str,
    response_time: float,
    response_length: int,
    exception: Exception,
    context: dict,
    genai_metrics: dict = None
):
    """
    Helper called by GenAILoadUser to aggregate metrics into listeners.
    """
    _STATS["requests"] += 1
    if exception is None:
        _STATS["successes"] += 1
    else:
        _STATS["failures"] += 1

    if genai_metrics:
        common = genai_metrics.get("common", {})
        in_tok = common.get("input_tokens")
        out_tok = common.get("output_tokens")
        ttft = common.get("time_to_first_token_ms")
        err_type = common.get("error_type", "UNKNOWN" if exception else "NONE")

        if in_tok:
            _STATS["total_input_tokens"] += in_tok
        if out_tok:
            _STATS["total_output_tokens"] += out_tok
        if ttft is not None:
            _STATS["ttft_list"].append(ttft)
        if exception or not common.get("success", True):
            _STATS["error_categories"][err_type] += 1

        # Push to Prometheus
        app_name = context.get("application", "generic")
        ObservabilityMetrics.record(app_name, genai_metrics)

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    req_count = _STATS["requests"]
    if req_count == 0:
        logger.info("GenAI Load Test finished. No requests recorded.")
        return

    ttfts = _STATS["ttft_list"]
    avg_ttft = (sum(ttfts) / len(ttfts)) if ttfts else 0.0

    print("\n=======================================================")
    print("           GenAI LOAD TEST SUMMARY REPORT              ")
    print("=======================================================")
    print(f" Total Requests         : {req_count}")
    print(f" Successful Requests    : {_STATS['successes']}")
    print(f" Failed Requests        : {_STATS['failures']}")
    print(f" Total Input Tokens     : {_STATS['total_input_tokens']}")
    print(f" Total Output Tokens    : {_STATS['total_output_tokens']}")
    print(f" Average TTFT (ms)      : {avg_ttft:.2f}")
    if _STATS["error_categories"]:
        print(" Failure Breakdown by Category:")
        for cat, cnt in _STATS["error_categories"].items():
            print(f"   - {cat}: {cnt}")
    print("=======================================================\n")
