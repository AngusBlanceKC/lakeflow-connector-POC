"""Path-based reverse proxy for the local fake APIs.

Cloudflare Quick Tunnels expose one origin port. This gateway keeps one origin
on port 8000 and routes a URL prefix to each simulator's dedicated port.
"""

from fastapi import FastAPI, Request
from fastapi.responses import Response
import httpx

app = FastAPI(title="Fake API Cloudflare Gateway")

ROUTES = {
    "visit-create": (8100, ""),
    "fusion": (8010, ""),
    "gevme": (8020, ""),
    "fairverify": (8030, ""),
    "showoff": (8040, ""),
    "livebuzz": (8050, ""),
}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "fake-api-cloudflare-gateway"}


@app.api_route(
    "/{api_name}/{path:path}",
    methods=["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"],
)
async def proxy(api_name: str, path: str, request: Request) -> Response:
    route = ROUTES.get(api_name)
    if route is None:
        return Response(content="unknown fake API route", status_code=404)

    port, path_prefix = route
    target = f"http://127.0.0.1:{port}/{path_prefix}{path}"
    headers = {
        key: value
        for key, value in request.headers.items()
        if key.lower() not in {"host", "content-length"}
    }

    async with httpx.AsyncClient(follow_redirects=False, timeout=60) as client:
        upstream = await client.request(
            request.method,
            target,
            params=list(request.query_params.multi_items()),
            headers=headers,
            content=await request.body(),
        )

    response_headers = {
        key: value
        for key, value in upstream.headers.items()
        if key.lower() not in {"content-length", "transfer-encoding", "connection"}
    }
    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        headers=response_headers,
        media_type=upstream.headers.get("content-type"),
    )
