"""Persistent FairVerify Ticketdata v2 simulator."""

from __future__ import annotations

import asyncio
import json
import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from faker import Faker
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse


ROOT = Path(__file__).parent
DATA_FILE = Path(os.getenv("FAIRVERIFY_DATA_FILE", ROOT / "data" / "fairverify-ticketdata-v2.json"))
EVENT_ID = os.getenv("FAIRVERIFY_EVENT_ID", "demo-event-001")
API_KEY = os.getenv("FAIRVERIFY_API_KEY", "demo-fairverify-api-key")
ACCESS_TOKEN = os.getenv("FAIRVERIFY_ACCESS_TOKEN", "demo-fairverify-access-token")
GENERATION_INTERVAL = float(os.getenv("FAIRVERIFY_GENERATE_INTERVAL_SECONDS", "60"))
GENERATE_PER_TICK = max(int(os.getenv("FAIRVERIFY_GENERATE_PER_TICK", "1")), 0)
MAX_GENERATED = max(int(os.getenv("FAIRVERIFY_MAX_GENERATED_TICKETS", "250")), 0)
RATE_LIMIT = max(int(os.getenv("FAIRVERIFY_RATE_LIMIT", "60")), 1)
RATE_WINDOW = max(int(os.getenv("FAIRVERIFY_RATE_WINDOW_SECONDS", "60")), 1)

fake = Faker("en_GB")
fake.seed_instance(240814)
app = FastAPI(title="FairVerify Ticketdata v2 simulator", version="2.0.0")
lock = threading.Lock()
request_times: dict[str, list[float]] = {}


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def ticket(number: int, generated: bool = False) -> dict:
    first, last = fake.first_name(), fake.last_name()
    return {
        "ticket_id": f"fv-ticket-{number:05d}",
        "event_id": EVENT_ID,
        "barcode": f"FVDEMO{number:08d}",
        "ticket_type": "visitor",
        "status": "valid",
        "first_name": first,
        "last_name": last,
        "email": f"{first}.{last}.{number}@example.test".lower(),
        "company": fake.company(),
        "price": 0.0,
        "currency": "EUR",
        "checked_in": False,
        "issued_at": now(),
        "updated_at": now(),
        "custom_fields": {"source": "faker" if generated else "seed"},
        "generated": generated,
    }


def seed() -> dict:
    return {
        "event_id": EVENT_ID,
        "revision": 1,
        "events": [{"event_id": EVENT_ID, "name": "FairVerify Demo Expo", "status": "published", "currency": "EUR"}],
        "tickets": [
            {**ticket(1), "first_name": "Ada", "last_name": "Lovelace", "email": "ada.lovelace@example.test", "company": "Analytical Engines Ltd"},
            {**ticket(2), "first_name": "Grace", "last_name": "Hopper", "email": "grace.hopper@example.test", "company": "Compiler Works", "checked_in": True},
        ],
        "scans": [],
        "tombstones": [],
    }


def save(state: dict) -> None:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = DATA_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2) + "\n")
    tmp.replace(DATA_FILE)


def load() -> dict:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not DATA_FILE.exists():
        state = seed()
        save(state)
        return state
    try:
        state = json.loads(DATA_FILE.read_text())
    except json.JSONDecodeError as error:
        raise RuntimeError(f"Invalid FairVerify state file: {DATA_FILE}") from error
    if not state.get("tickets"):
        state = seed()
        save(state)
    return state


def authenticate(request: Request) -> None:
    bearer = request.headers.get("Authorization") == f"Bearer {ACCESS_TOKEN}"
    key = request.headers.get("X-FairVerify-API-Key") == API_KEY
    if not (bearer or key):
        raise HTTPException(status_code=401, detail="FairVerify bearer token or API key required")


class RateLimited(Exception):
    def __init__(self, response: JSONResponse):
        self.response = response


@app.exception_handler(RateLimited)
async def rate_limit_handler(_: Request, error: RateLimited) -> JSONResponse:
    return error.response


def rate_limit(request: Request) -> None:
    key = request.client.host if request.client else "unknown"
    current = time.monotonic()
    with lock:
        recent = [stamp for stamp in request_times.get(key, []) if stamp > current - RATE_WINDOW]
        if len(recent) >= RATE_LIMIT:
            response = JSONResponse({"error": "rate_limit_exceeded"}, status_code=429)
            response.headers["Retry-After"] = str(max(1, int(RATE_WINDOW - (current - recent[0]))))
            raise RateLimited(response)
        recent.append(current)
        request_times[key] = recent


def rows(event_id: str, limit: int, offset: int, status: str | None, email: str | None) -> list[dict]:
    if event_id != EVENT_ID:
        raise HTTPException(status_code=404, detail="event_not_found")
    with lock:
        result = list(load()["tickets"])
    if status:
        result = [item for item in result if item["status"] == status]
    if email:
        result = [item for item in result if item["email"] == email]
    return result[offset : offset + min(limit, 1000)]


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "fairverify-ticketdata-v2-simulator", "event_id": EVENT_ID}


@app.get("/api/v2/events")
def events(request: Request, limit: int = Query(100, ge=1, le=1000), offset: int = Query(0, ge=0)) -> list[dict]:
    authenticate(request)
    rate_limit(request)
    with lock:
        return load()["events"][offset : offset + limit]


@app.get("/api/v2/events/{event_id}/tickets")
def event_tickets(
    request: Request,
    event_id: str,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    status: str | None = None,
    email: str | None = None,
) -> list[dict]:
    authenticate(request)
    rate_limit(request)
    return rows(event_id, limit, offset, status, email)


@app.get("/api/v2/tickets")
def all_tickets(
    request: Request,
    event_id: str = Query(EVENT_ID),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    status: str | None = None,
    email: str | None = None,
) -> list[dict]:
    authenticate(request)
    rate_limit(request)
    return rows(event_id, limit, offset, status, email)


@app.post("/api/v2/tickets/{ticket_id}/verify")
def verify_ticket(request: Request, ticket_id: str) -> dict:
    authenticate(request)
    rate_limit(request)
    with lock:
        state = load()
        match = next((item for item in state["tickets"] if item["ticket_id"] == ticket_id), None)
        if match is None:
            raise HTTPException(status_code=404, detail="ticket_not_found")
        valid = match["status"] == "valid"
        scan = {"scan_id": f"scan-{state['revision'] + 1:05d}", "ticket_id": ticket_id, "event_id": EVENT_ID, "valid": valid, "scanned_at": now()}
        state["revision"] += 1
        state["scans"].append(scan)
        match["checked_in"] = valid
        match["updated_at"] = scan["scanned_at"]
        save(state)
    return {"valid": valid, "ticket": match, "scan": scan}


@app.get("/admin/state")
def state(request: Request) -> dict:
    authenticate(request)
    with lock:
        return load()


@app.post("/admin/reset")
def reset(request: Request) -> dict:
    if request.headers.get("X-FairVerify-API-Key") != API_KEY:
        raise HTTPException(status_code=401, detail="admin API key required")
    with lock:
        save(seed())
    return {"status": "reset"}


async def faker_loop() -> None:
    while True:
        if GENERATION_INTERVAL > 0:
            await asyncio.sleep(GENERATION_INTERVAL)
            with lock:
                state = load()
                generated = sum(item.get("generated", False) for item in state["tickets"])
                count = min(GENERATE_PER_TICK, max(MAX_GENERATED - generated, 0))
                for _ in range(count):
                    state["revision"] += 1
                    state["tickets"].append(ticket(len(state["tickets"]) + 1, generated=True))
                if count:
                    save(state)
        else:
            await asyncio.sleep(3600)


@app.on_event("startup")
async def startup() -> None:
    load()
    if GENERATION_INTERVAL > 0 and GENERATE_PER_TICK > 0:
        asyncio.create_task(faker_loop())
