import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import settings
from app.db.session import init_db
from app.api.v1 import auth, contribution, review, export, admin, ws
from app.monitoring.health import router as monitoring_router
from app.monitoring.metrics_collector import get_metrics_collector
from app.core.exceptions import ContributionError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    os.makedirs(settings.QUARANTINE_STORAGE_PATH, exist_ok=True)
    get_metrics_collector()
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Standalone Legal Data Contribution Platform for Mahoun Ecosystem.",
    lifespan=lifespan
)

allow_origins = [settings.FRONTEND_URL] if settings.FRONTEND_URL else []
if settings.ENVIRONMENT == "development":
    allow_origins.extend(["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Gateway-Token", "X-CSRF-Token"],
    expose_headers=["X-Content-SHA256", "X-Original-Filename"],
)

@app.exception_handler(ContributionError)
async def contribution_error_handler(request: Request, exc: ContributionError):
    logger.warning(f"ContributionError: {exc.code} - {exc.message}", extra={"path": request.url.path, "extra": exc.extra})
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message, **exc.extra}, "detail": exc.message}
    )

@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception: {exc}", extra={"path": request.url.path})
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "INTERNAL_ERROR", "message": "Internal server error"}}
    )

app.include_router(auth.router, prefix="/api/v1")
app.include_router(contribution.router, prefix="/api/v1")
app.include_router(review.router, prefix="/api/v1")
app.include_router(export.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(ws.router, prefix="/api/v1")

app.include_router(monitoring_router)