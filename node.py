import httpx
import uvicorn
import asyncio
import subprocess
import uuid
from fastapi import FastAPI
from pydantic import BaseModel

NODE_ID = str(uuid.uuid4())
MODEL = "phi3"
PORT = 8001
SERVER_URL = "http://localhost:8000"

app = FastAPI()

class PromptRequest(BaseModel):
    prompt: str

def get_free_vram():
    try:
        result = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=memory.free", "--format=csv,noheader,nounits"],
            encoding="utf-8"
        )
        return int(result.strip())
    except:
        return 0

async def run_prompt(prompt: str) -> str:
    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(
            "http://localhost:11434/api/generate",
            json={"model": MODEL, "prompt": prompt, "stream": False}
        )
        return response.json()["response"]

@app.post("/infer")
async def infer(request: PromptRequest):
    print(f"📥 Prompt: {request.prompt[:50]}...")
    result = await run_prompt(request.prompt)
    print(f"✅ Done!")
    return {"response": result, "node_id": NODE_ID}

@app.get("/health")
def health():
    return {
        "node_id": NODE_ID,
        "model": MODEL,
        "free_vram_mb": get_free_vram(),
        "status": "online"
    }

# ─── Heartbeat every 10 seconds ───
async def heartbeat():
    while True:
        try:
            async with httpx.AsyncClient() as client:
                await client.post(f"{SERVER_URL}/heartbeat", json={
                    "node_id": NODE_ID,
                    "url": f"http://localhost:{PORT}",
                    "model": MODEL,
                    "free_vram_mb": get_free_vram()
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
                "free_vram_mb": get_free_vram()
            })
        print(f"✅ Registered with coordinator!")
    except:
        print("⚠️ Coordinator not running yet!")
    asyncio.create_task(heartbeat())

if __name__ == "__main__":
    print(f"🚀 Node {NODE_ID[:8]}...")
    print(f"🎮 VRAM free: {get_free_vram()}MB")
    uvicorn.run(app, host="0.0.0.0", port=PORT)