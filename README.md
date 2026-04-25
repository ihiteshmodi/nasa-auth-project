# NASA Auth + Scope API (FastAPI)

![Build](https://img.shields.io/badge/build-passing-brightgreen)
![Tests](https://img.shields.io/badge/tests-36%20passed-brightgreen)
![License](https://img.shields.io/badge/license-not%20specified-lightgrey)

> A FastAPI sample app for NASA data APIs with JWT auth, basic vs premium scopes, daily caching, retry handling, structured logging, and optional OpenTelemetry tracing.

## What This App Does

- Serves NASA endpoints with a mixed model of cached and non-cached APIs.
- Enforces authentication and authorization scopes:
	- `basic`: cached APIs only
	- `premium`: cached + non-cached APIs
- Requires `api_key` query param even when user auth is valid.
- Supports resilient upstream calls with retry/backoff for transient failures.
- Supports structured JSON logs with request correlation ID.
- Supports OpenTelemetry tracing when enabled.

## Quick Start

```bash
git clone <your-repo-url>
cd nasa-auth-project
uv sync && uv run uvicorn main:app --reload
```

If your network requires a custom CA bundle, export `SSL_CERT_FILE` before `uv` commands.

Verify:

```bash
curl http://127.0.0.1:8000/health
# Expected: {"status":"ok"}
```

Open docs:

- Swagger UI: http://127.0.0.1:8000/docs

## Demo Credentials (Sample App)

These are intentionally published for demo/testing use in this sample project:

- Basic user:
	- username: `basic_user`
	- password: `basic_password`
- Premium user:
	- username: `premium_user`
	- password: `premium_password`

## Usage Examples

### 1. Login and get token

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/login \
	-H "Content-Type: application/json" \
	-d '{"username":"premium_user","password":"premium_password"}'

# Expected: {"access_token":"...","token_type":"bearer"}
```

### 2. Call a premium (non-cached) endpoint

```bash
TOKEN="<paste_access_token_here>"

curl "http://127.0.0.1:8000/api/v1/nasa/eonet/events?api_key=DEMO_KEY" \
	-H "Authorization: Bearer ${TOKEN}"

# Expected response includes:
# {"source":"EONET","nocache":true,"data":{...}}
```

### 3. Call a cached endpoint (basic or premium)

```bash
TOKEN="<paste_access_token_here>"

curl "http://127.0.0.1:8000/api/v1/nasa/asteroids/feed?api_key=DEMO_KEY" \
	-H "Authorization: Bearer ${TOKEN}" -i

# Expected headers include:
# X-Cache-Status: HIT or MISS
# X-Data-Source: cache or upstream
```

## OpenTelemetry + Jaeger (Optional)

Tracing is feature-gated. It initializes only when `OPENTELEMETRY_TRACING=true`.

Start Jaeger:

```bash
docker compose up -d
```

Stop Jaeger:

```bash
docker compose down
```

Jaeger UI:

- http://localhost:16686

Recommended tracing env vars:

```bash
export OPENTELEMETRY_TRACING=true
export OPENTELEMETRY_SERVICE_NAME=nasa-auth-project
export OPENTELEMETRY_OTLP_ENDPOINT=http://localhost:4317
export OPENTELEMETRY_OTLP_INSECURE=true
```

## Configuration

Set values using environment variables.

| Variable | Description | Default | Required |
|---|---|---|---|
| `NASA_API_KEY` | Fallback NASA API key if query key not provided | empty | No |
| `DATABASE_URL` | SQLAlchemy database URL | `sqlite:///./nasa_artifacts.db` | No |
| `APP_ENV` | Runtime environment name | `local` | No |
| `LOG_LEVEL` | Log verbosity | `INFO` | No |
| `LOG_JSON` | Enable JSON structured logs | `true` | No |
| `LOG_SERVICE_NAME` | Service name in logs | `nasa-auth-project` | No |
| `OPENTELEMETRY_TRACING` | Enable tracing instrumentation/export | `false` | No |
| `OPENTELEMETRY_SERVICE_NAME` | Service name in traces | `nasa-auth-project` | No |
| `OPENTELEMETRY_OTLP_ENDPOINT` | OTLP exporter endpoint (gRPC) | `http://localhost:4317` | No |
| `OPENTELEMETRY_OTLP_INSECURE` | Use insecure OTLP transport | `true` | No |
| `JWT_SECRET_KEY` | JWT signing key | `replace-this-in-prod` | No (Yes in real prod) |
| `AUTH_PASSWORD_SALT` | Password hash salt | `nasa-auth-sample-salt` | No |
| `BASIC_USERNAME` | Username mapped to basic scope | `basic_user` | No |
| `PREMIUM_USERNAME` | Username mapped to premium scope | `premium_user` | No |

## API Reference

### Authentication

#### POST `/api/v1/auth/login`
JSON login endpoint.

Request:

```json
{
	"username": "premium_user",
	"password": "premium_password"
}
```

Response `200`:

```json
{
	"access_token": "<jwt>",
	"token_type": "bearer"
}
```

Errors:

- `401`: Invalid credentials

#### POST `/api/v1/auth/token`
OAuth2 password flow endpoint (form-data), used by Swagger Authorize.

### NASA Endpoints

All NASA endpoints require:

- `Authorization: Bearer <token>`
- Query param `api_key`

Non-cached (premium only):

- GET `/api/v1/nasa/donki/notifications`
- GET `/api/v1/nasa/eonet/events`
- GET `/api/v1/nasa/insight/weather`

Cached daily (basic and premium):

- GET `/api/v1/nasa/asteroids/feed`
- GET `/api/v1/nasa/epic/natural`

Common errors:

- `400`: query param `api_key` missing
- `401`: invalid or missing bearer token
- `403`: insufficient scope for endpoint
- `502`: upstream NASA service returned error
- `504`: upstream timeout

## Testing & Quality

This repository implements three concrete testing layers:

1. Basic non-trivial functions: at least 1 test each (unit/integration as appropriate).
2. Feature flags: at least 2 tests per flag (OFF and ON behavior).
3. E2E smoke: one small critical user journey test.

Current test commands:

```bash
uv run pytest -q
```

If your environment needs a custom certificate chain, set `SSL_CERT_FILE` first.

Smoke flow currently validated:

- health check
- login
- protected NASA endpoint access