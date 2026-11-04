"""
Monitoring System for Contribution Service
سیستم مانیتورینگ سرویس مشارکت حقوقی

Provides:
- Alert management with deduplication and lifecycle
- Statistical anomaly detection (Z-score + IQR)
- Rolling statistics calculation
- Contribution-specific metrics collection
- Health checks and Prometheus export
- Diagnostic report generation
- Data retention policies
- Behavioral monitoring for abuse detection
"""

from app.monitoring.alerting import (
    AlertSeverity,
    AlertChannel,
    Alert,
    AlertingSystem,
)
from app.monitoring.anomaly_detector import (
    AnomalyAlert,
    AnomalyDetector,
)
from app.monitoring.rolling_stats import (
    RollingStats,
    RollingStatsCalculator,
)
from app.monitoring.metrics_collector import (
    ContributionMetricsCollector,
    get_metrics_collector,
)

__all__ = [
    "AlertSeverity",
    "AlertChannel",
    "Alert",
    "AlertingSystem",
    "AnomalyAlert",
    "AnomalyDetector",
    "RollingStats",
    "RollingStatsCalculator",
    "ContributionMetricsCollector",
    "get_metrics_collector",
]
