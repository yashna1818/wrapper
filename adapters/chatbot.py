"""
Chatbot GenAI Adapter.
Handles text generation and conversational LLM APIs (streaming and non-streaming).
Extracts token counts, time-to-first-token (TTFT), and generation latency.
"""

import json
import random
from typing import Any, Optional, Dict
from wrapper.base_adapter import GenAIAdapter
from wrapper.request import GenAIRequest
from wrapper.response import GenAIResponse
from wrapper.context import RequestContext

class ChatbotAdapter(GenAIAdapter):
    def __init__(self, endpoint: str = "/api/v1/chat/completions", default_model: str = "gpt-4o"):
        self.endpoint = endpoint
        self.default_model = default_model

    def build_request(self, workload: Any, context: Optional[RequestContext] = None) -> GenAIRequest:
        # Extract workload parameters
        get_val = getattr(workload, "get", lambda k, d=None: getattr(workload, k, d))
        input_tokens_range = get_val("input_tokens", {"min": 50, "max": 500})
        output_tokens_range = get_val("output_tokens", {"min": 50, "max": 500})
        streaming = get_val("stream", False)
        
        if isinstance(input_tokens_range, dict):
            target_input_tokens = random.randint(input_tokens_range.get("min", 50), input_tokens_range.get("max", 500))
        else:
            target_input_tokens = int(input_tokens_range)

        if isinstance(output_tokens_range, dict):
            target_output_tokens = random.randint(output_tokens_range.get("min", 50), output_tokens_range.get("max", 500))
        else:
            target_output_tokens = int(output_tokens_range)
        
        # Synthetic prompt construction targeting ~target_input_tokens (approx 4 chars per token)
        prompt_words = ["Analyze", "the", "operational", "status", "and", "generate", "a", "summary", "report", "with", "detailed", "metrics"]
        filler = " ".join([random.choice(prompt_words) for _ in range(max(10, target_input_tokens // 2))])

        payload = {
            "model": getattr(workload, "model", self.default_model),
            "messages": [
                {"role": "system", "content": "You are a helpful AI assistant."},
                {"role": "user", "content": f"{filler} (Target input tokens: {target_input_tokens})"}
            ],
            "max_tokens": target_output_tokens,
            "stream": streaming,
            "temperature": 0.7,
        }

        req = GenAIRequest(
            endpoint=self.endpoint,
            method="POST",
            payload=payload,
            context=context
        )
        return req

    def send_request(self, request: GenAIRequest, client: Any) -> Any:
        headers = request.prepare_headers()
        response = client.post(
            request.endpoint,
            json=request.payload,
            headers=headers,
            timeout=request.timeout,
            name=f"Chatbot - {request.endpoint}"
        )
        return response

    def parse_response(
        self,
        raw_response: Any,
        latency_ms: float,
        ttft_ms: Optional[float] = None
    ) -> GenAIResponse:
        status_code = getattr(raw_response, "status_code", 500)
        
        if status_code != 200:
            err_msg = getattr(raw_response, "text", "Unknown HTTP error")
            return GenAIResponse(
                success=False,
                status_code=status_code,
                latency_ms=latency_ms,
                error_type="HTTP_ERROR",
                error_message=err_msg
            )

        try:
            data = raw_response.json()
            usage = data.get("usage", {})
            input_tokens = usage.get("prompt_tokens")
            output_tokens = usage.get("completion_tokens")
            total_tokens = usage.get("total_tokens")
            
            # Content output length check
            choices = data.get("choices", [])
            content = choices[0].get("message", {}).get("content", "") if choices else ""
            output_size = len(content.encode("utf-8"))

            return GenAIResponse(
                success=True,
                status_code=status_code,
                latency_ms=latency_ms,
                time_to_first_token_ms=ttft_ms,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens,
                output_size=output_size,
                application_metrics={
                    "finish_reason": choices[0].get("finish_reason") if choices else None,
                    "model": data.get("model")
                },
                raw_metadata={"id": data.get("id")}
            )
        except Exception as e:
            return GenAIResponse(
                success=False,
                status_code=status_code,
                latency_ms=latency_ms,
                error_type="PARSE_ERROR",
                error_message=f"Failed to parse JSON chatbot response: {e}"
            )
