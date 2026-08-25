"""
Image Generation GenAI Adapter.
Handles non-token image workloads (resolution, prompt complexity, diffusion steps).
"""

import random
from typing import Any, Optional
from wrapper.base_adapter import GenAIAdapter
from wrapper.request import GenAIRequest
from wrapper.response import GenAIResponse
from wrapper.context import RequestContext

class ImageGenerationAdapter(GenAIAdapter):
    def __init__(self, endpoint: str = "/api/v1/images/generations"):
        self.endpoint = endpoint

    def build_request(self, workload: Any, context: Optional[RequestContext] = None) -> GenAIRequest:
        resolution = getattr(workload, "resolution", "1024x1024")
        prompt_complexity = getattr(workload, "prompt_complexity", "medium")
        steps = getattr(workload, "steps", 30)

        payload = {
            "prompt": f"A realistic high quality image, complexity={prompt_complexity}, seed={random.randint(1, 100000)}",
            "size": resolution,
            "n": 1,
            "steps": steps,
            "response_format": "b64_json"
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
            name=f"ImageGen - {request.endpoint}"
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
                error_message=getattr(raw_response, "text", "Image Gen error")
            )

        try:
            data = raw_response.json()
            images_data = data.get("data", [])
            output_size = len(images_data[0].get("b64_json", "")) if images_data else 0

            return GenAIResponse(
                success=True,
                status_code=status_code,
                latency_ms=latency_ms,
                time_to_first_token_ms=None,  # No tokens for image gen
                input_tokens=None,
                output_tokens=None,
                total_tokens=None,
                output_size=output_size,
                application_metrics={
                    "resolution": data.get("resolution", "1024x1024"),
                    "steps": data.get("steps", 30),
                    "generation_time_ms": latency_ms,
                    "image_count": len(images_data)
                },
                raw_metadata={"created": data.get("created")}
            )
        except Exception as e:
            return GenAIResponse(
                success=False,
                status_code=status_code,
                latency_ms=latency_ms,
                error_type="PARSE_ERROR",
                error_message=f"Failed to parse Image Generation response: {e}"
            )
