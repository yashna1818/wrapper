"""
Tests for built-in application adapters (Chatbot, RAG, ImageGen, PPTGen, DocGen).
"""

from adapters import (
    ChatbotAdapter, RAGAdapter, ImageGenerationAdapter,
    PPTGenerationAdapter, DocumentGenerationAdapter
)
from workloads.schemas import (
    TokenWorkloadSpec, ImageWorkloadSpec, PPTWorkloadSpec, DocumentWorkloadSpec
)

class MockHTTPResponse:
    def __init__(self, status_code: int, json_data: dict, text: str = ""):
        self.status_code = status_code
        self._json = json_data
        self.text = text
        self.content = str(json_data).encode("utf-8")

    def json(self):
        return self._json

def test_chatbot_adapter():
    adapter = ChatbotAdapter()
    spec = TokenWorkloadSpec(application="chatbot")
    req = adapter.build_request(spec)
    assert req.endpoint == "/api/v1/chat/completions"
    assert "messages" in req.payload

    mock_resp = MockHTTPResponse(200, {
        "choices": [{"message": {"content": "Hello"}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150}
    })
    parsed = adapter.parse_response(mock_resp, latency_ms=250.0, ttft_ms=50.0)
    assert parsed.success is True
    assert parsed.input_tokens == 100
    assert parsed.output_tokens == 50

def test_rag_adapter():
    adapter = RAGAdapter()
    spec = TokenWorkloadSpec(application="rag")
    req = adapter.build_request(spec)
    assert req.endpoint == "/api/v1/rag/query"

    mock_resp = MockHTTPResponse(200, {
        "answer": "Context answer",
        "retrieval_metadata": {"retrieval_latency_ms": 45.0, "chunks_retrieved": 5},
        "usage": {"prompt_tokens": 300, "completion_tokens": 150, "total_tokens": 450}
    })
    parsed = adapter.parse_response(mock_resp, latency_ms=300.0)
    assert parsed.success is True
    assert parsed.application_metrics["retrieval_latency_ms"] == 45.0
    assert parsed.application_metrics["chunks_retrieved"] == 5

def test_image_adapter():
    adapter = ImageGenerationAdapter()
    spec = ImageWorkloadSpec(application="image_generation", resolution="1024x1024")
    req = adapter.build_request(spec)
    assert req.endpoint == "/api/v1/images/generations"

    mock_resp = MockHTTPResponse(200, {
        "resolution": "1024x1024",
        "steps": 30,
        "data": [{"b64_json": "abcd1234"}]
    })
    parsed = adapter.parse_response(mock_resp, latency_ms=800.0)
    assert parsed.success is True
    assert parsed.input_tokens is None  # Non-token application
    assert parsed.application_metrics["resolution"] == "1024x1024"

def test_ppt_adapter():
    adapter = PPTGenerationAdapter()
    spec = PPTWorkloadSpec(application="ppt_generation")
    req = adapter.build_request(spec)
    assert req.endpoint == "/api/v1/ppt/generate"

    mock_resp = MockHTTPResponse(200, {
        "document_id": "ppt-123",
        "file_size_bytes": 500000,
        "generation_metrics": {"slide_count": 10, "tool_calls": 4, "layout_time_ms": 120.0},
        "usage": {"prompt_tokens": 500, "completion_tokens": 1000}
    })
    parsed = adapter.parse_response(mock_resp, latency_ms=1200.0)
    assert parsed.success is True
    assert parsed.application_metrics["slide_count"] == 10
    assert parsed.application_metrics["tool_calls"] == 4

def test_doc_adapter():
    adapter = DocumentGenerationAdapter()
    spec = DocumentWorkloadSpec(application="document_generation")
    req = adapter.build_request(spec)
    assert req.endpoint == "/api/v1/documents/generate"

    mock_resp = MockHTTPResponse(200, {
        "document_id": "doc-555",
        "format": "pdf",
        "file_size_bytes": 250000,
        "metrics": {"page_count": 5, "section_count": 10, "rendering_time_ms": 300.0},
        "usage": {"prompt_tokens": 400, "completion_tokens": 1600}
    })
    parsed = adapter.parse_response(mock_resp, latency_ms=900.0)
    assert parsed.success is True
    assert parsed.application_metrics["page_count"] == 5
    assert parsed.application_metrics["document_format"] == "pdf"
