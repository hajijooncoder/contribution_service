"""
Data Retention Policy Manager
مدیریت خط‌مشی نگهداری داده

Provides:
- Configurable retention policies per data type
- Automated cleanup of old records
- Safe deletion with transaction support
"""

from datetime import datetime, timedelta
from typing import Dict
from sqlalchemy.orm import Session

from app.db.models import Submission, AuditLog


# خط‌مشی‌های نگهداری برای سرویس مشارکت
RetentionPolicies: Dict[str, int] = {
    "audit_logs": 90,           # 90 روز برای لاگ‌های audit
    "submission_drafts": 30,    # 30 روز برای پیش‌نویس‌های submission
    "rate_limit_state": 7,      # 7 روز برای وضعیت rate limiting
    "anomaly_history": 30,      # 30 روز برای تاریخچه ناهنجاری‌ها
    "alert_history": 90,        # 90 روز برای تاریخچه هشدارها
    "diagnostic_reports": 90,   # 90 روز برای گزارش‌های تشخیصی
}


class RetentionManager:
    """
    مدیر خط‌مشی نگهداری داده
    
    حذف امن رکوردهای قدیمی بر اساس خط‌مشی‌های تعریف شده
    """
    
    def __init__(self, policies: Dict[str, int] = None):
        """
        Args:
            policies: دیکشنری خط‌مشی‌ها (نام -> تعداد روز)
        """
        self.policies = policies or RetentionPolicies
    
    def cleanup_old_records(
        self,
        db: Session,
        policy_name: str
    ) -> int:
        """
        حذف رکوردهای قدیمی بر اساس خط‌مشی
        
        Args:
            db: نشست دیتابیس
            policy_name: نام خط‌مشی
        
        Returns:
            تعداد رکوردهای حذف شده
        """
        if policy_name not in self.policies:
            raise ValueError(f"خط‌مشی {policy_name} تعریف نشده است")
        
        retention_days = self.policies[policy_name]
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        deleted_count = 0
        
        try:
            if policy_name == "audit_logs":
                deleted_count = self._cleanup_audit_logs(db, cutoff_date)
            
            elif policy_name == "submission_drafts":
                deleted_count = self._cleanup_submission_drafts(db, cutoff_date)
            
            elif policy_name in ("rate_limit_state", "anomaly_history", "alert_history", "diagnostic_reports"):
                # این موارد در حافظه هستند، نیازی به cleanup دیتابیس ندارند
                # می‌توان در آینده با ذخیره‌سازی persistent پیاده‌سازی شود
                deleted_count = 0
            
            db.commit()
            return deleted_count
        
        except Exception as e:
            db.rollback()
            raise e
    
    def _cleanup_audit_logs(self, db: Session, cutoff_date: datetime) -> int:
        """حذف لاگ‌های audit قدیمی"""
        # فقط لاگ‌های غیرحیاتی را حذف می‌کنیم
        result = db.query(AuditLog).filter(
            AuditLog.timestamp < cutoff_date,
            AuditLog.action.notin_(["submission_approved", "submission_rejected"])
        ).delete(synchronize_session=False)
        
        return result
    
    def _cleanup_submission_drafts(self, db: Session, cutoff_date: datetime) -> int:
        """حذف پیش‌نویس‌های قدیمی submission"""
        # فقط submission‌های در وضعیت draft که قدیمی هستند
        result = db.query(Submission).filter(
            Submission.created_at < cutoff_date,
            Submission.status == "draft"
        ).delete(synchronize_session=False)
        
        return result
    
    def get_policy(self, policy_name: str) -> int:
        """دریافت تعداد روز نگهداری برای یک خط‌مشی"""
        return self.policies.get(policy_name, 0)
    
    def set_policy(self, policy_name: str, retention_days: int) -> None:
        """تنظیم خط‌مشی نگهداری"""
        if retention_days < 1:
            raise ValueError("تعداد روز نگهداری باید حداقل 1 باشد")
        
        self.policies[policy_name] = retention_days
