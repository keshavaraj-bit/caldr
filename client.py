import httpx
import asyncio
import time

SERVER_URL = "http://localhost:8000"

async def query(session: httpx.AsyncClient, prompt: str, request_num: int):
    start = time.time()
    try:
        response = await session.post(
            f"{SERVER_URL}/query",
            json={"prompt": prompt, "model": "phi3"}
        )
        result = response.json()
        elapsed = time.time() - start
        print(f"✅ Request {request_num} done in {elapsed:.1f}s | Node: {result.get('served_by', '?')[:25]}")
    except Exception as e:
        print(f"❌ Request {request_num} failed: {e}")

async def main():
    print("🚀 Sending 10 requests SIMULTANEOUSLY...\n")
    start = time.time()

    async with httpx.AsyncClient(timeout=300) as session:
        # Fire all 10 at exactly the same time
        tasks = [
            query(session, "What is AI in one sentence?", i+1)
            for i in range(10)
        ]
        await asyncio.gather(*tasks)

    total = time.time() - start
    print(f"\n⚡ All 10 requests completed in {total:.1f}s total")
    print(f"📊 Average: {total/10:.1f}s per request")

if __name__ == "__main__":
    asyncio.run(main())