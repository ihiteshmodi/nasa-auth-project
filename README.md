### Readme will be updated at later stages, Where more details about usage of the product is present. Creatin an intial sample readme for now.

## This is an individual project so all commits will be made directly to the main, we wont be utilizing branching here.

## OpenTelemetry + Jaeger (Optional)

Tracing is fully feature-gated and only runs when OPENTELEMETRY_TRACING is true.

### Start Jaeger

Start Jaeger with Docker Compose:

docker compose up -d

Stop Jaeger:

docker compose down

Jaeger UI: http://localhost:16686

### Environment variables

Set these before running the API:

OPENTELEMETRY_TRACING=true
OPENTELEMETRY_SERVICE_NAME=nasa-auth-project
OPENTELEMETRY_OTLP_ENDPOINT=http://localhost:4317
OPENTELEMETRY_OTLP_INSECURE=true

When OPENTELEMETRY_TRACING=false (default), no tracing instrumentation/exporter is initialized.