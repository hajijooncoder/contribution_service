"""
Diagnostic Report Generator
تولید گزارش‌های تشخیصی

Provides:
- Anomaly-triggered diagnostic reports
- Root cause analysis
- Actionable recommendations
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List
from uuid import uuid4

from app.monitoring.anomaly_detector import AnomalyAlert


@dataclass
class DiagnosticReport:
    """
    گزارش تشخیصی با ریشه‌یابی و توصیه‌های عملیاتی
    """
    report_id: str
    timestamp: datetime
    trigger: str  # "anomaly", "threshold", "manual"
    severity: str  # "high", "medium", "low"
    affected_metrics: List[str]
    summary: str
    details: Dict
    recommendations: List[str] = field(default_factory=list)


class DiagnosticReportGenerator:
    """
    تولیدکننده گزارش‌های تشخیصی با تحلیل علت ریشه‌ای
    
    بر اساس ناهنجاری‌های آماری، توصیه‌های عملیاتی ارائه می‌دهد
    """
    
    def __init__(self):
        self._metric_recommendations = {
            "submission": [
                "بررسی لاگ‌های خطای سرور",
                "بررسی ظرفیت دیتابیس",
                "بررسی rate limiting و IP blocking",
            ],
            "duplicate": [
                "بررسی آستانه‌های تشخیص تکراری",
                "بررسی کیفیت داده‌های ورودی",
                "بررسی الگوریتم SimHash",
            ],
            "review": [
                "بررسی تعداد reviewer فعال",
                "بررسی قوانین FSM و quorum",
                "بررسی توزیع بار کاری reviewers",
            ],
            "quality": [
                "بررسی فرآیند text enhancement",
                "بررسی قوانین scoring",
                "بررسی منابع داده ورودی",
            ],
            "audit": [
                "بررسی یکپارچگی hash chain",
                "بررسی فضای ذخیره‌سازی",
                "بررسی کلید HMAC",
            ],
            "rate_limit": [
                "بررسی الگوهای ترافیک",
                "بررسی لیست IP مشکوک",
                "تنظیم rate limit windows",
            ],
        }
    
    def _identify_metric_category(self, metric_name: str) -> str:
        """شناسایی دسته متریک"""
        metric_lower = metric_name.lower()
        
        if "submission" in metric_lower:
            return "submission"
        elif "duplicate" in metric_lower:
            return "duplicate"
        elif "review" in metric_lower:
            return "review"
        elif "quality" in metric_lower:
            return "quality"
        elif "audit" in metric_lower:
            return "audit"
        elif "rate" in metric_lower:
            return "rate_limit"
        else:
            return "unknown"
    
    def generate_report(
        self,
        trigger: str,
        anomaly_alerts: List[AnomalyAlert]
    ) -> DiagnosticReport:
        """
        تولید گزارش تشخیصی از ناهنجاری‌ها
        
        Args:
            trigger: دلیل تریگر شدن گزارش
            anomaly_alerts: لیست ناهنجاری‌های تشخیص داده شده
        
        Returns:
            گزارش تشخیصی کامل
        """
        if not anomaly_alerts:
            return DiagnosticReport(
                report_id=str(uuid4()),
                timestamp=datetime.now(timezone.utc),
                trigger=trigger,
                severity="low",
                affected_metrics=[],
                summary="هیچ ناهنجاری تشخیص داده نشد",
                details={},
                recommendations=[]
            )
        
        # تجمیع اطلاعات
        affected_metrics = [alert.metric_name for alert in anomaly_alerts]
        severities = [alert.severity for alert in anomaly_alerts]
        
        # تعیین شدت کلی
        if "high" in severities:
            overall_severity = "high"
        elif "medium" in severities:
            overall_severity = "medium"
        else:
            overall_severity = "low"
        
        # تولید خلاصه
        summary = f"{len(anomaly_alerts)} ناهنجاری تشخیص داده شد در متریک‌های: {', '.join(set(affected_metrics))}"
        
        # جزئیات
        details = {
            "anomalies": [
                {
                    "metric": alert.metric_name,
                    "current_value": alert.current_value,
                    "expected_range": alert.expected_range,
                    "severity": alert.severity,
                    "z_score": alert.z_score,
                    "message": alert.message,
                }
                for alert in anomaly_alerts
            ]
        }
        
        # تولید توصیه‌ها
        recommendations = []
        categories_seen = set()
        
        for alert in anomaly_alerts:
            category = self._identify_metric_category(alert.metric_name)
            if category in self._metric_recommendations and category not in categories_seen:
                recommendations.extend(self._metric_recommendations[category])
                categories_seen.add(category)
        
        # توصیه‌های عمومی
        if overall_severity == "high":
            recommendations.insert(0, "اقدام فوری: بررسی لاگ‌های سیستم و مشاوره با تیم عملیات")
        
        return DiagnosticReport(
            report_id=str(uuid4()),
            timestamp=datetime.now(timezone.utc),
            trigger=trigger,
            severity=overall_severity,
            affected_metrics=affected_metrics,
            summary=summary,
            details=details,
            recommendations=recommendations
        )
