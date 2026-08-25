"""
Unit tests for Core Wrapper modules (Registry, RequestContext, Errors, Response).
"""

import pytest
from wrapper import (
    ApplicationRegistry, GenAIAdapter, RequestContext,
    synthetic_context, ErrorNormalizer, ErrorCategory,
    GenAIResponse, MetricSet, GenAIRequest
)

class MockAdapter(GenAIAdapter):
    def build_request(self, workload, context=None):
        return GenAIRequest(endpoint="/mock", payload={"test": True}, context=context)

    def send_request(self, request, client):
        return None

    def parse_response(self, raw_response, latency_ms, ttft_ms=None):
        return GenAIResponse(success=True, status_code=200, latency_ms=latency_ms)

def test_registry_registration():
    reg = ApplicationRegistry()
    mock_adapter = MockAdapter()
    reg.register("test_app", mock_adapter)

    assert reg.contains("test_app")
    assert reg.get("TEST_APP") == mock_adapter
    assert "test_app" in reg.list_applications()

    with pytest.raises(KeyError):
        reg.get("non_existent_app")

def test_request_context_headers():
    ctx = RequestContext(
        test_run_id="run_123",
        application="chatbot",
        environment="staging",
        synthetic=True,
        scenario="peak"
    )
    headers = ctx.to_headers(header_prefix="X-Test-")

    assert headers["X-Test-Run-ID"] == "run_123"
    assert headers["X-Test-Application"] == "chatbot"
    assert headers["X-Test-Environment"] == "staging"
    assert headers["X-Synthetic-Request"] == "true"
    assert headers["X-Test-Scenario"] == "peak"

def test_synthetic_context_manager():
    with synthetic_context(test_run_id="ctx_001", application="rag") as ctx:
        assert ctx.test_run_id == "ctx_001"
        assert ctx.application == "rag"

def test_error_normalizer():
    e1 = ErrorNormalizer.normalize("HTTP 429 Too Many Requests", status_code=429)
    assert e1.category == ErrorCategory.RATE_LIMIT

    e2 = ErrorNormalizer.normalize("Connection timeout error", status_code=504)
    assert e2.category == ErrorCategory.TIMEOUT

    e3 = ErrorNormalizer.normalize("Unauthorized API Key", status_code=401)
    assert e3.category == ErrorCategory.AUTH_ERROR

    e4 = ErrorNormalizer.normalize("CUDA Out of Memory exception")
    assert e4.category == ErrorCategory.MODEL_ERROR

def test_genai_response_model():
    resp = GenAIResponse(
        success=True,
        status_code=200,
        latency_ms=500.0,
        time_to_first_token_ms=100.0,
        input_tokens=100,
        output_tokens=200
    )
    assert resp.total_tokens == 300
    assert resp.tokens_per_second is not None
    assert resp.tokens_per_second > 0

    metric_set = MetricSet.from_response(resp)
    m_dict = metric_set.to_dict()
    assert m_dict["common"]["input_tokens"] == 100
    assert m_dict["common"]["output_tokens"] == 200
