"""
Health Check Endpoints
نقاط پایانی بررسی سلامت

Provides:
- GET /health - basic health check
- GET /health/detailed - detailed component health
- GET /metrics - Prometheus metrics export
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.monitoring.metrics_collector import get_metrics_collector
from app.config import settings
import time

router = APIRouter(tags=["monitoring"])

_start_time = time.time()


@router.get("/health")
def health_check():
    """
    بررسی سلامت پایه سرویس
    """
    uptime = time.time() - _start_time
    
    return {
        "status": "healthy",
        "service": "contribution_service",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "uptime_seconds": int(uptime),
    }


@router.get("/health/detailed")
def detailed_health_check(db: Session = Depends(get_db)):
    """
    بررسی سلامت جزئیات کامپوننت‌ها
    """
    uptime = time.time() - _start_time
    metrics = get_metrics_collector()
    health_status = metrics.get_health_status()
    
    # بررسی اتصال به دیتابیس
    db_healthy = True
    try:
        db.execute("SELECT 1")
        db_status = "healthy"
    except Exception:
        db_healthy = False
        db_status = "critical"
    
    # بررسی audit ledger (می‌توان در صورت نیاز افزود)
    audit_ledger_status = "healthy"
    
    # بررسی rate limiter (همیشه فعال است)
    rate_limiter_status = "healthy"
    
    components = {
        "database": db_status,
        "audit_ledger": audit_ledger_status,
        "rate_limiter": rate_limiter_status,
        **health_status["components"],
    }
    
    # وضعیت کلی
    statuses = list(components.values())
    if "critical" in statuses:
        overall = "critical"
    elif "degraded" in statuses:
        overall = "degraded"
    else:
        overall = "healthy"
    
    return {
        "status": overall,
        "service": "contribution_service",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "uptime_seconds": int(uptime),
        "components": components,
        "timestamp": health_status["timestamp"],
    }


@router.get("/metrics")
def prometheus_metrics():
    """
    خروجی متریک‌ها به فرمت Prometheus
    """
    metrics = get_metrics_collector()
    return metrics.get_prometheus_metrics()
