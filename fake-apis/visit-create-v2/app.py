"""Small, deterministic Visit Create v2 API simulator."""

from __future__ import annotations

import os
import secrets
import string
import time
import asyncio
import json
from collections import defaultdict, deque
from copy import deepcopy
from pathlib import Path
from typing import Any

from faker import Faker
from fastapi import Body, FastAPI, HTTPException, Query, Request, Response, status

app = FastAPI(title="Visit Create v2 simulator", version="2.0.0")

API_KEY = os.getenv("VISIT_API_KEY", "demo-api-key")
EXPO_ID = "0rwwipz7fufs1"
MAX_PAGE_SIZE = 100
DATA_FILE = Path(os.getenv("VISIT_DATA_FILE", "data/visit-create-v2.json"))
GENERATE_INTERVAL_SECONDS = float(os.getenv("VISIT_GENERATE_INTERVAL_SECONDS", "30"))
GENERATE_PER_TICK = max(0, int(os.getenv("VISIT_GENERATE_PER_TICK", "1")))
MAX_GENERATED_VISITORS = max(0, int(os.getenv("VISIT_MAX_GENERATED_VISITORS", "500")))
RATE_LIMIT = int(os.getenv("VISIT_RATE_LIMIT", "60"))
RATE_WINDOW_SECONDS = int(os.getenv("VISIT_RATE_WINDOW_SECONDS", "60"))
ALLOWED_EXPOS = set(filter(None, os.getenv("VISIT_ALLOWED_EXPOS", EXPO_ID).split(",")))
READ_RESOURCES = set(filter(None, os.getenv("VISIT_API_READ_RESOURCES", "*").split(",")))
WRITE_RESOURCES = set(filter(None, os.getenv("VISIT_API_WRITE_RESOURCES", "*").split(",")))
EXPIRES_AT = os.getenv("VISIT_API_EXPIRES_AT")
WRITABLE = {"visitors", "partners", "contents", "licenses", "payments", "activities"}
WEBHOOK_TYPES = {"visitor", "partner", "action", "participant", "connection", "content", "payment"}

_revision = 1000
_records: dict[str, list[dict[str, Any]]] = {}
_webhooks: list[dict[str, Any]] = []
_request_times: dict[str, deque[float]] = defaultdict(deque)
_generator_task: asyncio.Task[None] | None = None


def _next_revision() -> int:
    global _revision
    _revision += 1
    return _revision


def _new_id() -> str:
    alphabet = string.ascii_lowercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(13))


def _seed() -> None:
    global _revision
    _records["expos"] = [
        {"id": EXPO_ID, "revision": 1001, "name": "Demo Expo", "reference": "demo-2026", "status": "live"}
    ]
    for resource, rows in {
        "visitors": [
            {"id": "visitor000001", "revision": 1002, "firstName": "Ada", "lastName": "Lovelace", "email": "ada@example.com", "registrationState": "registered", "deleted": False},
            {"id": "visitor000002", "revision": 1003, "firstName": "Alan", "lastName": "Turing", "email": "alan@example.com", "registrationState": "registered", "deleted": False},
        ],
        "partners": [
            {"id": "partner000001", "revision": 1004, "name": "Example Robotics", "contactReference": "robotics-001", "deleted": False}
        ],
        "participants": [{"id": "participant000001", "revision": 1005, "visitorId": "visitor000001", "showNoShow": "show", "checkIn": "2026-09-01T09:00:00Z"}],
        "contents": [{"id": "content000001", "revision": 1006, "title": "Welcome", "contentType": "event", "body": "Welcome to the demo expo"}],
        "licenses": [{"id": "license000001", "revision": 1007, "type": "demo", "status": "active"}],
        "payments": [{"id": "payment000001", "revision": 1008, "visitorId": "visitor000001", "amount": 25.0, "state": "paid"}],
        "actions": [{"id": "action000001", "revision": 1009, "visitorId": "visitor000001", "type": "badge-scan", "occurredAt": "2026-09-01T09:05:00Z"}],
        "connections": [{"id": "connection000001", "revision": 1010, "visitorId": "visitor000001", "partnerId": "partner000001", "createdAt": "2026-09-01T09:10:00Z"}],
        "activities": [{"id": "activity000001", "revision": 1011, "name": "Opening keynote", "start": "2026-09-01T10:00:00Z", "location": "Main hall"}],
        "touchpoints": [{"id": "touchpoint000001", "revision": 1012, "name": "Entrance scanner", "contentId": "content000001"}],
        "orders": [{"id": "order000001", "revision": 1013, "visitorId": "visitor000001", "state": "paid", "total": 25.0}],
        "questions": [{"id": "question000001", "revision": 1014, "label": "Dietary requirements", "type": "text"}],
        "registrationTypes": [{"id": "registration-type-visitor", "revision": 1015, "name": "Visitor"}],
        "registrationForms": [{"id": "form000001", "revision": 1016, "name": "Standard visitor form"}],
    }.items():
        _records[resource] = rows

    # A deterministic larger visitor set makes the 100-record Visit page
    # boundary and fromRevision pagination easy to exercise locally.
    fake = Faker()
    fake.seed_instance(2026)
    for number in range(3, 126):
        _records["visitors"].append(
            {
                "id": f"visitor{number:07d}",
                "revision": 1012 + number,
                "firstName": fake.first_name(),
                "lastName": fake.last_name(),
                "email": fake.email(),
                "registrationState": "registered",
                "deleted": False,
            }
        )
    _revision = max(row["revision"] for rows in _records.values() for row in rows)


def _save_state() -> None:
    """Persist the simulator state atomically so restarts retain API data."""
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    temporary = DATA_FILE.with_suffix(f"{DATA_FILE.suffix}.tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump({"revision": _revision, "records": _records, "webhooks": _webhooks}, handle, indent=2)
        handle.write("\n")
    os.replace(temporary, DATA_FILE)


def _load_state() -> None:
    global _revision, _records, _webhooks
    if not DATA_FILE.exists():
        _save_state()
        return
    try:
        with DATA_FILE.open(encoding="utf-8") as handle:
            state = json.load(handle)
        if not isinstance(state.get("records"), dict) or not isinstance(state.get("webhooks"), list):
            raise ValueError("state has an invalid shape")
        _revision = int(state["revision"])
        _records = state["records"]
        _webhooks = state["webhooks"]
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as error:
        raise RuntimeError(f"Could not load Visit simulator data from {DATA_FILE}: {error}") from error


def _generate_visitors() -> None:
    generated = [row for row in _records.get("visitors", []) if row["id"].startswith("generated-")]
    remaining = max(0, MAX_GENERATED_VISITORS - len(generated))
    fake = Faker()
    for _ in range(min(GENERATE_PER_TICK, remaining)):
        _records["visitors"].append(
            {
                "id": f"generated-{_new_id()}",
                "revision": _next_revision(),
                "firstName": fake.first_name(),
                "lastName": fake.last_name(),
                "email": fake.email(),
                "registrationState": fake.random_element(elements=("registered", "invited", "pending")),
                "deleted": False,
            }
        )
    if remaining and GENERATE_PER_TICK:
        _save_state()


async def _visitor_generator() -> None:
    while True:
        await asyncio.sleep(GENERATE_INTERVAL_SECONDS)
        _generate_visitors()


_seed()
_load_state()


@app.on_event("startup")
async def start_visitor_generator() -> None:
    global _generator_task
    if GENERATE_INTERVAL_SECONDS > 0 and GENERATE_PER_TICK > 0:
        _generator_task = asyncio.create_task(_visitor_generator())


@app.on_event("shutdown")
async def stop_visitor_generator() -> None:
    if _generator_task:
        _generator_task.cancel()
        await asyncio.gather(_generator_task, return_exceptions=True)


async def _authenticate(request: Request) -> None:
    header = request.headers.get("Authorization", "")
    if not header.startswith("Basic "):
        raise HTTPException(status_code=401, detail="Basic authentication required", headers={"WWW-Authenticate": "Basic"})
    import base64

    try:
        decoded = base64.b64decode(header[6:]).decode()
        username, _password = decoded.split(":", 1)
    except (ValueError, UnicodeDecodeError):
        raise HTTPException(status_code=401, detail="Invalid Basic authentication") from None
    if username != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    if EXPIRES_AT:
        try:
            if time.time() >= float(EXPIRES_AT):
                raise HTTPException(status_code=401, detail="API key has expired")
        except ValueError:
            raise HTTPException(status_code=500, detail="VISIT_API_EXPIRES_AT must be Unix time") from None

    client_ip = request.client.host if request.client else "unknown"
    allowed_ips = set(filter(None, os.getenv("VISIT_ALLOWED_IPS", "").split(",")))
    if allowed_ips and client_ip not in allowed_ips:
        raise HTTPException(status_code=403, detail="Client IP is not allowed")

    path_parts = request.url.path.strip("/").split("/")
    resource = path_parts[2] if len(path_parts) >= 3 and path_parts[:2] == ["create", "v2"] else ""
    permissions = READ_RESOURCES if request.method == "GET" else WRITE_RESOURCES
    if permissions != {"*"} and resource not in permissions:
        raise HTTPException(status_code=403, detail=f"API key is not permitted to access {resource}")

    expo_id = path_parts[3] if len(path_parts) >= 4 and path_parts[:2] == ["create", "v2"] else None
    if expo_id and "*" not in ALLOWED_EXPOS and expo_id not in ALLOWED_EXPOS:
        raise HTTPException(status_code=403, detail="API key is not enabled for this expo")


@app.middleware("http")
async def request_limit(request: Request, call_next):
    """Apply a small, deterministic per-client windowed request limit."""
    if request.url.path == "/health":
        return await call_next(request)
    now = time.monotonic()
    client = request.client.host if request.client else "unknown"
    calls = _request_times[client]
    while calls and calls[0] <= now - RATE_WINDOW_SECONDS:
        calls.popleft()
    if len(calls) >= RATE_LIMIT:
        retry_after = max(1, int(RATE_WINDOW_SECONDS - (now - calls[0])))
        return Response(
            content='{"detail":"Rate limit exceeded"}',
            status_code=429,
            media_type="application/json",
            headers={"Retry-After": str(retry_after), "X-RateLimit-Limit": str(RATE_LIMIT), "X-RateLimit-Remaining": "0"},
        )
    calls.append(now)
    response = await call_next(request)
    response.headers["X-RateLimit-Limit"] = str(RATE_LIMIT)
    response.headers["X-RateLimit-Remaining"] = str(max(0, RATE_LIMIT - len(calls)))
    response.headers["X-RateLimit-Reset"] = str(int(time.time() + RATE_WINDOW_SECONDS))
    return response


def _page(resource: str, from_revision: int, limit: int, show_deleted: bool = True) -> list[dict[str, Any]]:
    rows = [r for r in _records.get(resource, []) if r["revision"] >= from_revision]
    if not show_deleted:
        rows = [r for r in rows if not r.get("deleted", False)]
    return deepcopy(rows[: min(max(limit, 1), MAX_PAGE_SIZE)])


def _rows(resource: str, expo_id: str, from_revision: int, limit: int, show_deleted: bool = True) -> list[dict[str, Any]]:
    if expo_id != EXPO_ID:
        raise HTTPException(status_code=404, detail="Expo not found")
    return _page(resource, from_revision, limit, show_deleted)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/create/v2/expos")
async def list_expos(request: Request, limit: int = 100, fromRevision: int = 0, reference: str | None = None) -> list[dict[str, Any]]:
    await _authenticate(request)
    rows = _page("expos", fromRevision, limit)
    return [r for r in rows if reference is None or r.get("reference") == reference]


@app.get("/create/v2/expos/{item_id}")
async def get_expo(item_id: str, request: Request) -> dict[str, Any]:
    await _authenticate(request)
    for row in _records["expos"]:
        if row["id"] == item_id:
            return deepcopy(row)
    raise HTTPException(status_code=404, detail="Expo not found")


@app.get("/create/v2/{resource}/{expo_id}")
async def list_resource(
    resource: str,
    expo_id: str,
    request: Request,
    limit: int = 100,
    fromRevision: int = 0,
    showDeleted: bool = True,
    webhookId: str | None = None,
    contactReference: str | None = None,
    contactId: str | None = None,
    registrationStates: str | None = None,
) -> list[dict[str, Any]]:
    await _authenticate(request)
    if resource == "webhooks":
        if expo_id != EXPO_ID:
            raise HTTPException(status_code=404, detail="Expo not found")
        return deepcopy(_webhooks)
    if resource not in _records:
        raise HTTPException(status_code=404, detail="Endpoint not found")
    rows = _rows(resource, expo_id, fromRevision, limit, showDeleted)
    if contactReference:
        rows = [r for r in rows if r.get("contactReference") == contactReference]
    if contactId:
        rows = [r for r in rows if r.get("contactId") == contactId]
    if registrationStates:
        allowed = set(registrationStates.split(","))
        rows = [r for r in rows if r.get("registrationState") in allowed]
    if webhookId:
        webhook = next((w for w in _webhooks if w["id"] == webhookId), None)
        if webhook is None:
            raise HTTPException(status_code=404, detail="Webhook not found")
    return rows


@app.get("/create/v2/{resource}/{expo_id}/{item_id}")
async def get_resource(resource: str, expo_id: str, item_id: str, request: Request) -> dict[str, Any]:
    await _authenticate(request)
    if resource == "webhooks":
        if expo_id != EXPO_ID:
            raise HTTPException(status_code=404, detail="Expo not found")
        for webhook in _webhooks:
            if webhook["id"] == item_id:
                return deepcopy(webhook)
        raise HTTPException(status_code=404, detail="Webhook not found")
    for row in _rows(resource, expo_id, 0, MAX_PAGE_SIZE):
        if row["id"] == item_id:
            return row
    raise HTTPException(status_code=404, detail="Record not found")


@app.post("/create/v2/{resource}/{expo_id}", status_code=201)
async def create_resource(resource: str, expo_id: str, request: Request, body: dict[str, Any] = Body(...)) -> dict[str, Any]:
    await _authenticate(request)
    if resource == "webhooks":
        if expo_id != EXPO_ID or body.get("type") not in WEBHOOK_TYPES or not body.get("url"):
            raise HTTPException(status_code=400, detail="Valid url and webhook type are required")
        webhook = {"id": _new_id(), "currentRevision": _revision, "lastRevision": 0, "errorCount": 0, "log": [], "sentTime": None, "state": "wait", "enabled": bool(body.get("enabled", False)), "type": body["type"], "url": body["url"]}
        _webhooks.append(webhook)
        _save_state()
        return deepcopy(webhook)
    if resource not in WRITABLE:
        raise HTTPException(status_code=405, detail="Endpoint is read-only")
    if expo_id != EXPO_ID:
        raise HTTPException(status_code=404, detail="Expo not found")
    row = {**body, "id": body.get("id", _new_id()), "revision": _next_revision(), "deleted": False}
    _records.setdefault(resource, []).append(row)
    _save_state()
    return deepcopy(row)


@app.put("/create/v2/{resource}/{expo_id}/{item_id}")
async def update_resource(resource: str, expo_id: str, item_id: str, request: Request, body: dict[str, Any] = Body(...)) -> dict[str, Any]:
    await _authenticate(request)
    if resource == "webhooks":
        for webhook in _webhooks:
            if webhook["id"] == item_id:
                webhook.update({k: v for k, v in body.items() if k in {"enabled", "url", "type"}})
                return deepcopy(webhook)
        raise HTTPException(status_code=404, detail="Webhook not found")
    if resource not in WRITABLE:
        raise HTTPException(status_code=405, detail="Endpoint is read-only")
    for index, row in enumerate(_records.get(resource, [])):
        if row["id"] == item_id:
            updated = {**row, **body, "id": item_id, "revision": _next_revision()}
            _records[resource][index] = updated
            _save_state()
            return deepcopy(updated)
    raise HTTPException(status_code=404, detail="Record not found")


@app.delete("/create/v2/{resource}/{expo_id}/{item_id}")
async def delete_resource(resource: str, expo_id: str, item_id: str, request: Request) -> Response:
    await _authenticate(request)
    if resource == "webhooks":
        for index, webhook in enumerate(_webhooks):
            if webhook["id"] == item_id:
                _webhooks.pop(index)
                return Response(status_code=status.HTTP_204_NO_CONTENT)
        raise HTTPException(status_code=404, detail="Webhook not found")
    if resource not in WRITABLE:
        raise HTTPException(status_code=405, detail="Endpoint is read-only")
    for index, row in enumerate(_records.get(resource, [])):
        if row["id"] == item_id:
            if resource in {"visitors", "partners"}:
                _records[resource][index] = {**row, "deleted": True, "revision": _next_revision()}
            else:
                _records[resource].pop(index)
            _save_state()
            return Response(status_code=status.HTTP_204_NO_CONTENT)
    raise HTTPException(status_code=404, detail="Record not found")


@app.get("/create/v2/webhooks/{expo_id}")
async def list_webhooks(expo_id: str, request: Request) -> list[dict[str, Any]]:
    await _authenticate(request)
    if expo_id != EXPO_ID:
        raise HTTPException(status_code=404, detail="Expo not found")
    return deepcopy(_webhooks)


@app.post("/create/v2/webhooks/{expo_id}", status_code=201)
async def create_webhook(expo_id: str, request: Request, body: dict[str, Any] = Body(...)) -> dict[str, Any]:
    await _authenticate(request)
    if expo_id != EXPO_ID or body.get("type") not in WEBHOOK_TYPES or not body.get("url"):
        raise HTTPException(status_code=400, detail="Valid url and webhook type are required")
    webhook = {"id": _new_id(), "currentRevision": _revision, "lastRevision": 0, "errorCount": 0, "log": [], "sentTime": None, "state": "wait", "enabled": bool(body.get("enabled", False)), "type": body["type"], "url": body["url"]}
    _webhooks.append(webhook)
    _save_state()
    return deepcopy(webhook)


@app.put("/create/v2/webhooks/{expo_id}/{webhook_id}")
async def update_webhook(expo_id: str, webhook_id: str, request: Request, body: dict[str, Any] = Body(...)) -> dict[str, Any]:
    await _authenticate(request)
    for webhook in _webhooks:
        if webhook["id"] == webhook_id:
            webhook.update({k: v for k, v in body.items() if k in {"enabled", "url", "type"}})
            _save_state()
            return deepcopy(webhook)
    raise HTTPException(status_code=404, detail="Webhook not found")


@app.delete("/create/v2/webhooks/{expo_id}/{webhook_id}")
async def delete_webhook(expo_id: str, webhook_id: str, request: Request) -> Response:
    await _authenticate(request)
    for index, webhook in enumerate(_webhooks):
        if webhook["id"] == webhook_id:
            _webhooks.pop(index)
            _save_state()
            return Response(status_code=status.HTTP_204_NO_CONTENT)
    raise HTTPException(status_code=404, detail="Webhook not found")
