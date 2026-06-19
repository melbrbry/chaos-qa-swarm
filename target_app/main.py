"""FastAPI application entrypoint."""

from fastapi import FastAPI

from target_app.routes import items, loyalty, prorate, report, users

app = FastAPI(
  title="Chaos QA Swarm Target API",
  description="Internal business operations API",
  version="0.1.0",
)

app.include_router(items.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(report.router, prefix="/api")
app.include_router(prorate.router, prefix="/api")
app.include_router(loyalty.router, prefix="/api")


@app.get("/health")
def health() -> dict[str, str]:
  """Health check endpoint."""
  return {"status": "ok"}
