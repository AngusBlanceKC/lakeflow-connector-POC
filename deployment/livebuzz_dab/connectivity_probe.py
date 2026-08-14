import argparse
import json
import urllib.request


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--campaign", required=True)
    parser.add_argument("--api-key", required=True)
    args = parser.parse_args()
    base = args.base_url.rstrip("/")
    with urllib.request.urlopen(f"{base}/health", timeout=20) as response:
        print(json.dumps({"status": response.status, "body": response.read().decode()}))
    request = urllib.request.Request(
        f"{base}/campaign/{args.campaign}/api/exhibitors?limit=1&offset=0",
        headers={"X-API-Key": args.api_key},
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        print(
            json.dumps(
                {"status": response.status, "body": response.read().decode()[:500]}
            )
        )
    print("PROBE_OK")


if __name__ == "__main__":
    main()
