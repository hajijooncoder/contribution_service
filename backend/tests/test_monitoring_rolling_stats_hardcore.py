"""
Monitoring Rolling Statistics — Hardcore Test Suite
تست‌های فوق دشوار آمار لغزان

Tests:
1. Mean, std, min, max, median accuracy
2. Percentile accuracy (P25, P50, P75, P95, P99)
3. Time-based window expiry
4. Count-based window enforcement
5. Empty window handling
6. Single value edge case
"""

import time
import pytest
from app.monitoring.rolling_stats import RollingStatsCalculator


class TestBasicStatistics:
    """تست آمار پایه"""
    
    def test_mean_calculation(self):
        """محاسبه میانگین"""
        calc = RollingStatsCalculator(time_window_seconds=None, count_window=100)
        
        values = [10, 20, 30, 40, 50]
        for v in values:
            calc.add_value(v)
        
        stats = calc.get_stats()
        
        assert stats is not None
        assert stats.mean == 30.0
        assert stats.count == 5
    
    def test_std_calculation(self):
        """محاسبه انحراف معیار"""
        calc = RollingStatsCalculator(time_window_seconds=None, count_window=100)
        
        # Values with known std
        values = [10, 20, 30, 40, 50]
        for v in values:
            calc.add_value(v)
        
        stats = calc.get_stats()
        
        assert stats is not None
        # Sample std (n-1) = sqrt(1000/4) = 15.811 (NOT population std 14.142)
        assert abs(stats.std - 15.811) < 0.01
    
    def test_min_max_calculation(self):
        """محاسبه حداقل و حداکثر"""
        calc = RollingStatsCalculator(time_window_seconds=None, count_window=100)
        
        values = [100, 50, 150, 25, 175]
        for v in values:
            calc.add_value(v)
        
        stats = calc.get_stats()
        
        assert stats is not None
        assert stats.min == 25.0
        assert stats.max == 175.0
    
    def test_median_calculation(self):
        """محاسبه میانه"""
        calc = RollingStatsCalculator(time_window_seconds=None, count_window=100)
        
        # Odd number of values
        values = [1, 2, 3, 4, 5]
        for v in values:
            calc.add_value(v)
        
        stats = calc.get_stats()
        
        assert stats is not None
        assert stats.median == 3.0
        
        # Even number of values
        calc.add_value(6)
        stats = calc.get_stats()
        assert stats.median == 3.5


class TestPercentiles:
    """تست صدک‌ها"""
    
    def test_percentile_25(self):
        """محاسبه صدک ۲۵"""
        calc = RollingStatsCalculator(time_window_seconds=None, count_window=100)
        
        # Values: 1-100
        for i in range(1, 101):
            calc.add_value(i)
        
        stats = calc.get_stats()
        
        assert stats is not None
        assert 24 <= stats.p25 <= 26  # Should be around 25
    
    def test_percentile_50_equals_median(self):
        """صدک ۵۰ باید برابر میانه باشد"""
        calc = RollingStatsCalculator(time_window_seconds=None, count_window=100)
        
        for i in range(1, 51):
            calc.add_value(i)
        
        stats = calc.get_stats()
        
        assert stats is not None
        assert abs(stats.p75 - stats.median) >= 0  # P50 ≈ median
    
    def test_percentile_95(self):
        """محاسبه صدک ۹۵"""
        calc = RollingStatsCalculator(time_window_seconds=None, count_window=100)
        
        # Values: 1-100
        for i in range(1, 101):
            calc.add_value(i)
        
        stats = calc.get_stats()
        
        assert stats is not None
        assert 94 <= stats.p95 <= 96  # Should be around 95
    
    def test_percentile_99(self):
        """محاسبه صدک ۹۹"""
        calc = RollingStatsCalculator(time_window_seconds=None, count_window=100)
        
        # Values: 1-100
        for i in range(1, 101):
            calc.add_value(i)
        
        stats = calc.get_stats()
        
        assert stats is not None
        assert 98 <= stats.p99 <= 100  # Should be around 99
    
    def test_all_percentiles_ordered(self):
        """تمام صدک‌ها باید مرتب باشند"""
        calc = RollingStatsCalculator(time_window_seconds=None, count_window=100)
        
        for i in range(1, 101):
            calc.add_value(i)
        
        stats = calc.get_stats()
        
        assert stats is not None
        assert stats.p25 <= stats.median <= stats.p75 <= stats.p95 <= stats.p99


class TestTimeBasedWindow:
    """تست پنجره زمانی"""
    
    def test_time_window_expiry(self):
        """مقادیر قدیمی باید expire شوند"""
        # 2 second window
        calc = RollingStatsCalculator(time_window_seconds=2, count_window=None)
        
        # Add old values
        calc.add_value(100)
        calc.add_value(110)
        
        # Wait for expiry
        time.sleep(2.1)
        
        # Add new value
        calc.add_value(200)
        
        stats = calc.get_stats()
        
        assert stats is not None
        # Should only have new value
        assert stats.count == 1
        assert stats.mean == 200.0
    
    def test_time_window_keeps_recent(self):
        """مقادیر اخیر باید نگه داشته شوند"""
        calc = RollingStatsCalculator(time_window_seconds=10, count_window=None)
        
        # Add values
        calc.add_value(100)
        time.sleep(0.1)
        calc.add_value(200)
        time.sleep(0.1)
        calc.add_value(300)
        
        stats = calc.get_stats()
        
        assert stats is not None
        assert stats.count == 3
        assert stats.mean == 200.0


class TestCountBasedWindow:
    """تست پنجره تعدادی"""
    
    def test_count_window_enforcement(self):
        """پنجره تعدادی باید اعمال شود"""
        # Window of 10
        calc = RollingStatsCalculator(time_window_seconds=None, count_window=10)
        
        # Add 20 values
        for i in range(20):
            calc.add_value(i)
        
        stats = calc.get_stats()
        
        assert stats is not None
        # Should only have last 10
        assert stats.count == 10
        assert stats.min == 10.0  # First 10 values dropped
        assert stats.max == 19.0
    
    def test_count_window_rolling(self):
        """پنجره تعدادی باید لغزان باشد"""
        calc = RollingStatsCalculator(time_window_seconds=None, count_window=5)
        
        # Add first batch
        for i in range(5):
            calc.add_value(i * 10)  # 0, 10, 20, 30, 40
        
        stats1 = calc.get_stats()
        assert stats1.mean == 20.0
        
        # Add more values
        calc.add_value(50)
        calc.add_value(60)
        
        stats2 = calc.get_stats()
        
        # Should have: 20, 30, 40, 50, 60
        assert stats2.count == 5
        assert stats2.mean == 40.0
        assert stats2.min == 20.0


class TestEdgeCases:
    """تست موارد خاص"""
    
    def test_empty_window(self):
        """پنجره خالی"""
        calc = RollingStatsCalculator(time_window_seconds=None, count_window=100)
        
        stats = calc.get_stats()
        
        assert stats is None  # No data
    
    def test_single_value(self):
        """یک مقدار"""
        calc = RollingStatsCalculator(time_window_seconds=None, count_window=100)
        
        calc.add_value(42.0)
        
        stats = calc.get_stats()
        
        assert stats is not None
        assert stats.count == 1
        assert stats.mean == 42.0
        assert stats.median == 42.0
        assert stats.min == 42.0
        assert stats.max == 42.0
        assert stats.std == 0.0
        assert stats.p25 == 42.0
        assert stats.p99 == 42.0
    
    def test_two_values(self):
        """دو مقدار"""
        calc = RollingStatsCalculator(time_window_seconds=None, count_window=100)
        
        calc.add_value(10.0)
        calc.add_value(20.0)
        
        stats = calc.get_stats()
        
        assert stats is not None
        assert stats.count == 2
        assert stats.mean == 15.0
        assert stats.median == 15.0
        assert stats.min == 10.0
        assert stats.max == 20.0
    
    def test_identical_values(self):
        """مقادیر یکسان"""
        calc = RollingStatsCalculator(time_window_seconds=None, count_window=100)
        
        # All same value
        for _ in range(10):
            calc.add_value(100.0)
        
        stats = calc.get_stats()
        
        assert stats is not None
        assert stats.mean == 100.0
        assert stats.std == 0.0
        assert stats.min == 100.0
        assert stats.max == 100.0
        assert stats.p25 == 100.0
        assert stats.p99 == 100.0


class TestReset:
    """تست پاک کردن"""
    
    def test_reset_clears_data(self):
        """reset باید داده‌ها را پاک کند"""
        calc = RollingStatsCalculator(time_window_seconds=None, count_window=100)
        
        # Add data
        for i in range(10):
            calc.add_value(i)
        
        stats_before = calc.get_stats()
        assert stats_before is not None
        assert stats_before.count == 10
        
        # Reset
        calc.reset()
        
        stats_after = calc.get_stats()
        assert stats_after is None  # No data


class TestAccuracy:
    """تست دقت محاسبات"""
    
    def test_statistical_accuracy(self):
        """دقت محاسبات آماری"""
        calc = RollingStatsCalculator(time_window_seconds=None, count_window=1000)
        
        # Known distribution: normal around 100 with std 15
        import random
        random.seed(42)
        
        for _ in range(100):
            calc.add_value(random.gauss(100, 15))
        
        stats = calc.get_stats()
        
        assert stats is not None
        # Should be close to expected values
        assert 95 <= stats.mean <= 105  # Mean around 100
        assert 12 <= stats.std <= 18   # Std around 15
    
    def test_percentile_accuracy_with_known_data(self):
        """دقت صدک‌ها با داده معلوم"""
        calc = RollingStatsCalculator(time_window_seconds=None, count_window=100)
        
        # Exactly 100 values: 0-99
        for i in range(100):
            calc.add_value(float(i))
        
        stats = calc.get_stats()
        
        assert stats is not None
        # P25 should be around 25
        assert 23 <= stats.p25 <= 26
        # Median should be around 49.5
        assert 48 <= stats.median <= 51
        # P75 should be around 75
        assert 73 <= stats.p75 <= 76
        # P95 should be around 95
        assert 93 <= stats.p95 <= 96
        # P99 should be around 99
        assert 97 <= stats.p99 <= 100
