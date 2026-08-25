"""
Mock GenAI Services FastAPI Server.
Simulates heterogeneous GenAI application endpoints (Chatbot, RAG, Image Gen, PPT Gen, Document Gen).
Verifies synthetic header isolation tags and returns realistic responses and token usage metrics.
"""

import time
import random
import uvicorn
from typing import Dict, Any, Optional
from fastapi import FastAPI, Request, Response, Header, HTTPException
from pydantic import BaseModel

app = FastAPI(
    title="Mock GenAI Application Backend",
    description="Simulates realistic GenAI endpoints for load testing verification."
)

# Synthetic Isolation Audit Logger
SYNTHETIC_LOG = []

@app.middleware("http")
async def audit_synthetic_traffic(request: Request, call_next):
    synthetic_header = request.headers.get("x-synthetic-request", "false").lower()
    run_id = request.headers.get("x-test-run-id", "unknown")
    app_name = request.headers.get("x-test-application", "unknown")

    if synthetic_header == "true":
        SYNTHETIC_LOG.append({
            "path": request.url.path,
            "run_id": run_id,
            "application": app_name,
            "timestamp": time.time()
        })
    
    response = await call_next(request)
    return response

# --- 1. CHATBOT ENDPOINT ---
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str = "gpt-4o"
    messages: list[ChatMessage]
    max_tokens: Optional[int] = 500
    stream: Optional[bool] = False
    temperature: Optional[float] = 0.7

@app.post("/api/v1/chat/completions")
async def chat_completions(req: ChatCompletionRequest, request: Request):
    # Simulate LLM inference delay
    latency_sec = random.uniform(0.1, 0.4)
    time.sleep(latency_sec)

    input_text = " ".join([m.content for m in req.messages])
    estimated_input_tokens = max(10, len(input_text) // 4)
    output_tokens = min(req.max_tokens or 200, random.randint(50, 300))

    return {
        "id": f"chatcmpl-{random.randint(10000, 99999)}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": req.model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": f"Simulated chatbot response for prompt ({estimated_input_tokens} input tokens). " + ("word " * (output_tokens // 2))
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": estimated_input_tokens,
            "completion_tokens": output_tokens,
            "total_tokens": estimated_input_tokens + output_tokens
        }
    }

# --- 2. RAG ENDPOINT ---
class RAGQueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5
    max_tokens: Optional[int] = 500
    target_input_tokens: Optional[int] = 200

@app.post("/api/v1/rag/query")
async def rag_query(req: RAGQueryRequest):
    retrieval_delay = random.uniform(0.05, 0.15)
    generation_delay = random.uniform(0.1, 0.3)
    time.sleep(retrieval_delay + generation_delay)

    input_tokens = req.target_input_tokens or 300
    output_tokens = random.randint(100, 500)

    return {
        "answer": f"RAG generated answer based on top {req.top_k} retrieved context documents.",
        "sources": [f"doc_{i}.pdf" for i in range(1, (req.top_k or 5) + 1)],
        "retrieval_metadata": {
            "retrieval_latency_ms": round(retrieval_delay * 1000.0, 2),
            "chunks_retrieved": req.top_k,
            "top_score": 0.942
        },
        "usage": {
            "prompt_tokens": input_tokens,
            "completion_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens
        }
    }

# --- 3. IMAGE GENERATION ENDPOINT ---
class ImageGenRequest(BaseModel):
    prompt: str
    size: Optional[str] = "1024x1024"
    n: Optional[int] = 1
    steps: Optional[int] = 30

@app.post("/api/v1/images/generations")
async def image_generation(req: ImageGenRequest):
    generation_delay = random.uniform(0.3, 0.8)
    time.sleep(generation_delay)

    # Return mock base64 payload
    dummy_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==" * 10

    return {
        "created": int(time.time()),
        "resolution": req.size,
        "steps": req.steps,
        "data": [
            {"b64_json": dummy_b64}
        ]
    }

# --- 4. PPT GENERATION ENDPOINT ---
class PPTGenRequest(BaseModel):
    topic: str
    slide_count: Optional[int] = 10
    theme: Optional[str] = "navy"
    include_charts: Optional[bool] = True

@app.post("/api/v1/ppt/generate")
async def ppt_generation(req: PPTGenRequest):
    layout_delay = random.uniform(0.1, 0.2)
    rendering_delay = random.uniform(0.2, 0.5)
    time.sleep(layout_delay + rendering_delay)

    slides = req.slide_count or 10
    total_tokens = slides * 150

    return {
        "document_id": f"ppt-{random.randint(1000, 9999)}",
        "file_size_bytes": slides * 125000,
        "generation_metrics": {
            "slide_count": slides,
            "tool_calls": random.randint(2, 6),
            "chart_count": 3 if req.include_charts else 0,
            "layout_time_ms": round(layout_delay * 1000.0, 2)
        },
        "usage": {
            "prompt_tokens": total_tokens // 3,
            "completion_tokens": (total_tokens * 2) // 3,
            "total_tokens": total_tokens
        }
    }

# --- 5. DOCUMENT GENERATION ENDPOINT ---
class DocGenRequest(BaseModel):
    title: str
    target_pages: Optional[int] = 5
    format: Optional[str] = "pdf"

@app.post("/api/v1/documents/generate")
async def document_generation(req: DocGenRequest):
    render_delay = random.uniform(0.2, 0.6)
    time.sleep(render_delay)

    pages = req.target_pages or 5
    total_tokens = pages * 400

    return {
        "document_id": f"doc-{random.randint(10000, 99999)}",
        "format": req.format,
        "file_size_bytes": pages * 85000,
        "metrics": {
            "page_count": pages,
            "section_count": pages * 2,
            "rendering_time_ms": round(render_delay * 1000.0, 2)
        },
        "usage": {
            "prompt_tokens": total_tokens // 4,
            "completion_tokens": (total_tokens * 3) // 4,
            "total_tokens": total_tokens
        }
    }

@app.get("/synthetic_log")
async def get_synthetic_log():
    return {"synthetic_count": len(SYNTHETIC_LOG), "entries": SYNTHETIC_LOG[-20:]}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
