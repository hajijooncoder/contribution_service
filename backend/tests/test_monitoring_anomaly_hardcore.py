"""
Monitoring Anomaly Detection — Hardcore Test Suite
تست‌های فوق دشوار تشخیص ناهنجاری

Tests:
1. Z-score detection with known outlier
2. IQR detection with known outlier
3. No detection below min_samples threshold
4. No detection within normal range
5. Multiple metric tracking
6. Window size enforcement (old values dropped)
7. Configurable sensitivity
"""

import pytest
from app.monitoring.anomaly_detector import AnomalyDetector


class TestZScoreDetection:
    """تست تشخیص ناهنجاری با روش Z-score"""
    
    def test_detect_outlier_above_threshold(self):
        """تشخیص outlier بالای آستانه"""
        detector = AnomalyDetector(z_threshold=3.0, min_samples=10)
        
        metric_name = "submission_duration"
        
        # Add normal values (mean≈100, std≈10)
        for i in range(20):
            detector.add_metric(metric_name, 100 + (i % 10 - 5) * 2)
        
        # Add extreme outlier (should trigger anomaly)
        detector.add_metric(metric_name, 200)  # Very high
        
        anomalies = detector.detect_anomalies()
        
        assert len(anomalies) == 1
        assert anomalies[0].metric_name == metric_name
        assert anomalies[0].current_value == 200
        assert anomalies[0].z_score > 3.0
    
    def test_detect_outlier_below_threshold(self):
        """تشخیص outlier پایین‌تر از آستانه"""
        detector = AnomalyDetector(z_threshold=3.0, min_samples=10)
        
        metric_name = "quality_score"
        
        # Add normal values (mean≈80, std≈5)
        for i in range(20):
            detector.add_metric(metric_name, 80 + (i % 10 - 5))
        
        # Add extreme outlier (very low quality)
        detector.add_metric(metric_name, 30)
        
        anomalies = detector.detect_anomalies()
        
        assert len(anomalies) == 1
        assert anomalies[0].current_value == 30
        assert anomalies[0].severity in ["high", "medium"]
    
    def test_no_detection_within_normal_range(self):
        """عدم تشخیص در محدوده نرمال"""
        detector = AnomalyDetector(z_threshold=3.0, min_samples=10)
        
        metric_name = "review_count"
        
        # Add normal values
        for i in range(20):
            detector.add_metric(metric_name, 50 + (i % 10))
        
        # Add value within normal range
        detector.add_metric(metric_name, 55)
        
        anomalies = detector.detect_anomalies()
        
        # Should not detect anomaly
        review_anomalies = [a for a in anomalies if a.metric_name == metric_name]
        assert len(review_anomalies) == 0


class TestIQRDetection:
    """تست تشخیص ناهنجاری با روش IQR"""
    
    def test_iqr_detects_outlier(self):
        """IQR باید outlier را تشخیص دهد"""
        detector = AnomalyDetector(iqr_multiplier=1.5, min_samples=10)
        
        metric_name = "duplicate_rate"
        
        # Add values: 10, 12, 14, ..., 28 (Q1=14, Q3=26, IQR=12)
        for i in range(10):
            detector.add_metric(metric_name, 10 + i * 2)
        
        # Add extreme outlier
        detector.add_metric(metric_name, 100)
        
        anomalies = detector.detect_anomalies()
        
        assert len(anomalies) >= 1
        outlier_found = any(
            a.metric_name == metric_name and a.current_value == 100
            for a in anomalies
        )
        assert outlier_found


class TestMinSamplesThreshold:
    """تست آستانه حداقل تعداد نمونه"""
    
    def test_no_detection_below_min_samples(self):
        """عدم تشخیص زیر حداقل نمونه"""
        detector = AnomalyDetector(min_samples=10)
        
        metric_name = "test_metric"
        
        # Add only 5 samples (below threshold)
        for i in range(5):
            detector.add_metric(metric_name, 50)
        
        # Add obvious outlier
        detector.add_metric(metric_name, 1000)
        
        anomalies = detector.detect_anomalies()
        
        # Should not detect (not enough samples)
        assert len(anomalies) == 0
    
    def test_detection_at_min_samples(self):
        """تشخیص در حداقل نمونه"""
        detector = AnomalyDetector(min_samples=10, z_threshold=2.0)
        
        metric_name = "test_metric"
        
        # Add exactly min_samples
        for i in range(10):
            detector.add_metric(metric_name, 100)
        
        # Add outlier
        detector.add_metric(metric_name, 200)
        
        anomalies = detector.detect_anomalies()
        
        # Should detect (enough samples now)
        assert len(anomalies) >= 1


class TestMultipleMetrics:
    """تست ردیابی چندین متریک"""
    
    def test_track_multiple_metrics_independently(self):
        """ردیابی مستقل چند متریک"""
        detector = AnomalyDetector(z_threshold=3.0, min_samples=10)
        
        # Metric 1: normal
        for i in range(15):
            detector.add_metric("metric_1", 100 + i)
        detector.add_metric("metric_1", 110)  # Normal
        
        # Metric 2: has outlier
        for i in range(15):
            detector.add_metric("metric_2", 50 + i)
        detector.add_metric("metric_2", 500)  # Outlier
        
        anomalies = detector.detect_anomalies()
        
        # Should only detect metric_2 anomaly
        metric_2_anomalies = [a for a in anomalies if a.metric_name == "metric_2"]
        metric_1_anomalies = [a for a in anomalies if a.metric_name == "metric_1"]
        
        assert len(metric_2_anomalies) >= 1
        assert len(metric_1_anomalies) == 0
    
    def test_simultaneous_anomalies_in_multiple_metrics(self):
        """ناهنجاری همزمان در چند متریک"""
        detector = AnomalyDetector(z_threshold=2.5, min_samples=10)
        
        # Add normal values for both metrics
        for i in range(15):
            detector.add_metric("submissions", 100 + i)
            detector.add_metric("reviews", 50 + i)
        
        # Add outliers to both
        detector.add_metric("submissions", 500)
        detector.add_metric("reviews", 500)
        
        anomalies = detector.detect_anomalies()
        
        # Should detect both
        submission_anomalies = [a for a in anomalies if a.metric_name == "submissions"]
        review_anomalies = [a for a in anomalies if a.metric_name == "reviews"]
        
        assert len(submission_anomalies) >= 1
        assert len(review_anomalies) >= 1


class TestWindowSizeEnforcement:
    """تست اعمال اندازه پنجره"""
    
    def test_old_values_dropped(self):
        """مقادیر قدیمی باید حذف شوند"""
        detector = AnomalyDetector(window_size=100, min_samples=10)
        
        metric_name = "windowed_metric"
        
        # Add 150 values (more than window size)
        for i in range(150):
            detector.add_metric(metric_name, 100 + i % 10)
        
        # Check internal history size
        assert len(detector._metrics[metric_name]) == 100  # maxlen enforced
    
    def test_statistics_based_on_window_only(self):
        """آمار فقط بر اساس پنجره محاسبه شود"""
        detector = AnomalyDetector(window_size=20, z_threshold=3.0, min_samples=10)
        
        metric_name = "test"
        
        # Phase 1: Add values around 100
        for i in range(50):
            detector.add_metric(metric_name, 100 + i % 5)
        
        # Phase 2: Add values around 200 (new normal)
        for i in range(50):
            detector.add_metric(metric_name, 200 + i % 5)
        
        # Add value near old mean (100) - should be anomaly now
        detector.add_metric(metric_name, 105)
        
        anomalies = detector.detect_anomalies()
        
        # Should detect because current window is around 200
        test_anomalies = [a for a in anomalies if a.metric_name == metric_name]
        assert len(test_anomalies) >= 1


class TestConfigurableSensitivity:
    """تست حساسیت قابل تنظیم"""
    
    def test_lower_threshold_more_sensitive(self):
        """آستانه پایین‌تر = حساس‌تر"""
        # High sensitivity (z_threshold=2.0)
        sensitive_detector = AnomalyDetector(z_threshold=2.0, min_samples=10)
        
        # Low sensitivity (z_threshold=5.0)
        insensitive_detector = AnomalyDetector(z_threshold=5.0, min_samples=10)
        
        metric_name = "test"
        
        # Add same data to both - wider distribution to avoid IQR conflicts
        # Use range 50-150 with uniform distribution
        for i in range(30):
            value = 50 + (i * 100 / 30)  # Uniform 50-150
            sensitive_detector.add_metric(metric_name, value)
            insensitive_detector.add_metric(metric_name, value)
        
        # Add moderate outlier that:
        # - Has z-score between 2.0 and 5.0 (detected by sensitive, not by insensitive)
        # - Is within IQR bounds (so IQR doesn't detect it)
        # Mean ≈ 100, std ≈ 30, so 180 gives z-score ≈ 2.7
        # IQR range is much wider (Q1≈50, Q3≈150, upper_bound≈195), so 180 is safe
        sensitive_detector.add_metric(metric_name, 180)
        insensitive_detector.add_metric(metric_name, 180)
        
        sensitive_anomalies = sensitive_detector.detect_anomalies()
        insensitive_anomalies = insensitive_detector.detect_anomalies()
        
        # Sensitive (threshold=2.0) should detect z≈2.7
        # Insensitive (threshold=5.0) should NOT detect z≈2.7
        assert len(sensitive_anomalies) >= 1
        assert len(insensitive_anomalies) == 0
    
    def test_iqr_multiplier_affects_sensitivity(self):
        """ضریب IQR بر حساسیت تاثیر می‌گذارد"""
        # High sensitivity (multiplier=1.0)
        sensitive = AnomalyDetector(iqr_multiplier=1.0, min_samples=10)
        
        # Low sensitivity (multiplier=3.0)
        insensitive = AnomalyDetector(iqr_multiplier=3.0, min_samples=10)
        
        metric = "test"
        
        for i in range(15):
            value = 50 + i * 2
            sensitive.add_metric(metric, value)
            insensitive.add_metric(metric, value)
        
        # Add moderate outlier
        sensitive.add_metric(metric, 120)
        insensitive.add_metric(metric, 120)
        
        sensitive_anomalies = sensitive.detect_anomalies()
        insensitive_anomalies = insensitive.detect_anomalies()
        
        # Sensitive should detect more
        assert len(sensitive_anomalies) >= len(insensitive_anomalies)


class TestMetricStats:
    """تست آمار متریک"""
    
    def test_get_metric_stats(self):
        """دریافت آمار یک متریک"""
        detector = AnomalyDetector()
        
        metric_name = "test_metric"
        
        # Add values
        values = [10, 20, 30, 40, 50]
        for v in values:
            detector.add_metric(metric_name, v)
        
        stats = detector.get_metric_stats(metric_name)
        
        assert stats is not None
        assert stats["count"] == 5
        assert stats["mean"] == 30.0
        assert stats["median"] == 30.0
        assert stats["min"] == 10.0
        assert stats["max"] == 50.0
    
    def test_get_stats_for_nonexistent_metric(self):
        """آمار برای متریک ناموجود"""
        detector = AnomalyDetector()
        
        stats = detector.get_metric_stats("nonexistent")
        
        assert stats is None
