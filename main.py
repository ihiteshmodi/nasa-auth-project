import os
import uvicorn

# Toggle tracing from this file for local runs.
ENABLE_OPENTELEMETRY = True

os.environ.setdefault("OPENTELEMETRY_TRACING", "true" if ENABLE_OPENTELEMETRY else "false")
os.environ.setdefault("OPENTELEMETRY_SERVICE_NAME", "nasa-auth-project")
os.environ.setdefault("OPENTELEMETRY_OTLP_ENDPOINT", "http://localhost:4317")
os.environ.setdefault("OPENTELEMETRY_OTLP_INSECURE", "true")

from app.interfaces.main import app


def main():
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
