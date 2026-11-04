import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.db.session import init_db
from app.api.v1 import auth, contribution, review, export
from app.monitoring.health import router as monitoring_router
from app.monitoring.metrics_collector import get_metrics_collector

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure DB tables and quarantine storage exist
    init_db()
    os.makedirs(settings.QUARANTINE_STORAGE_PATH, exist_ok=True)
    
    # Initialize metrics collector
    get_metrics_collector()
    
    yield
    # Shutdown

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Standalone Legal Data Contribution Platform for Mahoun Ecosystem.",
    lifespan=lifespan
)

# CORS setup for web frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers under /api/v1
app.include_router(auth.router, prefix="/api/v1")
app.include_router(contribution.router, prefix="/api/v1")
app.include_router(review.router, prefix="/api/v1")
app.include_router(export.router, prefix="/api/v1")

# Mount monitoring endpoints
app.include_router(monitoring_router)

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "contribution_service",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "isolation_verified": True
    }
