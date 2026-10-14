import time
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel, Field
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from .providers import provider

app = FastAPI(title="Bedrock AI Gateway", version="0.1.0")
REQUESTS = Counter("ai_requests_total", "AI requests", ["status"])
LATENCY = Histogram("ai_request_duration_seconds", "AI request latency")

class Message(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    content: str = Field(min_length=1, max_length=20000)

class ChatRequest(BaseModel):
    messages: list[Message] = Field(min_length=1, max_length=50)

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.get("/readyz")
def readyz():
    return {"status": "ready"}

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.post("/v1/chat")
def chat(req: ChatRequest):
    started = time.perf_counter()
    try:
        text = provider().converse([m.model_dump() for m in req.messages])
        REQUESTS.labels("success").inc()
        return {"output": text}
    except Exception as exc:
        REQUESTS.labels("error").inc()
        raise HTTPException(status_code=502, detail="Foundation model invocation failed") from exc
    finally:
        LATENCY.observe(time.perf_counter() - started)
