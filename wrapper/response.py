"""
Normalized standard GenAI response model.
Unifies metrics across heterogeneous workloads (chatbots, RAG, images, PPT, documents, video).
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional

@dataclass
class GenAIResponse:
    success: bool
    status_code: int
    latency_ms: float
    time_to_first_token_ms: Optional[float] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    output_size: Optional[int] = None
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    application_metrics: Dict[str, Any] = field(default_factory=dict)
    raw_metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        # Auto-compute total tokens if input and output are present but total is missing
        if self.total_tokens is None and self.input_tokens is not None and self.output_tokens is not None:
            self.total_tokens = self.input_tokens + self.output_tokens

    @property
    def tokens_per_second(self) -> Optional[float]:
        """
        Calculate generation speed in output tokens per second.
        """
        if self.output_tokens is not None and self.latency_ms > 0:
            effective_latency_sec = (self.latency_ms - (self.time_to_first_token_ms or 0.0)) / 1000.0
            if effective_latency_sec > 0:
                return self.output_tokens / effective_latency_sec
            return self.output_tokens / (self.latency_ms / 1000.0)
        return None
