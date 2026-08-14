"""Databricks-side DNS/HTTPS/auth probe for the GEVME simulator."""

import argparse
import json
import socket
import ssl
import urllib.parse
import urllib.request


def request(url: str, headers: dict[str, str]) -> tuple[int, str]:
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30, context=ssl.create_default_context()) as response:
        return response.status, response.read().decode("utf-8")[:500]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--event-id", required=True)
    parser.add_argument("--access-token", required=True)
    args = parser.parse_args()
    base_url = args.base_url.rstrip("/")
    host = urllib.parse.urlparse(base_url).hostname
    print(f"DNS_OK host={host} addresses={socket.gethostbyname_ex(host)[2]}")
    status, body = request(f"{base_url}/health", {})
    print(f"HEALTH status={status} body={body}")
    headers = {"Authorization": f"Bearer {args.access_token}"}
    url = f"{base_url}/apiv2/api/events/{urllib.parse.quote(args.event_id)}/attendees?limit=1"
    status, body = request(url, headers)
    print(f"ATTENDEES status={status} body={body}")
    if status != 200:
        raise SystemExit("GEVME API probe failed")
    json.loads(body)
    print("PROBE_OK")


if __name__ == "__main__":
    main()
