"""
PPT/Presentation Generation GenAI Adapter.
Handles slide count, theme customization, agent tool execution metrics, and presentation output.
"""

import random
from typing import Any, Optional
from wrapper.base_adapter import GenAIAdapter
from wrapper.request import GenAIRequest
from wrapper.response import GenAIResponse
from wrapper.context import RequestContext

class PPTGenerationAdapter(GenAIAdapter):
    def __init__(self, endpoint: str = "/api/v1/ppt/generate"):
        self.endpoint = endpoint

    def build_request(self, workload: Any, context: Optional[RequestContext] = None) -> GenAIRequest:
        slides_range = getattr(workload, "slides", {"min": 5, "max": 20})
        if isinstance(slides_range, dict):
            slide_count = random.randint(slides_range.get("min", 5), slides_range.get("max", 20))
        else:
            slide_count = int(slides_range)

        include_charts = getattr(workload, "include_charts", True)
        
        payload = {
            "topic": f"Naval Operational Assessment Report {random.randint(100, 999)}",
            "slide_count": slide_count,
            "theme": "navy_dark_mode",
            "include_charts": include_charts,
            "export_format": "pptx"
        }

        return GenAIRequest(
            endpoint=self.endpoint,
            method="POST",
            payload=payload,
            context=context
        )

    def send_request(self, request: GenAIRequest, client: Any) -> Any:
        headers = request.prepare_headers()
        return client.post(
            request.endpoint,
            json=request.payload,
            headers=headers,
            timeout=request.timeout,
            name=f"PPTGen - {request.endpoint}"
        )

    def parse_response(
        self,
        raw_response: Any,
        latency_ms: float,
        ttft_ms: Optional[float] = None
    ) -> GenAIResponse:
        status_code = getattr(raw_response, "status_code", 500)

        if status_code != 200:
            return GenAIResponse(
                success=False,
                status_code=status_code,
                latency_ms=latency_ms,
                error_type="HTTP_ERROR",
                error_message=getattr(raw_response, "text", "PPT Gen error")
            )

        try:
            data = raw_response.json()
            usage = data.get("usage", {})
            metrics = data.get("generation_metrics", {})

            return GenAIResponse(
                success=True,
                status_code=status_code,
                latency_ms=latency_ms,
                time_to_first_token_ms=ttft_ms,
                input_tokens=usage.get("prompt_tokens"),
                output_tokens=usage.get("completion_tokens"),
                total_tokens=usage.get("total_tokens"),
                output_size=data.get("file_size_bytes"),
                application_metrics={
                    "slide_count": metrics.get("slide_count", data.get("slide_count")),
                    "tool_calls": metrics.get("tool_calls", 0),
                    "chart_count": metrics.get("chart_count", 0),
                    "layout_time_ms": metrics.get("layout_time_ms", 0.0),
                    "generation_time_ms": latency_ms
                },
                raw_metadata={"document_id": data.get("document_id")}
            )
        except Exception as e:
            return GenAIResponse(
                success=False,
                status_code=status_code,
                latency_ms=latency_ms,
                error_type="PARSE_ERROR",
                error_message=f"Failed to parse PPT Generation response: {e}"
            )
