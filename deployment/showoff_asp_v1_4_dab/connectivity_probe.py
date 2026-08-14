import argparse
import base64
import socket
import ssl
import urllib.parse
import urllib.request


def request(url: str, headers: dict[str, str], method: str = "GET") -> tuple[int, str]:
    req = urllib.request.Request(url, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=30, context=ssl.create_default_context()) as response:
        return response.status, response.read().decode("utf-8")[:500]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True); parser.add_argument("--api-key", required=True); parser.add_argument("--api-secret", required=True)
    args = parser.parse_args(); base = args.base_url.rstrip("/"); host = urllib.parse.urlparse(base).hostname
    print(f"DNS_OK host={host} addresses={socket.gethostbyname_ex(host)[2]}")
    status, body = request(f"{base}/health", {}); print(f"HEALTH status={status} body={body}")
    basic = base64.b64encode(f"{args.api_key}:{args.api_secret}".encode()).decode()
    status, token = request(f"{base}/public/token", {"Authorization": f"Basic {basic}"}, "POST"); print(f"TOKEN status={status} body={token}")
    status, body = request(f"{base}/public/visitors?O=0&L=1", {"Authorization": f"Bearer {token.strip(chr(34))}"}); print(f"VISITORS status={status} body={body}")
    if status != 200: raise SystemExit("ShowOff API probe failed")
    print("PROBE_OK")


if __name__ == "__main__": main()
