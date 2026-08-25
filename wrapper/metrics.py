"""
Standard metric schema & extraction helper.
Converts GenAIResponse into common + application-specific structured metric dictionary.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from wrapper.response import GenAIResponse

@dataclass
class MetricSet:
    common: Dict[str, Any] = field(default_factory=dict)
    application: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_response(cls, response: GenAIResponse) -> "MetricSet":
        return cls._from_resp(response)

    @staticmethod
    def _from_resp(response: GenAIResponse) -> "MetricSet":
        common_metrics = {
            "success": response.success,
            "status_code": response.status_code,
            "latency_ms": response.latency_ms,
            "time_to_first_token_ms": response.time_to_first_token_ms,
            "input_tokens": response.input_tokens,
            "output_tokens": response.output_tokens,
            "total_tokens": response.total_tokens,
            "tokens_per_second": response.tokens_per_second,
            "output_size": response.output_size,
            "error_type": response.error_type,
        }
        # Filter out None values from common metrics for clean reporting
        common_filtered = {k: v for k, v in common_metrics.items() if v is not None}
        return MetricSet(
            common=common_filtered,
            application=dict(response.application_metrics)
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "common": self.common,
            "application": self.application
        }
