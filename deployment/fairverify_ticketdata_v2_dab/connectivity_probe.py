import argparse
import json
import socket
import ssl
import urllib.parse
import urllib.request


def get(url: str, headers: dict[str, str]) -> tuple[int, str]:
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=30, context=ssl.create_default_context()) as response:
        return response.status, response.read().decode("utf-8")[:500]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--event-id", required=True)
    parser.add_argument("--api-key", required=True)
    args = parser.parse_args()
    base = args.base_url.rstrip("/")
    host = urllib.parse.urlparse(base).hostname
    print(f"DNS_OK host={host} addresses={socket.gethostbyname_ex(host)[2]}")
    status, body = get(f"{base}/health", {})
    print(f"HEALTH status={status} body={body}")
    path = f"{base}/api/v2/events/{urllib.parse.quote(args.event_id)}/tickets?limit=1"
    status, body = get(path, {"X-FairVerify-API-Key": args.api_key})
    print(f"TICKETS status={status} body={body}")
    if status != 200:
        raise SystemExit("FairVerify API probe failed")
    json.loads(body)
    print("PROBE_OK")


if __name__ == "__main__":
    main()
