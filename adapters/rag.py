"""
RAG (Retrieval-Augmented Generation) Adapter.
Extends standard token metrics with vector retrieval metrics (retrieval latency, retrieved chunks, top_k).
"""

import random
from typing import Any, Optional
from wrapper.base_adapter import GenAIAdapter
from wrapper.request import GenAIRequest
from wrapper.response import GenAIResponse
from wrapper.context import RequestContext

class RAGAdapter(GenAIAdapter):
    def __init__(self, endpoint: str = "/api/v1/rag/query"):
        self.endpoint = endpoint

    def build_request(self, workload: Any, context: Optional[RequestContext] = None) -> GenAIRequest:
        input_tokens_range = workload.get("input_tokens", {"min": 100, "max": 1000})
        output_tokens_range = workload.get("output_tokens", {"min": 100, "max": 800})
        top_k = workload.get("top_k", 5)

        if isinstance(input_tokens_range, dict):
            target_input_tokens = random.randint(input_tokens_range.get("min", 100), input_tokens_range.get("max", 1000))
        else:
            target_input_tokens = int(input_tokens_range)

        if isinstance(output_tokens_range, dict):
            target_output_tokens = random.randint(output_tokens_range.get("min", 100), output_tokens_range.get("max", 800))
        else:
            target_output_tokens = int(output_tokens_range)

        payload = {
            "query": f"Retrieve relevant knowledge documents for query ID {random.randint(1000, 9999)}",
            "top_k": top_k,
            "max_tokens": target_output_tokens,
            "target_input_tokens": target_input_tokens,
            "vector_search_filter": {"department": "operations"}
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
            name=f"RAG - {request.endpoint}"
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
                error_message=getattr(raw_response, "text", "RAG error")
            )

        try:
            data = raw_response.json()
            usage = data.get("usage", {})
            retrieval_meta = data.get("retrieval_metadata", {})

            return GenAIResponse(
                success=True,
                status_code=status_code,
                latency_ms=latency_ms,
                time_to_first_token_ms=ttft_ms or retrieval_meta.get("retrieval_latency_ms"),
                input_tokens=usage.get("prompt_tokens"),
                output_tokens=usage.get("completion_tokens"),
                total_tokens=usage.get("total_tokens"),
                output_size=len(str(data.get("answer", "")).encode("utf-8")),
                application_metrics={
                    "retrieval_latency_ms": retrieval_meta.get("retrieval_latency_ms", 0.0),
                    "chunks_retrieved": retrieval_meta.get("chunks_retrieved", 0),
                    "vector_similarity_score": retrieval_meta.get("top_score", 0.95),
                },
                raw_metadata={"sources": data.get("sources", [])}
            )
        except Exception as e:
            return GenAIResponse(
                success=False,
                status_code=status_code,
                latency_ms=latency_ms,
                error_type="PARSE_ERROR",
                error_message=f"Failed to parse RAG response: {e}"
            )
