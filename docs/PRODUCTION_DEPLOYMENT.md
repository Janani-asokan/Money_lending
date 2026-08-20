# Production deployment and availability

Run the live application on an always-on Linux host or managed container platform. A developer laptop and Docker Desktop are not production infrastructure.

## Stack

- `gateway`: public entry point; routes `/api` to FastAPI and other requests to React.
- `frontend`: Nginx serving the immutable Vite build.
- `backend`: non-root FastAPI container with health checks and graceful shutdown.
- `mongodb`: authenticated persistent replica-set member.
- Long-running services use `restart: unless-stopped`.
- Upstream 502/503/504 failures become a friendly 503 response with `Retry-After`.

The included single-host MongoDB is durable but not highly available. Live lending should use a managed multi-zone MongoDB replica set.

## Start production

1. Copy `.env.production.example` to `.env.production` and replace every `CHANGE_ME`.
2. Configure `server/.env` with production-only application, Aadhaar, audit and backup keys. Never commit environment files.
3. Run:

   ```powershell
   docker compose --env-file .env.production -f compose.production.yml up -d --build
   powershell -ExecutionPolicy Bypass -File scripts/verify-production-stack.ps1
   ```

4. Put a managed HTTPS load balancer in front of port 8080. Only that load balancer should be publicly accessible.

## Start isolated staging

```powershell
Copy-Item .env.staging.example .env.staging
docker compose -p money_lending_staging --env-file .env.staging -f compose.production.yml -f compose.staging.yml up -d --build
```

Staging must use different secrets and synthetic data—never real customer or Aadhaar records.

## Availability

For two API processes on one host:

```powershell
docker compose --env-file .env.production -f compose.production.yml up -d --scale backend=2
```

This handles one API process crashing, not host/power/network failure. True availability needs two hosts or a managed container service and a multi-zone database.

## External monitoring

Configure a monitor outside the production host to request these every minute:

- `https://YOUR_DOMAIN/gateway-health`
- `https://YOUR_DOMAIN/api/health`

Alert the owner and support team after two failures. Also monitor HTTP 5xx rate, latency, disk, container restarts, TLS expiry and backup age. The client must own the monitoring account and notification recipients.

## Required restart drill

1. Create test customer and payment records.
2. Restart the backend and confirm records remain.
3. Restart the complete stack and confirm records remain.
4. Reboot the host and confirm the container engine starts automatically.
5. Stop the backend and confirm users receive the maintenance response.
6. Restore the newest encrypted backup into an isolated database and reconcile record and ledger totals.

Do not approve go-live until all six checks pass and evidence is retained.
