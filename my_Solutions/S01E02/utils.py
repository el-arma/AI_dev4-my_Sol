import asyncio
import httpx
from typing import Any

async def send_request(
    client: httpx.AsyncClient,
    url: str,
    payload: dict[str, Any]
) -> dict[str, Any]:
    response = await client.post(url, json=payload)
    response.raise_for_status()
    return response.json()

async def sent_multi_async_requests(url: str, payloads: Any) -> Any:
    limits = httpx.Limits(max_connections=100, max_keepalive_connections=20)

    async with httpx.AsyncClient(limits=limits, timeout=30.0) as client:
        tasks = [
            send_request(client, url, payload)
            for payload in payloads
        ]

        results = await asyncio.gather(*tasks)

    return results

