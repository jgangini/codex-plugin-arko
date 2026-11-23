import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.features.notes.api import create_router
from app.features.notes.service import Store

app = FastAPI(title="Arko application", version="0.1.0")
app.add_middleware(TrustedHostMiddleware, allowed_hosts=os.getenv(
    "ARKO_ALLOWED_HOSTS", "localhost,127.0.0.1,testserver"
).split(","))


@app.get("/api/health", operation_id="health")
def health() -> dict[str, str]:
    return {"status": "ok"}


# Mount feature routers here, before the optional static root.
app.include_router(create_router(Store()))
static = Path(os.getenv("ARKO_STATIC_DIR", "frontend/dist"))
if static.is_dir():
    app.mount("/", StaticFiles(directory=static, html=True), name="frontend")
