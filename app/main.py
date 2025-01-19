from fastapi import FastAPI

from app.routers import event
from app.utils import health_check

app = FastAPI(
    title="Midnite API",
    description="Midnite API",
    version="1.0.0",
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.include_router(health_check.router)
app.include_router(event.router)
