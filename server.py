import asyncio
import time
import httpx
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from collections import deque
import uuid
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
nodes = {}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Request queue for pipeline ───
request_queue = asyncio.Queue()
active_requests = {}

class NodeRegister(BaseModel):
    node_id: str
    url: str
    model: str
    free_vram_mb: int

class PromptRequest(BaseModel):
    prompt: str
    model: str = "phi3"

def score_node(node: dict) -> float:
    age = time.time() - node["last_seen"]
    if age > 300:
        return -1
    vram_score = node["free_vram_mb"] / 1000
    ping_score = 1000 / max(node["ping_ms"], 1)
    reliability = node["success_rate"]
    return (vram_score * 0.4) + (ping_score * 0.4) + (reliability * 0.2)

@app.post("/register")
def register(node: NodeRegister):
    nodes[node.node_id] = {
        "url": node.url,
        "model": node.model,
        "free_vram_mb": node.free_vram_mb,
        "last_seen": time.time(),
        "ping_ms": 999,
        "success_rate": 1.0,
        "total_requests": 0,
        "failed_requests": 0,
        "busy": False,
        "status": "online"
    }
    print(f"✅ Node registered: {node.node_id[:20]}...")
    return {"message": "registered"}

@app.post("/heartbeat")
def heartbeat(node: NodeRegister):
    if node.node_id not in nodes:
        nodes[node.node_id] = {
            "url": node.url,
            "model": node.model,
            "free_vram_mb": node.free_vram_mb,
            "last_seen": time.time(),
            "ping_ms": 999,
            "success_rate": 1.0,
            "total_requests": 0,
            "failed_requests": 0,
            "busy": False,
            "status": "online"
        }
        print(f"✅ Auto-registered: {node.node_id[:20]}...")
    else:
        nodes[node.node_id]["last_seen"] = time.time()
        nodes[node.node_id]["free_vram_mb"] = node.free_vram_mb
    return {"message": "ok"}

@app.get("/nodes")
def list_nodes():
    return {
        k: {**v, "score": round(score_node(v), 3)}
        for k, v in nodes.items()
    }

def get_ranked_nodes(model: str):
    candidates = {
        k: v for k, v in nodes.items()
        if v["model"] == model
        and time.time() - v["last_seen"] < 300
    }
    if not candidates:
        return []
    scored = [(k, v, score_node(v)) for k, v in candidates.items()]
    scored.sort(key=lambda x: x[2], reverse=True)
    return [(k, v) for k, v, s in scored if s >= 0]

# ─── Try a single node ───
async def try_node(node_id: str, node_info: dict, prompt: str):
    start = time.time()
    nodes[node_id]["busy"] = True
    try:
        async with httpx.AsyncClient(timeout=300) as client:
            response = await client.post(
                f"{node_info['url']}/infer",
                json={"prompt": prompt}
            )
            ping = (time.time() - start) * 1000
            result = response.json()

            nodes[node_id]["ping_ms"] = ping
            nodes[node_id]["total_requests"] += 1
            s = nodes[node_id]["total_requests"]
            f = nodes[node_id]["failed_requests"]
            nodes[node_id]["success_rate"] = (s - f) / s
            nodes[node_id]["busy"] = False

            print(f"✅ Node {node_id[:12]}... done in {ping:.0f}ms")
            return result["response"], node_id, ping
    except Exception as e:
        nodes[node_id]["busy"] = False
        raise e

# ─── Process one request with failover ───
async def process_request(prompt: str, model: str):
    ranked = get_ranked_nodes(model)
    if not ranked:
        raise Exception("No nodes available")

    last_error = None
    for attempt, (node_id, node_info) in enumerate(ranked):
        try:
            if attempt > 0:
                print(f"🔄 Failover attempt {attempt + 1} → {node_id[:12]}...")
            else:
                print(f"⚡ Routing to: {node_id[:12]}... | Score: {round(score_node(node_info), 2)}")

            response, used_node, ping = await try_node(node_id, node_info, prompt)
            return response, used_node, ping, attempt + 1

        except Exception as e:
            last_error = str(e)
            print(f"❌ Node {node_id[:12]}... failed: {last_error}")
            if node_id in nodes:
                nodes[node_id]["failed_requests"] += 1
                nodes[node_id]["total_requests"] += 1
                s = nodes[node_id]["total_requests"]
                f = nodes[node_id]["failed_requests"]
                nodes[node_id]["success_rate"] = (s - f) / s
            continue

    raise Exception(f"All nodes failed. Last: {last_error}")

# ─── Pipeline: handle many requests simultaneously ───
@app.post("/query")
async def query(request: PromptRequest):
    request_id = str(uuid.uuid4())[:8]
    print(f"\n📥 [{request_id}] Query: {request.prompt[:50]}...")

    # Run concurrently — doesn't block other requests
    try:
        response, used_node, ping, attempts = await process_request(
            request.prompt,
            request.model
        )
        print(f"✅ [{request_id}] Done!")
        return {
            "response": response,
            "served_by": used_node,
            "ping_ms": round(ping),
            "score": round(score_node(nodes[used_node]), 3),
            "model": request.model,
            "attempts": attempts,
            "request_id": request_id
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

@app.get("/health")
def health():
    alive = sum(1 for n in nodes.values() if time.time() - n["last_seen"] < 300)
    busy = sum(1 for n in nodes.values() if n.get("busy", False))
    return {
        "status": "online",
        "total_nodes": len(nodes),
        "alive_nodes": alive,
        "busy_nodes": busy,
        "free_nodes": alive - busy
    }

if __name__ == "__main__":
    print("🌐 Starting Caldr coordinator...")
    uvicorn.run(app, host="0.0.0.0", port=8000, workers=1)