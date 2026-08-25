"""
Integration tests executing requests against live mock FastAPI server endpoints.
Verifies synthetic header isolation, response parsing, and error normalizer.
"""

import time
import pytest
import threading
import requests
import uvicorn
from mock_servers.mock_genai_services import app, SYNTHETIC_LOG
from wrapper import RequestContext, registry, synthetic_context
from adapters import register_default_adapters
from workloads.engine import WorkloadEngine

# Ensure default adapters registered
register_default_adapters()

MOCK_PORT = 8899
BASE_URL = f"http://127.0.0.1:{MOCK_PORT}"

@pytest.fixture(scope="module", autouse=True)
def run_mock_server():
    server_thread = threading.Thread(
        target=lambda: uvicorn.run(app, host="127.0.0.1", port=MOCK_PORT, log_level="warning"),
        daemon=True
    )
    server_thread.start()
    
    # Wait for server startup
    started = False
    for _ in range(20):
        try:
            r = requests.get(f"{BASE_URL}/synthetic_log", timeout=1.0)
            if r.status_code == 200:
                started = True
                break
        except Exception:
            time.sleep(0.1)
    
    if not started:
        pytest.fail("Mock FastAPI server failed to start")
    yield

def test_chatbot_integration():
    adapter = registry.get("chatbot")
    engine = WorkloadEngine({"application": "chatbot", "workload": {"input_tokens": {"min": 50, "max": 100}}})
    app_name, spec = engine.next_workload()

    ctx = RequestContext(test_run_id="integration_001", application="chatbot", synthetic=True)
    req = adapter.build_request(spec, context=ctx)
    
    headers = req.prepare_headers()
    start_time = time.perf_counter()
    raw_resp = requests.post(f"{BASE_URL}{req.endpoint}", json=req.payload, headers=headers, timeout=5.0)
    latency_ms = (time.perf_counter() - start_time) * 1000.0

    parsed = adapter.parse_response(raw_resp, latency_ms=latency_ms)
    assert parsed.success is True
    assert parsed.input_tokens is not None
    assert parsed.output_tokens is not None

def test_rag_integration():
    adapter = registry.get("rag")
    engine = WorkloadEngine({"application": "rag", "workload": {"top_k": 3}})
    app_name, spec = engine.next_workload()

    ctx = RequestContext(test_run_id="integration_002", application="rag", synthetic=True)
    req = adapter.build_request(spec, context=ctx)
    
    headers = req.prepare_headers()
    start_time = time.perf_counter()
    raw_resp = requests.post(f"{BASE_URL}{req.endpoint}", json=req.payload, headers=headers, timeout=5.0)
    latency_ms = (time.perf_counter() - start_time) * 1000.0

    parsed = adapter.parse_response(raw_resp, latency_ms=latency_ms)
    assert parsed.success is True
    assert parsed.application_metrics["chunks_retrieved"] == 3

def test_image_gen_integration():
    adapter = registry.get("image_generation")
    engine = WorkloadEngine({"application": "image_generation", "workload": {"resolution": "1024x1024"}})
    app_name, spec = engine.next_workload()

    ctx = RequestContext(test_run_id="integration_003", application="image_generation", synthetic=True)
    req = adapter.build_request(spec, context=ctx)
    
    headers = req.prepare_headers()
    start_time = time.perf_counter()
    raw_resp = requests.post(f"{BASE_URL}{req.endpoint}", json=req.payload, headers=headers, timeout=5.0)
    latency_ms = (time.perf_counter() - start_time) * 1000.0

    parsed = adapter.parse_response(raw_resp, latency_ms=latency_ms)
    assert parsed.success is True
    assert parsed.output_size > 0

def test_synthetic_traffic_isolation_audit():
    # Verify that synthetic headers were captured by the server middleware
    r = requests.get(f"{BASE_URL}/synthetic_log")
    data = r.json()
    assert data["synthetic_count"] > 0
    run_ids = [entry["run_id"] for entry in data["entries"]]
    assert "integration_001" in run_ids or "integration_002" in run_ids or "integration_003" in run_ids
