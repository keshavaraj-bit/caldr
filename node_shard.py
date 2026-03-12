import uvicorn
import asyncio
import httpx
import sys
from fastapi import FastAPI
from pydantic import BaseModel

# ─── Config from command line ───
PORT = int(sys.argv[1])
LAYER_START = int(sys.argv[2])
LAYER_END = int(sys.argv[3])
NEXT_NODE = sys.argv[4] if len(sys.argv) > 4 else None

NODE_ID = f"shard-{PORT}-layers-{LAYER_START}-{LAYER_END}"
SERVER_URL = "http://localhost:8000"
OLLAMA_URL = "http://localhost:11434"
MODEL = "phi3"

app = FastAPI()

class ShardRequest(BaseModel):
    prompt: str

async def run_shard(prompt: str) -> str:
    async with httpx.AsyncClient(timeout=300) as client:
        response = await client.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": MODEL, "prompt": prompt, "stream": False}
        )
        return response.json()["response"]

async def forward_to_next(result: str) -> str:
    async with httpx.AsyncClient(timeout=300) as client:
        response = await client.post(
            f"{NEXT_NODE}/infer",
            json={"prompt": result}
        )
        return response.json()["response"]

@app.post("/infer")
async def infer(request: ShardRequest):
    print(f"📥 Shard {PORT} (layers {LAYER_START}-{LAYER_END}) processing...")
    result = await run_shard(request.prompt)
    print(f"✅ Shard {PORT} done!")
    if NEXT_NODE:
        print(f"➡️  Forwarding to {NEXT_NODE}...")
        final = await forward_to_next(result)
    else:
        final = result
    return {"response": final, "node_id": NODE_ID}

@app.get("/health")
def health():
    return {
        "node_id": NODE_ID,
        "layers": f"{LAYER_START}-{LAYER_END}",
        "next_node": NEXT_NODE,
        "status": "online"
    }

async def heartbeat():
    while True:
        try:
            async with httpx.AsyncClient() as client:
                await client.post(f"{SERVER_URL}/heartbeat", json={
                    "node_id": NODE_ID,
                    "url": f"http://localhost:{PORT}",
                    "model": MODEL,
                    "free_vram_mb": (LAYER_END - LAYER_START) * 200
                })
        except:
            pass
        await asyncio.sleep(10)

@app.on_event("startup")
async def startup():
    await asyncio.sleep(1)
    try:
        async with httpx.AsyncClient() as client:
            await client.post(f"{SERVER_URL}/register", json={
                "node_id": NODE_ID,
                "url": f"http://localhost:{PORT}",
                "model": MODEL,
                "free_vram_mb": (LAYER_END - LAYER_START) * 200
            })
        print(f"✅ Shard {PORT} registered! Layers {LAYER_START}-{LAYER_END}")
    except:
        print("⚠️ Coordinator not running yet!")
    asyncio.create_task(heartbeat())

if __name__ == "__main__":
    print(f"🚀 Starting shard on port {PORT}")
    print(f"📦 Layers {LAYER_START} → {LAYER_END}")
    print(f"➡️  Next node: {NEXT_NODE or 'NONE (final shard)'}")
    uvicorn.run(app, host="0.0.0.0", port=PORT)