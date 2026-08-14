"""Small persistent GEVME API v2 simulator for connector development."""

from __future__ import annotations

import asyncio
import base64
import json
import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from faker import Faker
from fastapi import FastAPI, Form, HTTPException, Query, Request
from fastapi.responses import JSONResponse


ROOT = Path(__file__).parent
DATA_FILE = Path(os.getenv("GEVME_DATA_FILE", ROOT / "data" / "gevme.json"))
EVENT_ID = os.getenv("GEVME_EVENT_ID", "demo-event-001")
CLIENT_ID = os.getenv("GEVME_CLIENT_ID", "demo-client-id")
CLIENT_SECRET = os.getenv("GEVME_CLIENT_SECRET", "demo-client-secret")
ACCESS_TOKEN = os.getenv("GEVME_ACCESS_TOKEN", "demo-access-token")
GENERATION_INTERVAL = float(os.getenv("GEVME_GENERATE_INTERVAL_SECONDS", "60"))
GENERATE_PER_TICK = max(int(os.getenv("GEVME_GENERATE_PER_TICK", "1")), 0)
MAX_GENERATED = max(int(os.getenv("GEVME_MAX_GENERATED_ATTENDEES", "250")), 0)
RATE_LIMIT = max(int(os.getenv("GEVME_RATE_LIMIT", "60")), 1)
RATE_WINDOW = max(int(os.getenv("GEVME_RATE_WINDOW_SECONDS", "60")), 1)

fake = Faker("en_GB")
fake.seed_instance(240814)
lock = threading.Lock()
request_times: dict[str, list[float]] = {}
app = FastAPI(title="GEVME API v2 simulator", version="2.0.0")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _attendee(number: int, *, generated: bool = False) -> dict:
    first = fake.first_name()
    last = fake.last_name()
    email = f"{first}.{last}.{number}@example.test".lower()
    return {
        "id": f"attendee-{number:04d}",
        "event_id": EVENT_ID,
        "email": email,
        "first_name": first,
        "last_name": last,
        "full_name": f"{first} {last}",
        "company": fake.company(),
        "job_title": fake.job(),
        "country": fake.current_country_code(),
        "status": "registered",
        "checked_in": False,
        "created_at": _now(),
        "updated_at": _now(),
        "generated": generated,
    }


def _initial_state() -> dict:
    return {
        "event_id": EVENT_ID,
        "revision": 1,
        "attendees": [_attendee(1), _attendee(2), _attendee(3)],
        "tombstones": [],
    }


def _load() -> dict:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not DATA_FILE.exists():
        state = _initial_state()
        _save(state)
        return state
    try:
        state = json.loads(DATA_FILE.read_text())
        if not state.get("attendees"):
            state = _initial_state()
            _save(state)
        return state
    except json.JSONDecodeError as error:
        raise RuntimeError(f"Invalid GEVME data file: {DATA_FILE}") from error


def _save(state: dict) -> None:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    temp = DATA_FILE.with_suffix(".tmp")
    temp.write_text(json.dumps(state, indent=2) + "\n")
    temp.replace(DATA_FILE)


def _auth(request: Request) -> None:
    auth = request.headers.get("Authorization", "")
    expected = "Bearer " + ACCESS_TOKEN
    if auth != expected:
        raise HTTPException(status_code=401, detail="Bearer token is missing or invalid")


def _limit(request: Request) -> None:
    key = request.client.host if request.client else "unknown"
    now = time.monotonic()
    with lock:
        recent = [stamp for stamp in request_times.get(key, []) if stamp > now - RATE_WINDOW]
        if len(recent) >= RATE_LIMIT:
            retry_after = max(1, int(RATE_WINDOW - (now - recent[0])))
            request_times[key] = recent
            response = JSONResponse({"error": "rate_limit_exceeded"}, status_code=429)
            response.headers["Retry-After"] = str(retry_after)
            raise _RateLimited(response)
        recent.append(now)
        request_times[key] = recent


class _RateLimited(Exception):
    def __init__(self, response: JSONResponse):
        self.response = response


@app.exception_handler(_RateLimited)
async def rate_limit_handler(_: Request, error: _RateLimited) -> JSONResponse:
    return error.response


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "gevme-api-v2-simulator", "event_id": EVENT_ID}


@app.post("/apiv2/api/oauth/access_token")
def access_token(
    grant_type: str = Form(...),
    client_id: str = Form(...),
    client_secret: str = Form(...),
    scope: str = Form("root"),
) -> dict:
    if grant_type not in {"authorization_code", "client_credentials"}:
        raise HTTPException(status_code=400, detail="unsupported_grant_type")
    if client_id != CLIENT_ID or client_secret != CLIENT_SECRET:
        raise HTTPException(status_code=401, detail="invalid_client")
    return {"access_token": ACCESS_TOKEN, "token_type": "Bearer", "scope": scope, "expires_in": 3600}


def _list_attendees(event_id: str, limit: int, offset: int, modified_from: int | None, where_email: str | None) -> list[dict]:
    if event_id != EVENT_ID:
        raise HTTPException(status_code=404, detail="event_not_found")
    with lock:
        rows = list(_load()["attendees"])
    if where_email:
        rows = [row for row in rows if row["email"] == where_email]
    if modified_from is not None:
        threshold = modified_from / 1000
        rows = [row for row in rows if datetime.fromisoformat(row["updated_at"].replace("Z", "+00:00")).timestamp() >= threshold]
    return rows[offset : offset + min(limit, 1000)]


@app.get("/apiv2/api/events/{event_id}/attendees")
def get_attendees(
    request: Request,
    event_id: str,
    limit: int = Query(1000, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    modifiedFrom: int | None = Query(None),
    where_email: str | None = Query(None, alias="where[email]"),
) -> list[dict]:
    _auth(request)
    _limit(request)
    return _list_attendees(event_id, limit, offset, modifiedFrom, where_email)


@app.post("/apiv2/api/events/{event_id}/attendees")
def post_attendees(
    request: Request,
    event_id: str,
    limit: int = Form(1000),
    modifiedFrom: int | None = Form(None),
    where_email: str | None = Form(None, alias="where[email]"),
) -> list[dict]:
    _auth(request)
    _limit(request)
    return _list_attendees(event_id, limit, 0, modifiedFrom, where_email)


@app.get("/apiv2/api/events/{event_id}/attendees/total")
def attendee_total(request: Request, event_id: str) -> dict:
    _auth(request)
    _limit(request)
    rows = _list_attendees(event_id, 1000, 0, None, None)
    return {"total": len(rows), "checked_in": sum(row["checked_in"] for row in rows)}


async def _faker_loop() -> None:
    while True:
        if GENERATION_INTERVAL > 0:
            await asyncio.sleep(GENERATION_INTERVAL)
            with lock:
                state = _load()
                generated = sum(row.get("generated", False) for row in state["attendees"])
                remaining = min(GENERATE_PER_TICK, MAX_GENERATED - generated)
                for _ in range(max(remaining, 0)):
                    state["revision"] += 1
                    state["attendees"].append(_attendee(len(state["attendees"]) + 1, generated=True))
                if remaining > 0:
                    _save(state)
        else:
            await asyncio.sleep(3600)


@app.on_event("startup")
async def startup() -> None:
    _load()
    if GENERATION_INTERVAL > 0 and GENERATE_PER_TICK > 0:
        asyncio.create_task(_faker_loop())


@app.post("/admin/reset")
def reset(request: Request) -> dict:
    expected = "Basic " + base64.b64encode(b"admin:reset-demo").decode()
    if request.headers.get("Authorization") != expected:
        raise HTTPException(status_code=401, detail="admin credentials required")
    with lock:
        _save(_initial_state())
    return {"status": "reset"}


@app.get("/admin/state")
def state(request: Request) -> dict:
    _auth(request)
    with lock:
        return _load()
