"""
Rolling Statistics Calculator
محاسبه‌گر آمار لغزان

Provides:
- Time-based rolling window
- Count-based rolling window
- Percentiles (P25, P50, P75, P95, P99)
- Mean, std, min, max, median
- Thread-safe operation
"""

import statistics
import time
from collections import deque
from dataclasses import dataclass
from threading import RLock
from typing import List, Optional


@dataclass
class RollingStats:
    """
    آمار محاسبه شده از پنجره لغزان
    """
    mean: float
    std: float
    min: float
    max: float
    median: float
    p25: float
    p75: float
    p95: float
    p99: float
    count: int


class RollingStatsCalculator:
    """
    محاسبه‌گر آمار لغزان با دو روش:
    1. پنجره زمانی: فقط داده‌های اخیر (مثلاً آخرین ساعت)
    2. پنجره تعدادی: فقط N داده آخر
    
    Thread-safe
    """
    
    def __init__(
        self,
        time_window_seconds: Optional[int] = 3600,  # 1 hour
        count_window: Optional[int] = 1000
    ):
        """
        Args:
            time_window_seconds: پنجره زمانی (ثانیه)، None برای غیرفعال
            count_window: پنجره تعدادی، None برای غیرفعال
        """
        self._lock = RLock()
        self._time_window = time_window_seconds
        self._count_window = count_window
        
        # ذخیره (value, timestamp)
        maxlen = count_window if count_window else None
        self._data: deque = deque(maxlen=maxlen)
    
    def add_value(self, value: float) -> None:
        """افزودن مقدار جدید"""
        with self._lock:
            self._data.append((value, time.time()))
    
    def _get_valid_values(self) -> List[float]:
        """دریافت مقادیر معتبر در پنجره"""
        with self._lock:
            now = time.time()
            cutoff = now - self._time_window if self._time_window else 0
            
            # فیلتر بر اساس زمان
            valid = [v for v, t in self._data if t > cutoff]
            
            return valid
    
    def get_stats(self) -> Optional[RollingStats]:
        """
        محاسبه آمار
        
        Returns:
            RollingStats یا None اگر داده کافی نباشد
        """
        values = self._get_valid_values()
        
        if not values:
            return None
        
        sorted_values = sorted(values)
        count = len(sorted_values)
        
        # محاسبات پایه
        mean_val = statistics.mean(sorted_values)
        std_val = statistics.stdev(sorted_values) if count > 1 else 0.0
        min_val = min(sorted_values)
        max_val = max(sorted_values)
        median_val = statistics.median(sorted_values)
        
        # محاسبه صدک‌ها
        def percentile(data: List[float], p: float) -> float:
            """محاسبه صدک p (0-100)"""
            if not data:
                return 0.0
            k = (len(data) - 1) * (p / 100.0)
            f = int(k)
            c = f + 1
            if c >= len(data):
                return data[-1]
            d0 = data[f]
            d1 = data[c]
            return d0 + (d1 - d0) * (k - f)
        
        p25 = percentile(sorted_values, 25)
        p75 = percentile(sorted_values, 75)
        p95 = percentile(sorted_values, 95)
        p99 = percentile(sorted_values, 99)
        
        return RollingStats(
            mean=mean_val,
            std=std_val,
            min=min_val,
            max=max_val,
            median=median_val,
            p25=p25,
            p75=p75,
            p95=p95,
            p99=p99,
            count=count
        )
    
    def reset(self) -> None:
        """پاک کردن تمام داده‌ها"""
        with self._lock:
            self._data.clear()
