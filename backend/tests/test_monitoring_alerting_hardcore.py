"""
Monitoring Alerting System — Hardcore Test Suite
تست‌های فوق دشوار سیستم هشدارها

Tests:
1. Alert creation and retrieval
2. Alert deduplication (same title+source)
3. Alert lifecycle (create → acknowledge → resolve → suppress)
4. Alert severity filtering
5. Alert stats (count by severity, by status)
6. Rate limiting per source
7. Thread safety (concurrent alert creation)
"""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import pytest

from app.monitoring.alerting import (
    AlertSeverity,
    AlertChannel,
    Alert,
    AlertingSystem,
    AlertStatus,
)


class TestAlertCreationAndRetrieval:
    """تست ایجاد و بازیابی هشدار"""
    
    def test_create_alert_basic(self):
        """ایجاد هشدار ساده"""
        system = AlertingSystem()
        
        alert = system.create_alert(
            title="تست هشدار",
            description="این یک هشدار تستی است",
            severity=AlertSeverity.WARNING,
            source="test_system",
        )
        
        assert alert is not None
        assert alert.title == "تست هشدار"
        assert alert.severity == AlertSeverity.WARNING
        assert alert.status == AlertStatus.ACTIVE
        assert alert.dedup_key != ""
    
    def test_retrieve_alert_by_id(self):
        """بازیابی هشدار با شناسه"""
        system = AlertingSystem()
        
        alert = system.create_alert(
            title="هشدار شماره یک",
            description="توضیحات",
            severity=AlertSeverity.ERROR,
            source="test",
        )
        
        retrieved = system.get_alert(alert.id)
        assert retrieved is not None
        assert retrieved.id == alert.id
        assert retrieved.title == "هشدار شماره یک"
    
    def test_retrieve_nonexistent_alert(self):
        """بازیابی هشدار ناموجود"""
        system = AlertingSystem()
        
        retrieved = system.get_alert("nonexistent-id")
        assert retrieved is None


class TestAlertDeduplication:
    """تست جلوگیری از تکرار هشدارها"""
    
    def test_same_title_and_source_returns_none(self):
        """هشدار تکراری با همان عنوان و منبع"""
        system = AlertingSystem()
        
        alert1 = system.create_alert(
            title="Duplicate Alert",
            description="First occurrence",
            severity=AlertSeverity.WARNING,
            source="submission_system",
        )
        
        assert alert1 is not None
        dedup_key1 = alert1.dedup_key
        
        # Same title and source should be deduplicated
        alert2 = system.create_alert(
            title="Duplicate Alert",
            description="Second occurrence",
            severity=AlertSeverity.WARNING,
            source="submission_system",
        )
        
        assert alert2 is None  # Deduplicated
        
        # Verify only one alert exists
        alerts = system.list_alerts()
        assert len(alerts) == 1
    
    def test_different_source_creates_new_alert(self):
        """منبع متفاوت باید هشدار جدید ایجاد کند"""
        system = AlertingSystem()
        
        alert1 = system.create_alert(
            title="Same Title",
            description="From source 1",
            severity=AlertSeverity.INFO,
            source="source_1",
        )
        
        alert2 = system.create_alert(
            title="Same Title",
            description="From source 2",
            severity=AlertSeverity.INFO,
            source="source_2",
        )
        
        assert alert1 is not None
        assert alert2 is not None
        assert alert1.id != alert2.id
        assert alert1.dedup_key != alert2.dedup_key
    
    def test_resolved_alert_allows_new_duplicate(self):
        """هشدار حل شده اجازه تکرار جدید می‌دهد"""
        system = AlertingSystem()
        
        alert1 = system.create_alert(
            title="Resolved Issue",
            description="First",
            severity=AlertSeverity.ERROR,
            source="test",
        )
        
        assert alert1 is not None
        
        # Resolve the alert
        system.resolve_alert(alert1.id)
        
        # Now same alert should be allowed
        alert2 = system.create_alert(
            title="Resolved Issue",
            description="Second",
            severity=AlertSeverity.ERROR,
            source="test",
        )
        
        assert alert2 is not None
        assert alert2.id != alert1.id


class TestAlertLifecycle:
    """تست چرخه عمر هشدار"""
    
    def test_acknowledge_alert(self):
        """تایید دریافت هشدار"""
        system = AlertingSystem()
        
        alert = system.create_alert(
            title="Test Alert",
            description="Test",
            severity=AlertSeverity.WARNING,
            source="test",
        )
        
        assert alert.status == AlertStatus.ACTIVE
        
        success = system.acknowledge_alert(alert.id)
        assert success is True
        
        retrieved = system.get_alert(alert.id)
        assert retrieved.status == AlertStatus.ACKNOWLEDGED
        assert retrieved.acknowledged_at is not None
    
    def test_resolve_alert(self):
        """حل شدن مشکل هشدار"""
        system = AlertingSystem()
        
        alert = system.create_alert(
            title="Test Alert",
            description="Test",
            severity=AlertSeverity.ERROR,
            source="test",
        )
        
        # Acknowledge first
        system.acknowledge_alert(alert.id)
        
        # Then resolve
        success = system.resolve_alert(alert.id)
        assert success is True
        
        retrieved = system.get_alert(alert.id)
        assert retrieved.status == AlertStatus.RESOLVED
        assert retrieved.resolved_at is not None
    
    def test_suppress_alert(self):
        """خاموش کردن موقت هشدار"""
        system = AlertingSystem()
        
        alert = system.create_alert(
            title="Test Alert",
            description="Test",
            severity=AlertSeverity.INFO,
            source="test",
        )
        
        success = system.suppress_alert(alert.id, duration_minutes=30)
        assert success is True
        
        retrieved = system.get_alert(alert.id)
        assert retrieved.status == AlertStatus.SUPPRESSED
        assert retrieved.suppressed_until is not None
    
    def test_acknowledge_nonexistent_alert(self):
        """تایید هشدار ناموجود"""
        system = AlertingSystem()
        
        success = system.acknowledge_alert("nonexistent")
        assert success is False
    
    def test_resolve_suppressed_alert_fails(self):
        """resolve هشدار suppressed شده نباید کار کند"""
        system = AlertingSystem()
        
        alert = system.create_alert(
            title="Test",
            description="Test",
            severity=AlertSeverity.WARNING,
            source="test",
        )
        
        system.suppress_alert(alert.id)
        
        success = system.resolve_alert(alert.id)
        assert success is False  # Cannot resolve suppressed alert


class TestAlertFiltering:
    """تست فیلتر کردن هشدارها"""
    
    def test_list_alerts_by_severity(self):
        """فیلتر بر اساس severity"""
        system = AlertingSystem()
        
        system.create_alert("Critical 1", "desc", AlertSeverity.CRITICAL, "test")
        system.create_alert("Critical 2", "desc", AlertSeverity.CRITICAL, "test2")
        system.create_alert("Warning 1", "desc", AlertSeverity.WARNING, "test3")
        system.create_alert("Info 1", "desc", AlertSeverity.INFO, "test4")
        
        critical_alerts = system.list_alerts(severity=AlertSeverity.CRITICAL)
        assert len(critical_alerts) == 2
        
        warning_alerts = system.list_alerts(severity=AlertSeverity.WARNING)
        assert len(warning_alerts) == 1
    
    def test_list_alerts_by_status(self):
        """فیلتر بر اساس status"""
        system = AlertingSystem()
        
        alert1 = system.create_alert("Alert 1", "desc", AlertSeverity.ERROR, "test")
        alert2 = system.create_alert("Alert 2", "desc", AlertSeverity.ERROR, "test2")
        alert3 = system.create_alert("Alert 3", "desc", AlertSeverity.ERROR, "test3")
        
        system.acknowledge_alert(alert2.id)
        system.resolve_alert(alert3.id)
        
        active_alerts = system.list_alerts(status=AlertStatus.ACTIVE)
        assert len(active_alerts) == 1
        
        acknowledged_alerts = system.list_alerts(status=AlertStatus.ACKNOWLEDGED)
        assert len(acknowledged_alerts) == 1
        
        resolved_alerts = system.list_alerts(status=AlertStatus.RESOLVED)
        assert len(resolved_alerts) == 1
    
    def test_list_alerts_by_source(self):
        """فیلتر بر اساس source"""
        system = AlertingSystem()
        
        system.create_alert("Alert 1", "desc", AlertSeverity.INFO, "submission")
        system.create_alert("Alert 2", "desc", AlertSeverity.INFO, "submission")
        system.create_alert("Alert 3", "desc", AlertSeverity.INFO, "review")
        
        submission_alerts = system.list_alerts(source="submission")
        assert len(submission_alerts) == 2
        
        review_alerts = system.list_alerts(source="review")
        assert len(review_alerts) == 1


class TestAlertStats:
    """تست آمار سیستم هشدارها"""
    
    def test_get_stats(self):
        """دریافت آمار کلی"""
        system = AlertingSystem()
        
        # Create various alerts
        alert1 = system.create_alert("Critical", "desc", AlertSeverity.CRITICAL, "test1")
        alert2 = system.create_alert("Error", "desc", AlertSeverity.ERROR, "test2")
        alert3 = system.create_alert("Warning", "desc", AlertSeverity.WARNING, "test3")
        alert4 = system.create_alert("Info", "desc", AlertSeverity.INFO, "test4")
        
        # Change some statuses
        system.acknowledge_alert(alert2.id)
        system.resolve_alert(alert3.id)
        
        stats = system.get_stats()
        
        assert stats["total_alerts"] == 4
        assert stats["by_severity"]["critical"] == 1
        assert stats["by_severity"]["error"] == 1
        assert stats["by_severity"]["warning"] == 1
        assert stats["by_severity"]["info"] == 1
        assert stats["by_status"]["active"] == 2
        assert stats["by_status"]["acknowledged"] == 1
        assert stats["by_status"]["resolved"] == 1
        assert stats["unique_sources"] == 4


class TestRateLimiting:
    """تست محدودسازی نرخ ارسال"""
    
    def test_rate_limit_per_source(self):
        """محدودسازی تعداد هشدار در هر منبع"""
        system = AlertingSystem(rate_limit_per_source=3, rate_limit_window_seconds=60)
        
        # First 3 should succeed
        for i in range(3):
            alert = system.create_alert(
                f"Alert {i}",
                "desc",
                AlertSeverity.WARNING,
                "rate_limited_source"
            )
            assert alert is not None
        
        # 4th should be rate limited
        alert = system.create_alert(
            "Alert 4",
            "desc",
            AlertSeverity.WARNING,
            "rate_limited_source"
        )
        assert alert is None
    
    def test_rate_limit_per_source_independent(self):
        """محدودسازی به طور مستقل برای هر منبع"""
        system = AlertingSystem(rate_limit_per_source=2, rate_limit_window_seconds=60)
        
        # Source 1: 2 alerts
        for i in range(2):
            alert = system.create_alert(f"S1 Alert {i}", "desc", AlertSeverity.INFO, "source1")
            assert alert is not None
        
        # Source 1: 3rd should fail
        alert = system.create_alert("S1 Alert 3", "desc", AlertSeverity.INFO, "source1")
        assert alert is None
        
        # Source 2: should still work
        alert = system.create_alert("S2 Alert 1", "desc", AlertSeverity.INFO, "source2")
        assert alert is not None


class TestThreadSafety:
    """تست thread safety"""
    
    def test_concurrent_alert_creation(self):
        """ایجاد همزمان هشدارها"""
        system = AlertingSystem(rate_limit_per_source=1000)
        
        def create_alert(i):
            return system.create_alert(
                f"Concurrent Alert {i}",
                "desc",
                AlertSeverity.INFO,
                f"source_{i}"
            )
        
        # Create 100 alerts concurrently
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(create_alert, i) for i in range(100)]
            results = [f.result() for f in as_completed(futures)]
        
        # All should succeed (different sources)
        assert all(r is not None for r in results)
        
        # Verify count
        stats = system.get_stats()
        assert stats["total_alerts"] == 100
    
    def test_concurrent_status_changes(self):
        """تغییر همزمان وضعیت"""
        system = AlertingSystem()
        
        # Create alerts
        alerts = []
        for i in range(20):
            alert = system.create_alert(
                f"Alert {i}",
                "desc",
                AlertSeverity.WARNING,
                f"source_{i}"
            )
            alerts.append(alert)
        
        def acknowledge_alert(alert):
            return system.acknowledge_alert(alert.id)
        
        # Acknowledge all concurrently
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(acknowledge_alert, a) for a in alerts]
            results = [f.result() for f in as_completed(futures)]
        
        # All should succeed
        assert all(r is True for r in results)
        
        # Verify all are acknowledged
        acknowledged = system.list_alerts(status=AlertStatus.ACKNOWLEDGED)
        assert len(acknowledged) == 20
