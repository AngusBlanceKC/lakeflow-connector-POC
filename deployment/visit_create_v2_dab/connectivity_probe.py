"""Minimal Databricks-side HTTPS probe for the Visit Create simulator."""

from __future__ import annotations

import argparse
import base64
import json
import socket
import ssl
import urllib.error
import urllib.request
from urllib.parse import urlparse


def fetch(url: str, api_key: str | None = None) -> tuple[int, str]:
    headers = {"Accept": "application/json"}
    if api_key:
        token = base64.b64encode(f"{api_key}:".encode()).decode()
        headers["Authorization"] = f"Basic {token}"
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=20, context=ssl.create_default_context()) as response:
            return response.status, response.read().decode()
    except urllib.error.HTTPError as error:
        return error.code, error.read().decode()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--api-key", required=True)
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    host = urlparse(base_url).hostname
    if not host:
        print(f"INVALID_URL {base_url}")
        return 2
    try:
        addresses = sorted({item[4][0] for item in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)})
        print(f"DNS_OK host={host} addresses={addresses}")
    except OSError as error:
        print(f"DNS_ERROR host={host} error={error!r}")
        return 1

    api_root_marker = "/create/v2"
    health_base = base_url.removesuffix(api_root_marker)
    for url, path, key in (
        (f"{health_base}/health", "/health", None),
        (f"{base_url}/expos", "/create/v2/expos", args.api_key),
    ):
        try:
            status, body = fetch(url, key)
            print(f"HTTP status={status} path={path} body={body[:1000]}")
            if status >= 400:
                return 1
            if path == "/create/v2/expos":
                parsed = json.loads(body)
                if not isinstance(parsed, list):
                    print(f"INVALID_JSON_SHAPE type={type(parsed).__name__}")
                    return 1
        except (OSError, ValueError, ssl.SSLError) as error:
            print(f"HTTP_ERROR path={path} error={error!r}")
            return 1
    print("PROBE_OK")
    return 0


if __name__ == "__main__":
    main()
