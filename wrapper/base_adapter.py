"""
Abstract base class interface for GenAI application adapters.
Every application-specific adapter (Chatbot, RAG, Image, PPT, Document) inherits from GenAIAdapter.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional
from wrapper.request import GenAIRequest
from wrapper.response import GenAIResponse
from wrapper.metrics import MetricSet
from wrapper.errors import NormalizedError, ErrorNormalizer
from wrapper.context import RequestContext

class GenAIAdapter(ABC):
    """
    Standard interface separating Locust load-testing infrastructure from
    application-specific API protocols, payload schemas, and response formats.
    """

    @abstractmethod
    def build_request(self, workload: Any, context: Optional[RequestContext] = None) -> GenAIRequest:
        """
        Construct a GenAIRequest payload and endpoint from workload parameters.
        """
        pass

    @abstractmethod
    def send_request(self, request: GenAIRequest, client: Any) -> Any:
        """
        Execute the request using Locust's HTTP client (or custom client/session).
        """
        pass

    @abstractmethod
    def parse_response(
        self,
        raw_response: Any,
        latency_ms: float,
        ttft_ms: Optional[float] = None
    ) -> GenAIResponse:
        """
        Parse raw API response (JSON, streaming chunk, image binary) into normalized GenAIResponse.
        """
        pass

    def extract_metrics(self, response: GenAIResponse) -> MetricSet:
        """
        Extract standard common and application-specific metrics. Default implementation.
        """
        return MetricSet.from_response(response)

    def normalize_error(self, error: Any, status_code: Optional[int] = None) -> NormalizedError:
        """
        Categorize errors into standard failure categories. Default implementation using ErrorNormalizer.
        """
        return ErrorNormalizer.normalize(error, status_code)
