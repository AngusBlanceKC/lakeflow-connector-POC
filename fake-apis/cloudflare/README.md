# Cloudflare Tunnel for the local fake APIs

This directory documents how to expose all six local FastAPI simulators to
Databricks through one Cloudflare Tunnel. The tunnel process runs on the same
machine as the services and forwards one public HTTPS hostname to the local
path gateway:

| API | Local service | Public path |
| --- | --- | --- |
| Visit Create v2 | `127.0.0.1:8100` | `/visit-create` |
| Fusion/Circdata | `127.0.0.1:8010` | `/fusion` |
| GEVME | `127.0.0.1:8020` | `/gevme` |
| FairVerify Ticketdata v2 | `127.0.0.1:8030` | `/fairverify` |
| ShowOff ASP v1.4 | `127.0.0.1:8040` | `/showoff` |
| LiveBuzz | `127.0.0.1:8050` | `/livebuzz` |

Run [`run_all.sh`](run_all.sh) to start all six services. Fusion uses port
`8010` in this combined setup so it does not conflict with Visit Create on
port `8000`.

Use a Quick Tunnel for a short-lived test, or a named tunnel for a stable
hostname. Quick Tunnels do not require a Cloudflare account; named tunnels use
the Cloudflare browser login and a domain managed in the account.

## Prerequisites

On macOS:

```bash
brew install cloudflared
cloudflared --version
```

Start all simulators first:

```bash
./fake-apis/cloudflare/run_all.sh
```

## Fast temporary tunnel

This is the quickest Databricks connectivity test:

```bash
cloudflared tunnel --url http://127.0.0.1:8000
```

### Current public URL

The currently running Quick Tunnel is:

https://<cloudflareURL>

Set the shared shell variable once and use it for every API:

```bash
export CLOUDFLARE_URL="https://<cloudflareURL>"
```

Routes through the shared gateway are `/visit-create`, `/fusion`, `/gevme`,
`/fairverify`, `/showoff`, and `/livebuzz`.

This URL is temporary and changes when the Quick Tunnel process restarts.

In this repository, `<cloudflareURL>` means the hostname printed by
`cloudflared`, without `https://` and without an API route suffix. For example,
the FairVerify URL is `https://<cloudflareURL>/fairverify`.

Copy the generated `https://*.trycloudflare.com` URL and append
`/visit-create/create/v2` for the Visit Create connector `base_url`. Keep this
terminal running. The URL changes when the process stops and Quick Tunnels are
intended for testing, not production.

To expose every API without buying a domain, use one Quick Tunnel for the
gateway:

```bash
./fake-apis/cloudflare/run_quick_tunnels.sh
```

The script starts all six APIs, the gateway, and one temporary tunnel. Use the
single generated URL with the path shown in the table above. Keep the script
running while Databricks jobs execute.

After `run_quick_tunnels.sh` has started, retrieve the generated URL with:

```bash
export CLOUDFLARE_URL="$(find "${TMPDIR:-/tmp}/fake-api-cloudflare-logs" -type f -name '*.tunnel.log' -exec rg -o 'https://[[:alnum:]-]+\.trycloudflare\.com' {} + 2>/dev/null | tail -1)"
echo "${CLOUDFLARE_URL}"
```

Use `${CLOUDFLARE_URL}` in the API URLs below. For example, the FairVerify
endpoint is `${CLOUDFLARE_URL}/fairverify`.

For a manually started tunnel, save its output first and extract the URL:

```bash
cloudflared tunnel --url http://127.0.0.1:8000 2>&1 | tee /tmp/fake-api-cloudflare.log
export CLOUDFLARE_URL="$(rg -o 'https://[[:alnum:]-]+\.trycloudflare\.com' /tmp/fake-api-cloudflare.log | tail -1)"
```

If you started the tunnel in another terminal without saving its output, set
the current value directly:

```bash
export CLOUDFLARE_URL="https://navy-affordable-devoted-gathered.trycloudflare.com"
```

## Stable named tunnel for all APIs

1. Log in through the browser:

   ```bash
   cloudflared tunnel login
   ```

2. Create a tunnel:

   ```bash
   cloudflared tunnel create fake-apis
   cloudflared tunnel list
   ```

   Save the tunnel UUID printed by the command. Cloudflare stores the tunnel
   credentials under `~/.cloudflared/`; do not commit that directory.

3. Copy [`config.example.yml`](./config.example.yml) to
   `~/.cloudflared/config.yml`, replacing `<TUNNEL_UUID>` and
   `<api.example.com>` with your values.

4. Create the single DNS route:

   ```bash
   cloudflared tunnel route dns fake-apis api.example.com
   ```

5. Run it:

   ```bash
   cloudflared tunnel --config ~/.cloudflared/config.yml run fake-apis
   ```

The connector base URLs will share one hostname and use different paths:

```text
Visit Create: ${CLOUDFLARE_URL}/visit-create/create/v2
Fusion:       ${CLOUDFLARE_URL}/fusion
GEVME:        ${CLOUDFLARE_URL}/gevme
FairVerify:   ${CLOUDFLARE_URL}/fairverify
ShowOff:      ${CLOUDFLARE_URL}/showoff
LiveBuzz:     ${CLOUDFLARE_URL}/livebuzz
```

Replace `example.com` with a domain managed in your Cloudflare account. A
named tunnel cannot provide permanent custom hostnames without a domain.

## Databricks connector settings

Use the matching public hostname in each Unity Catalog connection or DAB
`base_url` variable. For example, Visit Create uses:

```text
base_url = https://api.example.com/visit-create/create/v2
api_key = <the value used for VISIT_API_KEY>
expo_id = 0rwwipz7fufs1
```

If Databricks serverless egress is restricted, allowlist the tunnel hostname
in the workspace network policy. Never expose the simulator with the default
`demo-api-key` beyond a short local test.

## Reset and security notes

- The FastAPI services persist data in their individual `data/*.json` files.
- A tunnel exposes the API to the internet; use a strong key and rotate it
  after testing.
- Tunnel credentials live outside this repository in `~/.cloudflared/`.
- Delete the local JSON data file only when you intentionally want to reset the
  simulator state.

References: [Cloudflare Quick Tunnels](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/do-more-with-tunnels/trycloudflare/), [Cloudflare Tunnel setup](https://developers.cloudflare.com/tunnel/setup/), and [Databricks serverless egress controls](https://docs.databricks.com/aws/en/security/network/serverless-network-security/network-policies).
