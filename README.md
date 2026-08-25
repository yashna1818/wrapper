# Central GenAI Load-Testing Wrapper & Adapter Framework

A production-oriented, central GenAI load-testing framework built to sit between **Locust** and multiple heterogeneous GenAI applications (Chatbots, RAG pipelines, Image Generation, PPT Generation, Document Generation, Code Gen, Audio/Video Gen, and Agentic AI).

The framework provides **one reusable central unit** that allows any GenAI application to be load-tested through the same Locust infrastructure without hard-coding application-specific logic into Locust.

---

## 1. Core Architecture

```text
                    ┌──────────────────────────────┐
                    │      TEST CONFIGURATION      │
                    │                              │
                    │ application                  │
                    │ workload profile             │
                    │ users                         │
                    │ spawn rate                    │
                    │ duration                      │
                    │ request distribution          │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │     CENTRAL WRAPPER           │
                    │                              │
                    │ Application Registry          │
                    │ Adapter Interface             │
                    │ Request Builder               │
                    │ Response Parser               │
                    │ Metrics Extractor             │
                    │ Error Normalizer              │
                    │ Test Metadata Injector        │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                            ┌───────────┐
                            │  LOCUST   │
                            └─────┬─────┘
                                  │
      ┌───────────────────────────┼───────────────────────────┐
      ▼                           ▼                           ▼
ChatbotAdapter              ImageGenAdapter              PPTGenAdapter
(Tokens, Streaming, TTFT)   (Resolution, Steps)         (Slides, Tools)
      │                           │                           │
      ▼                           ▼                           ▼
Chatbot Service             ImageGen Service            PPT Service
      │                           │                           │
      └───────────────────────────┼───────────────────────────┘
                                  ▼
                      Observability & Isolation
            (OTel / Prometheus / Synthetic Header Tags)
```

---

## 2. Framework Components

### 1. Abstract Adapter Interface (`GenAIAdapter`)
Located in [`wrapper/base_adapter.py`](file:///Users/yashna/Wrapper1/wrapper/base_adapter.py), defines standard methods every application adapter implements:
- `build_request(workload, context)`: Constructs request payload and endpoints.
- `send_request(request, client)`: Sends request via client/session.
- `parse_response(raw_response, latency_ms, ttft_ms)`: Normalizes heterogeneous responses into standard `GenAIResponse`.
- `extract_metrics(response)`: Extracts common (`latency_ms`, `input_tokens`, `output_tokens`, `ttft_ms`) and application-specific metrics.
- `normalize_error(error, status_code)`: Categorizes failures into standard categories.

### 2. Application Registry (`ApplicationRegistry`)
Located in [`wrapper/registry.py`](file:///Users/yashna/Wrapper1/wrapper/registry.py). Maps application names to adapters (`chatbot`, `rag`, `image_generation`, `ppt_generation`, `document_generation`).

### 3. Workload Engine (`WorkloadEngine`)
Located in [`workloads/engine.py`](file:///Users/yashna/Wrapper1/workloads/engine.py). Samples workload parameters dynamically based on min/max ranges or weighted multi-application distributions.

### 4. Synthetic Data Isolation
Located in [`wrapper/context.py`](file:///Users/yashna/Wrapper1/wrapper/context.py). Injects standardized HTTP headers into all load-test requests to prevent synthetic traffic from polluting production conversation history, RL/fine-tuning datasets, Redis state, or analytics:
- `X-Synthetic-Request: true`
- `X-Test-Run-ID: <run_id>`
- `X-Test-Application: <app_name>`
- `X-Test-Environment: <env>`
- `X-Test-Virtual-User-ID: <vu_id>`
- `X-Test-Scenario: <scenario>`

### 5. Error Normalizer (`ErrorNormalizer`)
Located in [`wrapper/errors.py`](file:///Users/yashna/Wrapper1/wrapper/errors.py). Classifies failures into standard enum categories:
- `TIMEOUT`
- `RATE_LIMIT`
- `AUTH_ERROR`
- `SERVER_ERROR`
- `VALIDATION_ERROR`
- `MODEL_ERROR`
- `QUEUE_TIMEOUT`
- `NETWORK_ERROR`
- `UNKNOWN`

---

## 3. Project Structure

```text
/Users/yashna/Wrapper1
├── wrapper/
│   ├── base_adapter.py      # Abstract GenAIAdapter interface
│   ├── registry.py          # ApplicationRegistry
│   ├── request.py           # GenAIRequest & Header injector
│   ├── response.py          # GenAIResponse standard model
│   ├── metrics.py           # MetricSet schema & calculation
│   ├── errors.py            # ErrorNormalizer & ErrorCategory
│   └── context.py           # RequestContext & synthetic isolation
├── adapters/
│   ├── chatbot.py           # ChatbotAdapter
│   ├── rag.py               # RAGAdapter
│   ├── image_generation.py  # ImageGenerationAdapter
│   ├── ppt_generation.py    # PPTGenerationAdapter
│   └── document_generation.py # DocumentGenerationAdapter
├── workloads/
│   ├── engine.py            # WorkloadEngine
│   ├── schemas.py           # Workload dataclasses
│   └── profiles/            # YAML workload profiles
│       ├── normal.yaml
│       ├── peak.yaml
│       ├── stress.yaml
│       ├── spike.yaml
│       ├── endurance.yaml
│       └── naval_operational_load.yaml
├── locust/
│   ├── generic_user.py      # Importable application-agnostic Locust user
│   ├── custom_options.py    # CLI parser (--application, --profile, --scenario)
│   ├── listeners.py         # Custom Locust stat reporting (TTFT, Tokens/sec)
│   └── tasks.py             # Reusable TaskSet
├── observability/
│   ├── metrics.py           # Prometheus counters & histograms
│   ├── tracing.py           # OpenTelemetry span builder
│   └── logging.py           # Structured JSON logger
├── config/
│   ├── loader.py            # YAML test config loader
│   ├── test.yaml            # Single application config
│   └── mixed_scenario.yaml  # Mixed scenario config
├── mock_servers/
│   └── mock_genai_services.py # FastAPI mock backend for testing
├── tests/
│   ├── unit/                # Unit tests
│   ├── adapters/            # Adapter tests
│   └── integration/         # Integration tests
└── README.md
```

---

## 4. Manual Execution Guide for Testers

Locust load tests are manually authored and executed by the tester using standard Locust commands.

### Setup
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Start Mock GenAI Backend (For Testing)
```bash
python mock_servers/mock_genai_services.py
```

### 1. Run Chatbot Load Test (Stress Profile)
```bash
locust \
  -f locust/generic_user.py \
  --host http://localhost:8000 \
  --application chatbot \
  --profile stress \
  --headless -u 10 -r 2 --run-time 30s
```

### 2. Run Image Generation Load Test (Peak Profile)
```bash
locust \
  -f locust/generic_user.py \
  --host http://localhost:8000 \
  --application image_generation \
  --profile peak \
  --headless -u 5 -r 1 --run-time 30s
```

### 3. Run Mixed Multi-Application Load Test (`naval_operational_load`)
```bash
locust \
  -f locust/generic_user.py \
  --host http://localhost:8000 \
  --scenario naval_operational_load \
  --headless -u 20 -r 4 --run-time 30s
```

---

## 5. Adding a New Application Adapter

To add support for a new GenAI application (e.g. `code_generation`):

1. **Create Adapter**: Subclass `GenAIAdapter` in `adapters/code_generation.py`:
```python
from wrapper import GenAIAdapter, GenAIRequest, GenAIResponse

class CodeGenerationAdapter(GenAIAdapter):
    def build_request(self, workload, context=None):
        return GenAIRequest(endpoint="/api/v1/code/generate", payload={"language": "python"})

    def send_request(self, request, client):
        return client.post(request.endpoint, json=request.payload, headers=request.prepare_headers())

    def parse_response(self, raw_response, latency_ms, ttft_ms=None):
        data = raw_response.json()
        return GenAIResponse(success=True, status_code=200, latency_ms=latency_ms, output_tokens=150)
```

2. **Register Adapter**:
```python
from wrapper import registry
registry.register("code_generation", CodeGenerationAdapter())
```

3. **Run Locust Test**:
```bash
locust -f locust/generic_user.py --application code_generation
```

Zero modifications to the central wrapper or Locust core infrastructure are required!

---

## 6. Running Automated Tests

Run the full pytest suite (16 tests passing):
```bash
PYTHONPATH=. ./venv/bin/pytest -v
```
