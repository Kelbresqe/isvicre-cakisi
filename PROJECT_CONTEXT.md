# Project Context

- Project name: `İsviçre Çakısı`
- Repo URL: `https://github.com/Kelbresqe/isvicre-cakisi`
- Local path: `/Users/kelbresqe/isvicre-cakisi`
- Current app version: `1.2.0` (README badge)
- Runtime target: Python `3.13+`

## Service endpoints

- Local: `http://localhost:8000`
- Local IPv4 fallback: `http://127.0.0.1:8000`
- Local IPv6 fallback: `http://[::1]:8000`
- Public: `https://caki.golgediyar.com`
- Health endpoints verified: `/health`, `/ready`

## Runtime / infrastructure

- Local container/runtime: OrbStack
- Public tunnel: cloudflared
- Public hostname `caki.golgediyar.com` is routed through cloudflared to the local OrbStack app container on port 8000.
- The cloudflared tunnel configuration is system-level/external and is not stored in this repo.

## Host-header and CORS policy

The app uses TrustedHostMiddleware. Local and public access require the following host/origin values to be present in runtime configuration:

```text
TRUSTED_HOSTS=["localhost","127.0.0.1","testserver","caki.golgediyar.com"]
CORS_ORIGINS=["http://localhost:3000","http://localhost:8000","https://caki.golgediyar.com"]
```

Development mode also appends loopback hosts for local access:

```text
localhost
127.0.0.1
::1
[::1]
```

If `https://caki.golgediyar.com` returns `Invalid host header`, check that `caki.golgediyar.com` is present in `TRUSTED_HOSTS`, then recreate the app container:

```bash
docker-compose up -d app
```

## Last sync status

- Local access verified: `http://localhost:8000` returns 200.
- IPv4 access verified: `http://127.0.0.1:8000` returns 200.
- IPv6 access verified: `http://[::1]:8000` returns 200.
- Public access verified: `https://caki.golgediyar.com` returns 200.
- Host-header regression root cause was cloudflared/public Host header `caki.golgediyar.com` not being included in container `TRUSTED_HOSTS`.

## Important decisions

- Keep project context short and durable for future Kanban cards.
- Treat public exposure as production-sensitive if the app is running in `dev` mode.
- Do not remove TrustedHostMiddleware to fix local/public routing; add the exact allowed hosts instead.
- After host/CORS env changes in Docker Compose, recreate the app container. A simple code change without container recreation may not update middleware configuration.

## Open risks

- Public service is currently reachable through cloudflared and OrbStack.
- Public service may still run in `ENV=dev`; production hardening should use `ENV=prod`, `DEBUG=false`, `DOCS_ENABLED=false`, `REDOC_ENABLED=false`, strict `TRUSTED_HOSTS`, and restricted observability endpoints.
- cloudflared settings are not documented in-repo, so operational changes may need system-side updates.
