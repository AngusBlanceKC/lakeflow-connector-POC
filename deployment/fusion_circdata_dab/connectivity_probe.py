"""Databricks-side DNS/HTTPS/auth probe for the Fusion simulator."""

import base64
import argparse
import json
import socket
import ssl
import urllib.parse
import urllib.request


def request(url: str, headers: dict[str, str]) -> tuple[int, str]:
    req = urllib.request.Request(url, headers=headers)
    context = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=30, context=context) as response:
        return response.status, response.read().decode("utf-8")[:500]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--event-id", required=True)
    parser.add_argument("--username", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--install-name", required=True)
    parser.add_argument("--api-key", required=True)
    args = parser.parse_args()
    base_url = args.base_url.rstrip("/")
    event_id = args.event_id
    parsed = urllib.parse.urlparse(base_url)
    print(f"DNS_OK host={parsed.hostname} addresses={socket.gethostbyname_ex(parsed.hostname)[2]}")
    auth = base64.b64encode(f"{args.username}:{args.password}".encode()).decode()
    headers = {"Authorization": f"Basic {auth}", "X-Fusion-Install-Name": args.install_name, "X-Fusion-API-Key": args.api_key}
    status, body = request(f"{base_url}/health", {})
    print(f"HEALTH status={status} body={body}")
    status, body = request(f"{base_url}/People?eventId={urllib.parse.quote(event_id)}&limit=1", headers)
    print(f"PEOPLE status={status} body={body}")
    if status != 200:
        raise SystemExit("Fusion API probe failed")
    print("PROBE_OK")


if __name__ == "__main__":
    main()
