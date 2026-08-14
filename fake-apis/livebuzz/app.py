"""FastAPI simulator for the LiveBuzz event JSON API contract."""

from __future__ import annotations

import asyncio
import json
import os
import secrets
import time
from pathlib import Path
from typing import Any

from faker import Faker
from fastapi import FastAPI, HTTPException, Query, Request, Response

app = FastAPI(title="LiveBuzz API simulator", version="1.0.0")
DATA_FILE = Path(os.getenv("LIVEBUZZ_DATA_FILE", "data/livebuzz.json"))
CAMPAIGN = os.getenv("LIVEBUZZ_CAMPAIGN", "demo-event-2026")
API_KEY = os.getenv("LIVEBUZZ_API_KEY", "demo-livebuzz-api-key")
BEARER = os.getenv("LIVEBUZZ_BEARER", "demo-livebuzz-bearer")
RATE_LIMIT = max(1, int(os.getenv("LIVEBUZZ_RATE_LIMIT", "30")))
RATE_WINDOW_SECONDS = max(1, int(os.getenv("LIVEBUZZ_RATE_WINDOW_SECONDS", "60")))
GENERATE_INTERVAL_SECONDS = float(os.getenv("LIVEBUZZ_GENERATE_INTERVAL_SECONDS", "60"))
GENERATE_PER_TICK = max(0, int(os.getenv("LIVEBUZZ_GENERATE_PER_TICK", "1")))
MAX_GENERATED_ATTENDEES = max(
    0, int(os.getenv("LIVEBUZZ_MAX_GENERATED_ATTENDEES", "250"))
)
_state: dict[str, list[dict[str, Any]]] = {
    "exhibitors": [],
    "speakers": [],
    "sessions": [],
    "attendees": [],
}
_requests: dict[str, list[float]] = {}
_generator_task: asyncio.Task[None] | None = None


def _save() -> None:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    temporary = DATA_FILE.with_suffix(DATA_FILE.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump({"campaign": CAMPAIGN, "records": _state}, handle, indent=2)
        handle.write("\n")
    os.replace(temporary, DATA_FILE)


def _seed() -> None:
    fake = Faker("en_GB")
    fake.seed_instance(2026)
    _state["exhibitors"] = [
        {
            "id": "exh-0001",
            "identifier": "LB-EXH-0001",
            "companyName": "Analytical Engines",
            "logo": "/assets/exh-0001.png",
            "description": "Data and event technology",
            "telephone": "+44 20 0000 0001",
            "emailAddress": "hello@example.test",
            "websiteUrl": "https://example.test",
            "stands": ["E09"],
            "addresses": [
                {
                    "line_1": "1 Example Street",
                    "line_2": "",
                    "line_3": "",
                    "city": "London",
                    "county": "London",
                    "region": "England",
                    "country": "GB",
                }
            ],
            "socialMediaChannels": [{"type": "website", "url": "https://example.test"}],
            "status": "active",
            "updated_at": "2026-01-15T10:00:00Z",
        }
    ]
    _state["speakers"] = [
        {
            "id": "spk-0001",
            "firstName": "Ada",
            "lastName": "Lovelace",
            "companyName": "Analytical Engines",
            "jobTitle": "Mathematician",
            "emailAddress": "ada@example.test",
            "biography": "A keynote speaker.",
            "updated_at": "2026-01-15T10:00:00Z",
        }
    ]
    _state["sessions"] = [
        {
            "id": "ses-0001",
            "title": "Future of Events",
            "description": "A demo session",
            "start": "2026-06-15T09:00:00Z",
            "end": "2026-06-15T10:00:00Z",
            "location": "Hall A",
            "track": "Main stage",
            "speaker_ids": ["spk-0001"],
            "updated_at": "2026-01-15T10:00:00Z",
        }
    ]
    _state["attendees"] = [
        {
            "id": "att-0001",
            "firstName": "Grace",
            "lastName": "Hopper",
            "emailAddress": "grace@example.test",
            "companyName": "Compilers Ltd",
            "jobTitle": "Engineer",
            "status": "registered",
            "registered_at": "2026-01-10T09:00:00Z",
            "updated_at": "2026-01-15T10:00:00Z",
        }
    ]
    for number in range(2, 11):
        _state["attendees"].append(
            {
                "id": f"att-{number:04d}",
                "firstName": fake.first_name(),
                "lastName": fake.last_name(),
                "emailAddress": fake.email(),
                "companyName": fake.company(),
                "jobTitle": fake.job(),
                "status": "registered",
                "registered_at": "2026-01-11T09:00:00Z",
                "updated_at": f"2026-01-{number + 10:02d}T09:00:00Z",
            }
        )


def _load() -> None:
    if not DATA_FILE.exists():
        _seed()
        _save()
        return
    try:
        with DATA_FILE.open(encoding="utf-8") as handle:
            payload = json.load(handle)
        records = payload["records"]
        if not isinstance(records, dict) or any(
            not isinstance(records.get(key), list) for key in _state
        ):
            raise ValueError
        _state.update(records)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        raise RuntimeError(
            f"Invalid LiveBuzz simulator state in {DATA_FILE}"
        ) from error


def _authorized(request: Request) -> None:
    supplied = request.headers.get("X-API-Key") or request.headers.get(
        "X-LiveBuzz-API-Key"
    )
    bearer = request.headers.get("Authorization", "")
    if supplied != API_KEY and bearer != f"Bearer {BEARER}":
        raise HTTPException(
            status_code=401, detail="LiveBuzz API key or bearer is invalid"
        )


def _page(
    rows: list[dict[str, Any]], limit: int, offset: int, since: str | None
) -> dict[str, Any]:
    filtered = [
        row for row in rows if not since or str(row.get("updated_at", "")) > since
    ]
    page_size = min(max(limit, 1), 100)
    page = filtered[max(offset, 0) : max(offset, 0) + page_size]
    return {
        "data": page,
        "meta": {
            "total": len(filtered),
            "offset": max(offset, 0),
            "limit": page_size,
            "has_more": max(offset, 0) + page_size < len(filtered),
        },
    }


async def _generate() -> None:
    while True:
        await asyncio.sleep(GENERATE_INTERVAL_SECONDS)
        generated = [
            row for row in _state["attendees"] if row["id"].startswith("generated-")
        ]
        if not GENERATE_PER_TICK or len(generated) >= MAX_GENERATED_ATTENDEES:
            continue
        fake = Faker("en_GB")
        for _ in range(
            min(GENERATE_PER_TICK, MAX_GENERATED_ATTENDEES - len(generated))
        ):
            stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            _state["attendees"].append(
                {
                    "id": f"generated-{secrets.token_hex(5)}",
                    "firstName": fake.first_name(),
                    "lastName": fake.last_name(),
                    "emailAddress": fake.email(),
                    "companyName": fake.company(),
                    "jobTitle": fake.job(),
                    "status": "registered",
                    "registered_at": stamp,
                    "updated_at": stamp,
                }
            )
        _save()


@app.on_event("startup")
async def startup() -> None:
    global _generator_task
    _load()
    if GENERATE_INTERVAL_SECONDS > 0 and GENERATE_PER_TICK > 0:
        _generator_task = asyncio.create_task(_generate())


@app.on_event("shutdown")
async def shutdown() -> None:
    if _generator_task:
        _generator_task.cancel()
        await asyncio.gather(_generator_task, return_exceptions=True)


@app.middleware("http")
async def rate_limit(request: Request, call_next):
    if request.url.path == "/health":
        return await call_next(request)
    now = time.monotonic()
    client = request.client.host if request.client else "unknown"
    calls = [
        stamp
        for stamp in _requests.get(client, [])
        if stamp > now - RATE_WINDOW_SECONDS
    ]
    if len(calls) >= RATE_LIMIT:
        return Response(
            content='{"detail":"Rate limit exceeded"}',
            status_code=429,
            media_type="application/json",
            headers={
                "Retry-After": "1",
                "X-RateLimit-Limit": str(RATE_LIMIT),
                "X-RateLimit-Remaining": "0",
            },
        )
    calls.append(now)
    _requests[client] = calls
    response = await call_next(request)
    response.headers["X-RateLimit-Limit"] = str(RATE_LIMIT)
    response.headers["X-RateLimit-Remaining"] = str(max(0, RATE_LIMIT - len(calls)))
    return response


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "livebuzz-simulator"}


@app.get("/campaign/{campaign}/api/{resource}")
async def resource(
    request: Request,
    campaign: str,
    resource: str,
    limit: int = Query(100),
    offset: int = Query(0),
    since: str | None = None,
):
    _authorized(request)
    if campaign != CAMPAIGN:
        raise HTTPException(status_code=404, detail="LiveBuzz campaign not found")
    aliases = {
        "exhibitors": "exhibitors",
        "speakers": "speakers",
        "sessions": "sessions",
        "seminars": "sessions",
        "attendees": "attendees",
        "registrants": "attendees",
        "customers": "attendees",
    }
    table = aliases.get(resource.lower())
    if table is None:
        raise HTTPException(status_code=404, detail="LiveBuzz resource not found")
    return _page(_state[table], limit, offset, since)
