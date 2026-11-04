"""
Contribution Service Metrics Collector
جمع‌آوری متریک‌های سرویس مشارکت

Domain-specific metrics:
- Submission metrics (total, by status, by type, duration)
- Duplicate detection metrics (by level)
- Review metrics (by decision, queue depth)
- Quality score distribution
- Audit ledger health
- Rate limiting rejections
- Active users
"""

import time
from collections import defaultdict
from threading import RLock
from typing import Dict, List, Optional


class Counter:
    """شمارنده thread-safe"""
    def __init__(self):
        self._lock = RLock()
        self._value = 0
    
    def inc(self, amount: int = 1):
        with self._lock:
            self._value += amount
    
    def get(self) -> int:
        with self._lock:
            return self._value
    
    def reset(self):
        with self._lock:
            self._value = 0


class Gauge:
    """مقدار فعلی thread-safe"""
    def __init__(self):
        self._lock = RLock()
        self._value = 0.0
    
    def set(self, value: float):
        with self._lock:
            self._value = value
    
    def inc(self, amount: float = 1.0):
        with self._lock:
            self._value += amount
    
    def dec(self, amount: float = 1.0):
        with self._lock:
            self._value -= amount
    
    def get(self) -> float:
        with self._lock:
            return self._value


class Histogram:
    """هیستوگرام thread-safe برای توزیع مقادیر"""
    def __init__(self):
        self._lock = RLock()
        self._values: List[float] = []
        self._sum = 0.0
        self._count = 0
    
    def observe(self, value: float):
        with self._lock:
            self._values.append(value)
            self._sum += value
            self._count += 1
    
    def get_stats(self) -> Dict:
        with self._lock:
            if not self._values:
                return {"count": 0, "sum": 0.0, "avg": 0.0}
            return {
                "count": self._count,
                "sum": self._sum,
                "avg": self._sum / self._count if self._count > 0 else 0.0,
                "min": min(self._values),
                "max": max(self._values),
            }


class ContributionMetricsCollector:
    """
    جمع‌آوری متریک‌های سرویس مشارکت حقوقی
    
    Thread-safe و با قابلیت export به Prometheus
    """
    
    def __init__(self):
        self._lock = RLock()
        self._start_time = time.time()
        
        # Submission metrics
        self._submission_total = Counter()
        self._submission_by_status: Dict[str, Counter] = defaultdict(Counter)
        self._submission_by_type: Dict[str, Counter] = defaultdict(Counter)
        self._submission_duration = Histogram()
        
        # Duplicate detection metrics
        self._duplicate_detected: Dict[str, Counter] = defaultdict(Counter)
        
        # Review metrics
        self._review_total = Counter()
        self._review_by_decision: Dict[str, Counter] = defaultdict(Counter)
        self._review_queue_depth = Gauge()
        
        # Quality metrics
        self._quality_scores = Histogram()
        
        # Audit ledger metrics
        self._audit_entries = Counter()
        self._audit_integrity_checks = Counter()
        self._audit_integrity_failures = Counter()
        
        # Rate limiting metrics
        self._rate_limit_rejections: Dict[str, Counter] = defaultdict(Counter)
        
        # Active users
        self._active_users = Gauge()
    
    # ===== Submission Metrics =====
    
    def record_submission(
        self,
        status: str,
        document_type: str,
        duration_seconds: Optional[float] = None
    ):
        """ثبت یک submission"""
        self._submission_total.inc()
        self._submission_by_status[status].inc()
        self._submission_by_type[document_type].inc()
        
        if duration_seconds is not None:
            self._submission_duration.observe(duration_seconds)
    
    def record_duplicate_detection(self, level: str):
        """ثبت تشخیص تکراری (exact, near, partial, version)"""
        self._duplicate_detected[level].inc()
    
    # ===== Review Metrics =====
    
    def record_review(self, decision: str):
        """ثبت یک review (approve, reject, request_correction)"""
        self._review_total.inc()
        self._review_by_decision[decision].inc()
    
    def set_review_queue_depth(self, depth: int):
        """تنظیم عمق صف review"""
        self._review_queue_depth.set(float(depth))
    
    # ===== Quality Metrics =====
    
    def record_quality_score(self, score: float):
        """ثبت نمره کیفیت (0-100)"""
        self._quality_scores.observe(score)
    
    # ===== Audit Ledger Metrics =====
    
    def record_audit_entry(self):
        """ثبت یک ورودی audit"""
        self._audit_entries.inc()
    
    def record_audit_integrity_check(self, success: bool):
        """ثبت بررسی یکپارچگی audit ledger"""
        self._audit_integrity_checks.inc()
        if not success:
            self._audit_integrity_failures.inc()
    
    # ===== Rate Limiting Metrics =====
    
    def record_rate_limit_rejection(self, endpoint: str):
        """ثبت رد درخواست به دلیل rate limit"""
        self._rate_limit_rejections[endpoint].inc()
    
    # ===== Active Users =====
    
    def set_active_users(self, count: int):
        """تنظیم تعداد کاربران فعال"""
        self._active_users.set(float(count))
    
    # ===== Export =====
    
    def get_prometheus_metrics(self) -> str:
        """
        خروجی متریک‌ها به فرمت Prometheus
        
        Returns:
            متن فرمت Prometheus
        """
        lines = []
        
        # Uptime
        uptime = time.time() - self._start_time
        lines.append(f"# HELP contribution_uptime_seconds Service uptime in seconds")
        lines.append(f"# TYPE contribution_uptime_seconds gauge")
        lines.append(f"contribution_uptime_seconds {uptime:.0f}")
        
        # Submissions
        lines.append(f"# HELP contribution_submissions_total Total number of submissions")
        lines.append(f"# TYPE contribution_submissions_total counter")
        lines.append(f"contribution_submissions_total {self._submission_total.get()}")
        
        for status, counter in self._submission_by_status.items():
            lines.append(f'contribution_submissions_by_status{{status="{status}"}} {counter.get()}')
        
        for doc_type, counter in self._submission_by_type.items():
            lines.append(f'contribution_submissions_by_type{{type="{doc_type}"}} {counter.get()}')
        
        # Submission duration
        duration_stats = self._submission_duration.get_stats()
        if duration_stats["count"] > 0:
            lines.append(f"# HELP contribution_submission_duration_seconds Submission processing duration")
            lines.append(f"# TYPE contribution_submission_duration_seconds summary")
            lines.append(f"contribution_submission_duration_count {duration_stats['count']}")
            lines.append(f"contribution_submission_duration_sum {duration_stats['sum']:.2f}")
        
        # Duplicates
        lines.append(f"# HELP contribution_duplicates_detected_total Duplicates detected by level")
        lines.append(f"# TYPE contribution_duplicates_detected_total counter")
        for level, counter in self._duplicate_detected.items():
            lines.append(f'contribution_duplicates_detected_total{{level="{level}"}} {counter.get()}')
        
        # Reviews
        lines.append(f"# HELP contribution_reviews_total Total number of reviews")
        lines.append(f"# TYPE contribution_reviews_total counter")
        lines.append(f"contribution_reviews_total {self._review_total.get()}")
        
        for decision, counter in self._review_by_decision.items():
            lines.append(f'contribution_reviews_by_decision{{decision="{decision}"}} {counter.get()}')
        
        lines.append(f"# HELP contribution_review_queue_depth Current review queue depth")
        lines.append(f"# TYPE contribution_review_queue_depth gauge")
        lines.append(f"contribution_review_queue_depth {self._review_queue_depth.get():.0f}")
        
        # Quality
        quality_stats = self._quality_scores.get_stats()
        if quality_stats["count"] > 0:
            lines.append(f"# HELP contribution_quality_score Quality score distribution")
            lines.append(f"# TYPE contribution_quality_score summary")
            lines.append(f"contribution_quality_score_count {quality_stats['count']}")
            lines.append(f"contribution_quality_score_sum {quality_stats['sum']:.2f}")
            lines.append(f"contribution_quality_score_avg {quality_stats['avg']:.2f}")
        
        # Audit
        lines.append(f"# HELP contribution_audit_entries_total Total audit ledger entries")
        lines.append(f"# TYPE contribution_audit_entries_total counter")
        lines.append(f"contribution_audit_entries_total {self._audit_entries.get()}")
        
        lines.append(f"# HELP contribution_audit_integrity_checks_total Total integrity checks")
        lines.append(f"# TYPE contribution_audit_integrity_checks_total counter")
        lines.append(f"contribution_audit_integrity_checks_total {self._audit_integrity_checks.get()}")
        
        lines.append(f"# HELP contribution_audit_integrity_failures_total Total integrity check failures")
        lines.append(f"# TYPE contribution_audit_integrity_failures_total counter")
        lines.append(f"contribution_audit_integrity_failures_total {self._audit_integrity_failures.get()}")
        
        # Rate limiting
        lines.append(f"# HELP contribution_rate_limit_rejections_total Rate limit rejections by endpoint")
        lines.append(f"# TYPE contribution_rate_limit_rejections_total counter")
        for endpoint, counter in self._rate_limit_rejections.items():
            lines.append(f'contribution_rate_limit_rejections_total{{endpoint="{endpoint}"}} {counter.get()}')
        
        # Active users
        lines.append(f"# HELP contribution_active_users Current number of active users")
        lines.append(f"# TYPE contribution_active_users gauge")
        lines.append(f"contribution_active_users {self._active_users.get():.0f}")
        
        return "\n".join(lines) + "\n"
    
    def get_health_status(self) -> Dict:
        """
        وضعیت سلامت کامپوننت‌ها
        
        Returns:
            Dict با وضعیت هر کامپوننت (healthy/degraded/critical)
        """
        components = {}
        
        # Submission system
        total_submissions = self._submission_total.get()
        if total_submissions == 0:
            components["submission_system"] = "healthy"  # تازه راه‌اندازی شده
        else:
            components["submission_system"] = "healthy"
        
        # Audit ledger
        audit_checks = self._audit_integrity_checks.get()
        audit_failures = self._audit_integrity_failures.get()
        
        if audit_checks == 0:
            components["audit_ledger"] = "healthy"
        elif audit_failures == 0:
            components["audit_ledger"] = "healthy"
        elif audit_failures / audit_checks < 0.01:  # کمتر از 1% خرابی
            components["audit_ledger"] = "degraded"
        else:
            components["audit_ledger"] = "critical"
        
        # Review queue
        queue_depth = int(self._review_queue_depth.get())
        if queue_depth < 10:
            components["review_queue"] = "healthy"
        elif queue_depth < 50:
            components["review_queue"] = "degraded"
        else:
            components["review_queue"] = "critical"
        
        # Overall status
        statuses = list(components.values())
        if "critical" in statuses:
            overall = "critical"
        elif "degraded" in statuses:
            overall = "degraded"
        else:
            overall = "healthy"
        
        return {
            "status": overall,
            "components": components,
            "timestamp": time.time(),
        }


# Global singleton instance
_metrics_collector: Optional[ContributionMetricsCollector] = None
_collector_lock = RLock()


def get_metrics_collector() -> ContributionMetricsCollector:
    """دریافت instance سراسری metrics collector"""
    global _metrics_collector
    with _collector_lock:
        if _metrics_collector is None:
            _metrics_collector = ContributionMetricsCollector()
        return _metrics_collector
