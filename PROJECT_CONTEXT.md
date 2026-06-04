# Project Context

- Repo URL: `https://github.com/Kelbresqe/isvicre-cakisi.git`
- Local path: `/Users/kelbresqe/isvicre-cakisi`
- Current app version: `1.2.0` (README badge)
- Runtime target: Python `3.13+`

## Service endpoints
- Local: `http://localhost:8000`
- Public: `https://caki.golgediyar.com`
- Health endpoints verified: `/health`, `/ready`
- Docs endpoint: `/docs`
- Metrics endpoint: `/metrics`

## Infra notes
- OrbStack is the active local container/runtime environment for the project.
- cloudflared tunnel is in use for the public hostname, but no tunnel config was found in the repo; configuration appears to be system-level/external.

## Last sync status
- Local install and quality gates completed successfully.
- Local and public smoke tests passed.
- No code changes were required; repository remained clean.
- Both local and public traffic currently reached the same running container during verification.

## Important decisions
- Keep the project context note short and durable for future cards.
- Treat public exposure as production-sensitive if the app is running in `dev` mode.

## Open risks
- Public `/docs`, `/metrics`, and `/ready` were reachable during verification and should be restricted or disabled for production use.
- Public service was observed in `environment: "dev"`; this is a release risk.
- cloudflared settings are not documented in-repo, so operational changes may need system-side updates.

## Verification results
- Local `/health`: PASS
- Local `/ready`: PASS
- Public `/health`: PASS
- Public `/ready`: PASS
- Public `/docs`: reachable
- Public `/metrics`: reachable

## Suggested next step
- Switch the public deployment to production-safe env values: `ENV=prod`, `DEBUG=false`, `DOCS_ENABLED=false`, `REDOC_ENABLED=false`, and restricted trusted host / CORS settings.
