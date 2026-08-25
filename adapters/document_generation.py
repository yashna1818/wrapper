"""
Document Generation GenAI Adapter.
Handles document processing (PDF, DOCX, Markdown), page counts, and rendering metrics.
"""

import random
from typing import Any, Optional
from wrapper.base_adapter import GenAIAdapter
from wrapper.request import GenAIRequest
from wrapper.response import GenAIResponse
from wrapper.context import RequestContext

class DocumentGenerationAdapter(GenAIAdapter):
    def __init__(self, endpoint: str = "/api/v1/documents/generate"):
        self.endpoint = endpoint

    def build_request(self, workload: Any, context: Optional[RequestContext] = None) -> GenAIRequest:
        pages_range = getattr(workload, "pages", {"min": 2, "max": 15})
        if isinstance(pages_range, dict):
            page_count = random.randint(pages_range.get("min", 2), pages_range.get("max", 15))
        else:
            page_count = int(pages_range)

        fmt = getattr(workload, "format", "pdf")

        payload = {
            "title": f"Synthetic Operational Briefing #{random.randint(1000, 9999)}",
            "target_pages": page_count,
            "format": fmt,
            "include_toc": True,
            "include_appendix": True
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
            name=f"DocGen - {request.endpoint}"
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
                error_message=getattr(raw_response, "text", "Document Gen error")
            )

        try:
            data = raw_response.json()
            usage = data.get("usage", {})
            metrics = data.get("metrics", {})

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
                    "page_count": metrics.get("page_count", data.get("target_pages")),
                    "section_count": metrics.get("section_count", 0),
                    "rendering_time_ms": metrics.get("rendering_time_ms", 0.0),
                    "document_format": data.get("format", "pdf")
                },
                raw_metadata={"document_id": data.get("document_id")}
            )
        except Exception as e:
            return GenAIResponse(
                success=False,
                status_code=status_code,
                latency_ms=latency_ms,
                error_type="PARSE_ERROR",
                error_message=f"Failed to parse Document Generation response: {e}"
            )
