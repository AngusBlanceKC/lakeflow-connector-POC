"""FastAPI simulator for the private Fusion/Circdata integration API."""

from __future__ import annotations

import asyncio
import base64
import json
import os
import secrets
import time
from pathlib import Path
from typing import Any

from faker import Faker
from fastapi import FastAPI, HTTPException, Query, Request, Response

app = FastAPI(title="Fusion (Circdata) simulator", version="1.0.0")
DATA_FILE = Path(os.getenv("FUSION_DATA_FILE", "data/fusion-circdata.json"))
EVENT_ID = os.getenv("FUSION_EVENT_ID", "demo-event-001")
USERNAME = os.getenv("FUSION_USERNAME", "demo-user")
PASSWORD = os.getenv("FUSION_PASSWORD", "demo-password")
INSTALL_NAME = os.getenv("FUSION_INSTALL_NAME", "demo-install")
API_KEY = os.getenv("FUSION_API_KEY", "demo-api-key")
GENERATE_INTERVAL_SECONDS = float(os.getenv("FUSION_GENERATE_INTERVAL_SECONDS", "60"))
GENERATE_PER_TICK = max(0, int(os.getenv("FUSION_GENERATE_PER_TICK", "1")))
MAX_GENERATED_PEOPLE = max(0, int(os.getenv("FUSION_MAX_GENERATED_PEOPLE", "250")))
RATE_LIMIT = max(1, int(os.getenv("FUSION_RATE_LIMIT", "60")))
RATE_WINDOW_SECONDS = max(1, int(os.getenv("FUSION_RATE_WINDOW_SECONDS", "60")))
_requests: dict[str, list[float]] = {}
_state: dict[str, list[dict[str, Any]]] = {"people": [], "event_tickets": []}
_generator_task: asyncio.Task[None] | None = None


def _save() -> None:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    temporary = DATA_FILE.with_suffix(DATA_FILE.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump({"event_id": EVENT_ID, "records": _state}, handle, indent=2)
        handle.write("\n")
    os.replace(temporary, DATA_FILE)


def _seed() -> None:
    fake = Faker()
    fake.seed_instance(2026)
    _state["people"] = [
        {
            "Id": "person-0001", "TITLE": "Dr", "FORENAME": "Ada", "SURNAME": "Lovelace",
            "EMAIL": "ada@example.com", "TEL": "+44 20 0000 0001", "MOBILE": "",
            "FAX": "", "COMPANY": "Analytical Engines", "JOBTITLE": "Mathematician",
            "ADDR1": "1 Example Street", "ADDR2": "", "ADDR3": "", "TOWN": "London",
            "COUNTY": "London", "POSTCODE": "EC1A 1AA", "COUNTRY": "GB",
            "STATUS": "registered", "BADGETYPE": "delegate", "CURRENCY": "GBP",
            "ATTENDED": "true", "BADGEID": "BADGE-0001",
        }
    ]
    _state["event_tickets"] = [
        {
            "Id": "ticket-0001", "PersonId": "person-0001", "EventId": EVENT_ID,
            "TicketType": "delegate", "Status": "confirmed", "RegisteredAt": "2026-01-15T10:00:00Z",
            "UpdatedAt": "2026-01-15T10:00:00Z", "CustomFields": {"diet": "none"},
        }
    ]
    for number in range(2, 11):
        person_id = f"person-{number:04d}"
        _state["people"].append({
            "Id": person_id, "TITLE": "", "FORENAME": fake.first_name(), "SURNAME": fake.last_name(),
            "EMAIL": fake.email(), "TEL": fake.phone_number(), "MOBILE": fake.phone_number(),
            "FAX": "", "COMPANY": fake.company(), "JOBTITLE": fake.job(), "ADDR1": fake.street_address(),
            "ADDR2": "", "ADDR3": "", "TOWN": fake.city(), "COUNTY": fake.state(),
            "POSTCODE": fake.postcode(), "COUNTRY": "GB", "STATUS": "registered",
            "BADGETYPE": "visitor", "CURRENCY": "GBP", "ATTENDED": "false", "BADGEID": f"BADGE-{number:04d}",
        })


def _load() -> None:
    if not DATA_FILE.exists():
        _seed()
        _save()
        return
    with DATA_FILE.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    records = payload.get("records")
    if not isinstance(records, dict) or not all(isinstance(records.get(key), list) for key in _state):
        raise RuntimeError(f"Invalid Fusion simulator state in {DATA_FILE}")
    _state.update(records)


def _authorized(request: Request) -> None:
    authorization = request.headers.get("Authorization", "")
    valid_basic = False
    if authorization.startswith("Basic "):
        try:
            decoded = base64.b64decode(authorization[6:]).decode()
            valid_basic = decoded == f"{USERNAME}:{PASSWORD}"
        except (ValueError, UnicodeDecodeError):
            valid_basic = False
    valid_key = request.headers.get("X-Fusion-API-Key") == API_KEY
    valid_install = request.headers.get("X-Fusion-Install-Name") == INSTALL_NAME
    if not (valid_basic and valid_key and valid_install):
        raise HTTPException(status_code=401, detail="Fusion credentials are invalid")


def _page(rows: list[dict[str, Any]], limit: int, offset: int) -> list[dict[str, Any]]:
    return rows[max(0, offset): max(0, offset) + min(max(1, limit), 500)]


async def _generate() -> None:
    while True:
        await asyncio.sleep(GENERATE_INTERVAL_SECONDS)
        generated = [row for row in _state["people"] if row["Id"].startswith("generated-")]
        if not GENERATE_PER_TICK or len(generated) >= MAX_GENERATED_PEOPLE:
            continue
        fake = Faker()
        for _ in range(min(GENERATE_PER_TICK, MAX_GENERATED_PEOPLE - len(generated))):
            person_id = f"generated-{secrets.token_hex(5)}"
            _state["people"].append({
                "Id": person_id, "TITLE": "", "FORENAME": fake.first_name(), "SURNAME": fake.last_name(),
                "EMAIL": fake.email(), "TEL": fake.phone_number(), "MOBILE": "", "FAX": "",
                "COMPANY": fake.company(), "JOBTITLE": fake.job(), "ADDR1": fake.street_address(),
                "ADDR2": "", "ADDR3": "", "TOWN": fake.city(), "COUNTY": fake.state(),
                "POSTCODE": fake.postcode(), "COUNTRY": "GB", "STATUS": "registered",
                "BADGETYPE": "visitor", "CURRENCY": "GBP", "ATTENDED": "false", "BADGEID": person_id,
            })
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
    calls = [stamp for stamp in _requests.get(client, []) if stamp > now - RATE_WINDOW_SECONDS]
    if len(calls) >= RATE_LIMIT:
        return Response(
            content='{"detail":"Rate limit exceeded"}', status_code=429, media_type="application/json",
            headers={"Retry-After": "1", "X-RateLimit-Limit": str(RATE_LIMIT), "X-RateLimit-Remaining": "0"},
        )
    calls.append(now)
    _requests[client] = calls
    response = await call_next(request)
    response.headers["X-RateLimit-Limit"] = str(RATE_LIMIT)
    response.headers["X-RateLimit-Remaining"] = str(max(0, RATE_LIMIT - len(calls)))
    return response


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/People")
async def people(request: Request, eventId: str = Query(EVENT_ID), limit: int = 100, offset: int = 0):
    _authorized(request)
    if eventId != EVENT_ID:
        raise HTTPException(status_code=404, detail="Fusion event not found")
    return _page(_state["people"], limit, offset)


@app.get("/VisitorIntegrationApi/api/EventTicket")
async def event_tickets(request: Request, eventId: str = Query(EVENT_ID), limit: int = 100, offset: int = 0):
    _authorized(request)
    if eventId != EVENT_ID:
        raise HTTPException(status_code=404, detail="Fusion event not found")
    return _page(_state["event_tickets"], limit, offset)
