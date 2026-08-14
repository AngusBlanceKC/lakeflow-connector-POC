"""Persistent ShowOff ASP API v1.4 simulator."""

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
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse

ROOT = Path(__file__).parent
DATA_FILE = Path(os.getenv("SHOWOFF_DATA_FILE", ROOT / "data" / "showoff-asp-v1-4.json"))
API_KEY = os.getenv("SHOWOFF_API_KEY", "demo-showoff-api-key")
API_SECRET = os.getenv("SHOWOFF_API_SECRET", "demo-showoff-api-secret")
ACCESS_TOKEN = os.getenv("SHOWOFF_ACCESS_TOKEN", "demo-showoff-access-token")
SITE_UUID = os.getenv("SHOWOFF_SITE_UUID", "demo-site-001")
GENERATION_INTERVAL = float(os.getenv("SHOWOFF_GENERATE_INTERVAL_SECONDS", "60"))
GENERATE_PER_TICK = max(int(os.getenv("SHOWOFF_GENERATE_PER_TICK", "1")), 0)
MAX_GENERATED = max(int(os.getenv("SHOWOFF_MAX_GENERATED_VISITORS", "250")), 0)
RATE_LIMIT = max(int(os.getenv("SHOWOFF_RATE_LIMIT", "60")), 1)
RATE_WINDOW = max(int(os.getenv("SHOWOFF_RATE_WINDOW_SECONDS", "60")), 1)

fake = Faker("en_GB")
fake.seed_instance(240814)
app = FastAPI(title="ShowOff ASP API v1.4 simulator", version="1.4")
lock = threading.Lock()
request_times: dict[str, list[float]] = {}
resources = {"visitors", "exhibitors", "seminars", "sessions", "speakers", "sites", "products"}


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def visitor(number: int, generated: bool = False) -> dict:
    first, last = fake.first_name(), fake.last_name()
    return {"Uuid": f"visitor-{number:04d}", "SiteUuid": SITE_UUID, "FirstName": first, "LastName": last,
            "Email": f"{first}.{last}.{number}@example.test".lower(), "Company": fake.company(),
            "JobTitle": fake.job(), "Status": "registered", "Created": now(), "Modified": now(),
            "Generated": generated}


def seed() -> dict:
    return {"revision": 1, "sites": [{"Uuid": SITE_UUID, "Name": "ShowOff Demo Site", "Slug": "showoff-demo", "isActive": True}],
            "products": [{"Uuid": "product-001", "Name": "ShowOff Demo Event", "Code": "DEMO", "isActive": True}],
            "exhibitors": [{"Uuid": "exhibitor-001", "SiteUuid": SITE_UUID, "Name": "Example Exhibitor", "CompanyUuid": "company-001", "isActive": True}],
            "seminars": [{"Uuid": "seminar-001", "SiteUuid": SITE_UUID, "Name": "Opening Keynote", "Slug": "opening-keynote", "isPublished": True}],
            "sessions": [{"Uuid": "session-001", "SiteUuid": SITE_UUID, "Name": "Opening Session", "Start": "2026-09-01T09:00:00Z", "End": "2026-09-01T10:00:00Z"}],
            "speakers": [{"Uuid": "speaker-001", "SiteUuid": SITE_UUID, "FirstName": "Ada", "LastName": "Lovelace", "Company": "Analytical Engines Ltd", "JobTitle": "Mathematician"}],
            "visitors": [visitor(1), visitor(2)], "tombstones": []}


def save(state: dict) -> None:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    temp = DATA_FILE.with_suffix(".tmp")
    temp.write_text(json.dumps(state, indent=2) + "\n")
    temp.replace(DATA_FILE)


def load() -> dict:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not DATA_FILE.exists():
        state = seed(); save(state); return state
    try:
        state = json.loads(DATA_FILE.read_text())
        if not state.get("visitors"):
            state = seed()
            save(state)
        return state
    except json.JSONDecodeError as error:
        raise RuntimeError(f"Invalid ShowOff data file: {DATA_FILE}") from error


def auth(request: Request, *, token_only: bool = False) -> None:
    header = request.headers.get("Authorization", "")
    if header == f"Bearer {ACCESS_TOKEN}":
        return
    if not token_only and header == "Basic " + base64.b64encode(f"{API_KEY}:{API_SECRET}".encode()).decode():
        return
    response = JSONResponse({"error": "invalid_token"}, status_code=401)
    response.headers["WWW-Authenticate"] = 'Bearer error="invalid_token"'
    raise _AuthFailed(response)


class _AuthFailed(Exception):
    def __init__(self, response: JSONResponse):
        self.response = response


@app.exception_handler(_AuthFailed)
async def auth_handler(_: Request, error: _AuthFailed) -> JSONResponse:
    return error.response


class _RateLimited(Exception):
    def __init__(self, response: JSONResponse):
        self.response = response


@app.exception_handler(_RateLimited)
async def rate_handler(_: Request, error: _RateLimited) -> JSONResponse:
    return error.response


def rate_limit(request: Request) -> None:
    key = request.client.host if request.client else "unknown"
    current = time.monotonic()
    with lock:
        recent = [stamp for stamp in request_times.get(key, []) if stamp > current - RATE_WINDOW]
        if len(recent) >= RATE_LIMIT:
            response = JSONResponse({"error": "rate_limit_exceeded"}, status_code=429)
            response.headers["Retry-After"] = str(max(1, int(RATE_WINDOW - (current - recent[0]))))
            raise _RateLimited(response)
        recent.append(current); request_times[key] = recent


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "showoff-asp-v1-4-simulator", "site_uuid": SITE_UUID}


@app.post("/public/token")
def token(request: Request) -> JSONResponse:
    auth(request)
    response = JSONResponse(ACCESS_TOKEN)
    response.headers["Authentication-Info"] = "expires-in=3600"
    response.headers["Expires"] = "3600"
    return response


@app.get("/public/{resource}")
def collection(request: Request, resource: str, O: int = Query(0, ge=0), L: int = Query(10, ge=1, le=1000), S: str | None = None, Q: str | None = None, SiteUuid: str | None = None) -> JSONResponse:
    if resource not in resources:
        raise HTTPException(status_code=404, detail="resource_not_found")
    auth(request, token_only=True); rate_limit(request)
    with lock:
        records = list(load().get(resource, []))
    if SiteUuid:
        records = [item for item in records if item.get("SiteUuid") == SiteUuid]
    if Q:
        query = Q.lower(); records = [item for item in records if query in json.dumps(item).lower()]
    if S:
        field = S.lstrip("-")
        records.sort(key=lambda item: str(item.get(field, "")), reverse=S.startswith("-"))
    page = records[O : O + L]
    response = JSONResponse(page)
    response.headers["X-Records-Total"] = str(len(load().get(resource, [])))
    response.headers["X-Records-Filtered"] = str(len(records))
    response.headers["X-Records-Page"] = str(len(page))
    links = []
    if O > 0: links.append(f"</public/{resource}?O=0&L={L}>; rel=\"first\"")
    if O + L < len(records): links.append(f"</public/{resource}?O={O + L}&L={L}>; rel=\"next\"")
    if links: response.headers["Link"] = ", ".join(links)
    response.headers["Authentication-Info"] = "expires-in=3600"
    return response


@app.get("/public/{resource}/{uuid}")
def individual(request: Request, resource: str, uuid: str) -> dict:
    if resource not in resources: raise HTTPException(status_code=404, detail="resource_not_found")
    auth(request, token_only=True); rate_limit(request)
    with lock: record = next((item for item in load().get(resource, []) if item.get("Uuid") == uuid), None)
    if record is None: raise HTTPException(status_code=404, detail="record_not_found")
    return record


@app.on_event("startup")
async def startup() -> None:
    load()
    if GENERATION_INTERVAL > 0 and GENERATE_PER_TICK > 0: asyncio.create_task(faker_loop())


async def faker_loop() -> None:
    while True:
        if GENERATION_INTERVAL > 0:
            await asyncio.sleep(GENERATION_INTERVAL)
            with lock:
                state = load(); generated = sum(item.get("Generated", False) for item in state["visitors"])
                count = min(GENERATE_PER_TICK, max(MAX_GENERATED - generated, 0))
                for _ in range(count):
                    state["revision"] += 1; state["visitors"].append(visitor(len(state["visitors"]) + 1, True))
                if count: save(state)
        else: await asyncio.sleep(3600)
