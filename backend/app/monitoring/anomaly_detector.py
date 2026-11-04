"""
Statistical Anomaly Detection
تشخیص ناهنجاری آماری

Provides:
- Z-score based anomaly detection (configurable threshold)
- IQR (Interquartile Range) based detection
- Rolling window per metric
- Minimum sample requirement
- Thread-safe operation
"""

import statistics
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from threading import RLock
from typing import Dict, List, Optional


@dataclass
class AnomalyAlert:
    """
    هشدار ناهنجاری آماری
    """
    metric_name: str
    current_value: float
    expected_range: tuple[float, float]  # (min, max)
    severity: str  # "high", "medium", "low"
    timestamp: datetime
    z_score: Optional[float] = None
    message: str = ""


class AnomalyDetector:
    """
    تشخیص‌دهنده ناهنجاری آماری با استفاده از:
    - Z-score: فاصله از میانگین بر حسب انحراف معیار
    - IQR: محدوده بین چارک‌های اول و سوم
    
    Thread-safe و با حافظه محدود (rolling window)
    """
    
    def __init__(
        self,
        z_threshold: float = 3.0,
        iqr_multiplier: float = 1.5,
        min_samples: int = 10,
        window_size: int = 1000
    ):
        """
        Args:
            z_threshold: آستانه Z-score برای تشخیص ناهنجاری
            iqr_multiplier: ضریب IQR برای تشخیص outlier
            min_samples: حداقل تعداد نمونه قبل از تشخیص
            window_size: حداکثر تعداد نمونه نگهداری شده برای هر متریک
        """
        self._lock = RLock()
        self._metrics: Dict[str, deque] = {}
        self._z_threshold = z_threshold
        self._iqr_multiplier = iqr_multiplier
        self._min_samples = min_samples
        self._window_size = window_size
    
    def add_metric(self, metric_name: str, value: float) -> None:
        """افزودن مقدار جدید به متریک"""
        with self._lock:
            if metric_name not in self._metrics:
                self._metrics[metric_name] = deque(maxlen=self._window_size)
            
            self._metrics[metric_name].append(value)
    
    def _calculate_z_score(self, values: List[float], current: float) -> float:
        """محاسبه Z-score"""
        if len(values) < 2:
            return 0.0
        
        mean = statistics.mean(values)
        try:
            stdev = statistics.stdev(values)
            if stdev == 0:
                return 0.0
            return abs(current - mean) / stdev
        except statistics.StatisticsError:
            return 0.0
    
    def _calculate_iqr_bounds(self, values: List[float]) -> tuple[float, float]:
        """محاسبه محدوده IQR"""
        if len(values) < 4:
            return (float('-inf'), float('inf'))
        
        sorted_values = sorted(values)
        q1 = statistics.median(sorted_values[:len(sorted_values)//2])
        q3 = statistics.median(sorted_values[(len(sorted_values)+1)//2:])
        iqr = q3 - q1
        
        lower = q1 - self._iqr_multiplier * iqr
        upper = q3 + self._iqr_multiplier * iqr
        
        return (lower, upper)
    
    def detect_anomalies(self) -> List[AnomalyAlert]:
        """
        تشخیص تمام ناهنجاری‌های فعلی
        
        Returns:
            لیست هشدارهای ناهنجاری
        """
        anomalies = []
        
        with self._lock:
            for metric_name, values in self._metrics.items():
                if len(values) < self._min_samples:
                    continue
                
                current_value = values[-1]
                historical_values = list(values)[:-1]  # همه به جز آخرین
                
                # روش Z-score
                z_score = self._calculate_z_score(historical_values, current_value)
                if z_score > self._z_threshold:
                    mean = statistics.mean(historical_values)
                    stdev = statistics.stdev(historical_values) if len(historical_values) > 1 else 0
                    
                    severity = "high" if z_score > self._z_threshold * 1.5 else "medium"
                    
                    anomalies.append(AnomalyAlert(
                        metric_name=metric_name,
                        current_value=current_value,
                        expected_range=(mean - stdev, mean + stdev),
                        severity=severity,
                        timestamp=datetime.now(timezone.utc),
                        z_score=z_score,
                        message=f"متریک {metric_name} با مقدار {current_value:.2f} دارای Z-score={z_score:.2f} است (آستانه: {self._z_threshold})"
                    ))
                    continue
                
                # روش IQR
                lower, upper = self._calculate_iqr_bounds(historical_values)
                if current_value < lower or current_value > upper:
                    anomalies.append(AnomalyAlert(
                        metric_name=metric_name,
                        current_value=current_value,
                        expected_range=(lower, upper),
                        severity="low",
                        timestamp=datetime.now(timezone.utc),
                        z_score=None,
                        message=f"متریک {metric_name} با مقدار {current_value:.2f} خارج از محدوده IQR است [{lower:.2f}, {upper:.2f}]"
                    ))
        
        return anomalies
    
    def get_metric_stats(self, metric_name: str) -> Optional[Dict]:
        """دریافت آمار یک متریک"""
        with self._lock:
            if metric_name not in self._metrics:
                return None
            
            values = list(self._metrics[metric_name])
            if not values:
                return None
            
            return {
                "count": len(values),
                "mean": statistics.mean(values),
                "median": statistics.median(values),
                "min": min(values),
                "max": max(values),
                "stdev": statistics.stdev(values) if len(values) > 1 else 0,
            }
