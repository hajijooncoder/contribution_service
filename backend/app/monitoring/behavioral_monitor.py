"""
Behavioral Monitoring System
سیستم نظارت رفتاری کاربران

Provides:
- Per-user activity pattern tracking
- Anomaly detection in user behavior
- Abuse pattern detection
- Submission/review rate monitoring
"""

import time
from collections import defaultdict, deque
from dataclasses import dataclass
from threading import RLock
from typing import Dict, List, Optional


@dataclass
class UserBehaviorProfile:
    """پروفایل رفتاری کاربر"""
    user_id: int
    submission_count: int = 0
    review_count: int = 0
    duplicate_count: int = 0
    quality_scores: List[float] = None
    last_activity: float = 0
    recent_submissions: deque = None  # (timestamp, quality_score)
    recent_reviews: deque = None  # (timestamp, decision)
    
    def __post_init__(self):
        if self.quality_scores is None:
            self.quality_scores = []
        if self.recent_submissions is None:
            self.recent_submissions = deque(maxlen=100)
        if self.recent_reviews is None:
            self.recent_reviews = deque(maxlen=100)


class BehavioralMonitor:
    """
    سیستم نظارت رفتاری برای تشخیص الگوهای مشکوک:
    - افزایش ناگهانی تعداد submission
    - افت کیفیت ناگهانی
    - الگوی رد مکرر در review
    - عدم فعالیت طولانی‌مدت
    
    Thread-safe
    """
    
    def __init__(
        self,
        submission_burst_threshold: int = 10,  # 10 submission در 5 دقیقه
        submission_burst_window: int = 300,     # 5 دقیقه
        quality_drop_threshold: float = 20.0,   # افت 20 امتیازی
        review_rejection_threshold: float = 0.8, # 80% رد
        inactivity_threshold: int = 86400 * 7   # 7 روز
    ):
        self._lock = RLock()
        self._profiles: Dict[int, UserBehaviorProfile] = {}
        
        # آستانه‌ها
        self._submission_burst_threshold = submission_burst_threshold
        self._submission_burst_window = submission_burst_window
        self._quality_drop_threshold = quality_drop_threshold
        self._review_rejection_threshold = review_rejection_threshold
        self._inactivity_threshold = inactivity_threshold
    
    def _get_or_create_profile(self, user_id: int) -> UserBehaviorProfile:
        """دریافت یا ایجاد پروفایل کاربر"""
        if user_id not in self._profiles:
            self._profiles[user_id] = UserBehaviorProfile(user_id=user_id)
        return self._profiles[user_id]
    
    def record_submission(self, user_id: int, quality_score: float) -> None:
        """ثبت یک submission"""
        with self._lock:
            profile = self._get_or_create_profile(user_id)
            
            now = time.time()
            profile.submission_count += 1
            profile.quality_scores.append(quality_score)
            profile.recent_submissions.append((now, quality_score))
            profile.last_activity = now
    
    def record_review(self, user_id: int, decision: str) -> None:
        """ثبت یک review"""
        with self._lock:
            profile = self._get_or_create_profile(user_id)
            
            now = time.time()
            profile.review_count += 1
            profile.recent_reviews.append((now, decision))
            profile.last_activity = now
    
    def record_duplicate(self, user_id: int) -> None:
        """ثبت تشخیص تکراری"""
        with self._lock:
            profile = self._get_or_create_profile(user_id)
            profile.duplicate_count += 1
    
    def detect_anomalies(self) -> List[str]:
        """
        تشخیص ناهنجاری‌های رفتاری
        
        Returns:
            لیست هشدارهای رفتاری
        """
        warnings = []
        now = time.time()
        
        with self._lock:
            for user_id, profile in self._profiles.items():
                # 1. تشخیص burst در submission
                recent_burst_count = sum(
                    1 for ts, _ in profile.recent_submissions
                    if now - ts < self._submission_burst_window
                )
                if recent_burst_count >= self._submission_burst_threshold:
                    warnings.append(
                        f"کاربر {user_id}: فعالیت غیرعادی - {recent_burst_count} submission در {self._submission_burst_window // 60} دقیقه"
                    )
                
                # 2. تشخیص افت کیفیت
                if len(profile.quality_scores) >= 5:
                    recent_avg = sum(profile.quality_scores[-5:]) / 5
                    overall_avg = sum(profile.quality_scores) / len(profile.quality_scores)
                    
                    if overall_avg - recent_avg > self._quality_drop_threshold:
                        warnings.append(
                            f"کاربر {user_id}: افت کیفیت - از {overall_avg:.1f} به {recent_avg:.1f}"
                        )
                
                # 3. تشخیص نرخ بالای رد در review
                if len(profile.recent_reviews) >= 10:
                    recent_rejections = sum(
                        1 for _, decision in list(profile.recent_reviews)[-10:]
                        if decision == "reject"
                    )
                    rejection_rate = recent_rejections / 10
                    
                    if rejection_rate >= self._review_rejection_threshold:
                        warnings.append(
                            f"کاربر {user_id}: نرخ بالای رد review - {rejection_rate * 100:.0f}%"
                        )
                
                # 4. تشخیص نرخ بالای duplicate
                if profile.submission_count >= 10:
                    duplicate_rate = profile.duplicate_count / profile.submission_count
                    if duplicate_rate > 0.5:  # بیش از 50% تکراری
                        warnings.append(
                            f"کاربر {user_id}: نرخ بالای تکراری - {duplicate_rate * 100:.0f}%"
                        )
                
                # 5. تشخیص عدم فعالیت
                if profile.last_activity > 0:
                    inactive_duration = now - profile.last_activity
                    if inactive_duration > self._inactivity_threshold:
                        warnings.append(
                            f"کاربر {user_id}: عدم فعالیت - {int(inactive_duration / 86400)} روز"
                        )
        
        return warnings
    
    def get_user_profile(self, user_id: int) -> Optional[UserBehaviorProfile]:
        """دریافت پروفایل رفتاری کاربر"""
        with self._lock:
            return self._profiles.get(user_id)
    
    def get_stats(self) -> Dict:
        """آمار کلی"""
        with self._lock:
            total_users = len(self._profiles)
            total_submissions = sum(p.submission_count for p in self._profiles.values())
            total_reviews = sum(p.review_count for p in self._profiles.values())
            
            return {
                "total_users_tracked": total_users,
                "total_submissions": total_submissions,
                "total_reviews": total_reviews,
                "avg_submissions_per_user": total_submissions / total_users if total_users > 0 else 0,
                "avg_reviews_per_user": total_reviews / total_users if total_users > 0 else 0,
            }
