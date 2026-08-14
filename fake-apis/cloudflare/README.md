# Cloudflare Tunnel for the local fake APIs

This directory documents how to expose the local Visit Create v2 simulator to
Databricks through Cloudflare Tunnel. The tunnel process runs on the same
machine as the FastAPI service and forwards a public HTTPS hostname to
`http://127.0.0.1:8000`.

Use a Quick Tunnel for a short-lived test, or a named tunnel for a stable
hostname. Quick Tunnels do not require a Cloudflare account; named tunnels use
the Cloudflare browser login and a domain managed in the account.

## Prerequisites

On macOS:

```bash
brew install cloudflared
cloudflared --version
```

Start the simulator first:

```bash
cd fake-apis/visit-create-v2
VISIT_API_KEY='use-a-strong-test-key' .venv/bin/uvicorn app:app --host 127.0.0.1 --port 8000
```

## Fast temporary tunnel

This is the quickest Databricks connectivity test:

```bash
cloudflared tunnel --url http://127.0.0.1:8000
```

Copy the generated `https://*.trycloudflare.com` URL and append
`/create/v2` for the connector `base_url`. Keep this terminal running. The
URL changes when the process stops and Quick Tunnels are intended for testing,
not production.

## Stable named tunnel

1. Log in through the browser:

   ```bash
   cloudflared tunnel login
   ```

2. Create a tunnel:

   ```bash
   cloudflared tunnel create visit-create-v2
   cloudflared tunnel list
   ```

   Save the tunnel UUID printed by the command. Cloudflare stores the tunnel
   credentials under `~/.cloudflared/`; do not commit that directory.

3. Copy [`config.example.yml`](./config.example.yml) to
   `~/.cloudflared/config.yml`, replacing `<TUNNEL_UUID>` and
   `<api.example.com>` with your values.

4. Create the DNS route:

   ```bash
   cloudflared tunnel route dns visit-create-v2 api.example.com
   ```

5. Run it:

   ```bash
   cloudflared tunnel --config ~/.cloudflared/config.yml run visit-create-v2
   ```

The connector URL will be:
`https://api.example.com/create/v2`.

## Databricks connector settings

Use these values in the Visit Create v2 Unity Catalog connection:

```text
base_url = https://api.example.com/create/v2
api_key = <the value used for VISIT_API_KEY>
expo_id = 0rwwipz7fufs1
```

If Databricks serverless egress is restricted, allowlist the tunnel hostname
in the workspace network policy. Never expose the simulator with the default
`demo-api-key` beyond a short local test.

## Reset and security notes

- The FastAPI service persists data in
  `fake-apis/visit-create-v2/data/visit-create-v2.json`.
- A tunnel exposes the API to the internet; use a strong key and rotate it
  after testing.
- Tunnel credentials live outside this repository in `~/.cloudflared/`.
- Delete the local JSON data file only when you intentionally want to reset the
  simulator state.

References: [Cloudflare Quick Tunnels](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/do-more-with-tunnels/trycloudflare/), [Cloudflare Tunnel setup](https://developers.cloudflare.com/tunnel/setup/), and [Databricks serverless egress controls](https://docs.databricks.com/aws/en/security/network/serverless-network-security/network-policies).
