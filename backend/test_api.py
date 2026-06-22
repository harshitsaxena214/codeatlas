import httpx
import asyncio

async def run():
    async with httpx.AsyncClient() as client:
        r = await client.post('http://localhost:8000/api/repositories/', json={'github_url':'https://github.com/fastapi/fastapi'})
        print(r.status_code, r.text)

asyncio.run(run())
