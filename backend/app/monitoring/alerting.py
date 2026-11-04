"""
Alert Management System
سیستم مدیریت هشدارها

Provides:
- Alert severity levels (CRITICAL, ERROR, WARNING, INFO)
- Alert channels (WEBHOOK, EMAIL, SLACK - stub implementations)
- Alert deduplication via dedup_key hashing
- Alert lifecycle (create → acknowledge → resolve → suppress)
- Rate limiting per source
- Thread-safe in-memory storage
"""

import hashlib
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from threading import RLock
from typing import Dict, List, Optional
from uuid import uuid4


class AlertSeverity(Enum):
    """سطح شدت هشدار"""
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class AlertChannel(Enum):
    """کانال ارسال هشدار"""
    WEBHOOK = "webhook"
    EMAIL = "email"
    SLACK = "slack"


class AlertStatus(Enum):
    """وضعیت چرخه عمر هشدار"""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


@dataclass
class Alert:
    """
    هشدار سیستمی با قابلیت ردیابی چرخه عمر
    """
    id: str
    title: str
    description: str
    severity: AlertSeverity
    source: str
    timestamp: datetime
    metadata: Dict = field(default_factory=dict)
    dedup_key: str = ""
    status: AlertStatus = AlertStatus.ACTIVE
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    suppressed_until: Optional[datetime] = None


class AlertingSystem:
    """
    سیستم مدیریت هشدارها با قابلیت‌های:
    - ذخیره‌سازی حافظه‌ای thread-safe
    - جلوگیری از تکرار هشدارها (deduplication)
    - محدودسازی نرخ ارسال (rate limiting)
    - چرخه عمر هشدار (lifecycle management)
    """
    
    def __init__(
        self,
        rate_limit_per_source: int = 10,
        rate_limit_window_seconds: int = 60
    ):
        self._lock = RLock()
        self._alerts: Dict[str, Alert] = {}
        self._dedup_map: Dict[str, str] = {}  # dedup_key -> alert_id
        self._source_timestamps: Dict[str, List[float]] = {}
        self._rate_limit_per_source = rate_limit_per_source
        self._rate_limit_window = rate_limit_window_seconds
    
    def _generate_dedup_key(self, title: str, source: str) -> str:
        """تولید کلید یکتا برای جلوگیری از تکرار"""
        raw = f"{title}:{source}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]
    
    def _check_rate_limit(self, source: str) -> bool:
        """بررسی محدودیت نرخ ارسال برای منبع"""
        now = time.time()
        cutoff = now - self._rate_limit_window
        
        with self._lock:
            if source not in self._source_timestamps:
                self._source_timestamps[source] = []
            
            # حذف رکوردهای قدیمی
            self._source_timestamps[source] = [
                ts for ts in self._source_timestamps[source]
                if ts > cutoff
            ]
            
            # بررسی تعداد
            if len(self._source_timestamps[source]) >= self._rate_limit_per_source:
                return False
            
            self._source_timestamps[source].append(now)
            return True
    
    def create_alert(
        self,
        title: str,
        description: str,
        severity: AlertSeverity,
        source: str,
        metadata: Optional[Dict] = None,
        channels: Optional[List[AlertChannel]] = None
    ) -> Optional[Alert]:
        """
        ایجاد هشدار جدید
        
        Returns:
            Alert if created, None if rate limited or deduplicated
        """
        # بررسی محدودیت نرخ
        if not self._check_rate_limit(source):
            return None
        
        dedup_key = self._generate_dedup_key(title, source)
        
        with self._lock:
            # بررسی تکرار
            if dedup_key in self._dedup_map:
                existing_id = self._dedup_map[dedup_key]
                existing = self._alerts.get(existing_id)
                # اگر هشدار فعال است، تکرار نکن
                if existing and existing.status in (AlertStatus.ACTIVE, AlertStatus.ACKNOWLEDGED):
                    return None
            
            # ایجاد هشدار جدید
            alert = Alert(
                id=str(uuid4()),
                title=title,
                description=description,
                severity=severity,
                source=source,
                timestamp=datetime.now(timezone.utc),
                metadata=metadata or {},
                dedup_key=dedup_key,
                status=AlertStatus.ACTIVE
            )
            
            self._alerts[alert.id] = alert
            self._dedup_map[dedup_key] = alert.id
            
            # ارسال به کانال‌ها (stub implementation)
            if channels:
                self._send_to_channels(alert, channels)
            
            return alert
    
    def _send_to_channels(self, alert: Alert, channels: List[AlertChannel]) -> None:
        """ارسال هشدار به کانال‌های خارجی (stub)"""
        # در صورت نیاز می‌توان پیاده‌سازی واقعی اضافه کرد
        pass
    
    def get_alert(self, alert_id: str) -> Optional[Alert]:
        """دریافت هشدار با شناسه"""
        with self._lock:
            return self._alerts.get(alert_id)
    
    def list_alerts(
        self,
        severity: Optional[AlertSeverity] = None,
        status: Optional[AlertStatus] = None,
        source: Optional[str] = None,
        limit: int = 100
    ) -> List[Alert]:
        """لیست هشدارها با فیلتر"""
        with self._lock:
            results = list(self._alerts.values())
            
            if severity:
                results = [a for a in results if a.severity == severity]
            if status:
                results = [a for a in results if a.status == status]
            if source:
                results = [a for a in results if a.source == source]
            
            # مرتب‌سازی بر اساس زمان (جدیدترین اول)
            results.sort(key=lambda x: x.timestamp, reverse=True)
            
            return results[:limit]
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """تایید دریافت هشدار"""
        with self._lock:
            alert = self._alerts.get(alert_id)
            if not alert or alert.status != AlertStatus.ACTIVE:
                return False
            
            alert.status = AlertStatus.ACKNOWLEDGED
            alert.acknowledged_at = datetime.now(timezone.utc)
            return True
    
    def resolve_alert(self, alert_id: str) -> bool:
        """حل شدن مشکل هشدار"""
        with self._lock:
            alert = self._alerts.get(alert_id)
            if not alert or alert.status == AlertStatus.SUPPRESSED:
                return False
            
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = datetime.now(timezone.utc)
            return True
    
    def suppress_alert(self, alert_id: str, duration_minutes: int = 60) -> bool:
        """خاموش کردن موقت هشدار"""
        with self._lock:
            alert = self._alerts.get(alert_id)
            if not alert:
                return False
            
            alert.status = AlertStatus.SUPPRESSED
            alert.suppressed_until = datetime.now(timezone.utc) + timedelta(minutes=duration_minutes)
            return True
    
    def get_stats(self) -> Dict:
        """آمار کلی سیستم هشدارها"""
        with self._lock:
            total = len(self._alerts)
            by_severity = {s: 0 for s in AlertSeverity}
            by_status = {s: 0 for s in AlertStatus}
            
            for alert in self._alerts.values():
                by_severity[alert.severity] += 1
                by_status[alert.status] += 1
            
            return {
                "total_alerts": total,
                "by_severity": {k.value: v for k, v in by_severity.items()},
                "by_status": {k.value: v for k, v in by_status.items()},
                "unique_sources": len(set(a.source for a in self._alerts.values())),
            }
