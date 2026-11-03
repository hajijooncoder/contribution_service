import React, { useEffect, useState } from 'react';
import { ContributionHistoryItem } from '../types';
import { apiClient } from '../api/client';
import { Clock, CheckCircle2, XCircle, AlertTriangle, ShieldCheck, RefreshCw } from 'lucide-react';

export const ContributionHistory: React.FC = () => {
  const [history, setHistory] = useState<ContributionHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchHistory = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiClient.getMyHistory();
      setHistory(data);
    } catch (err: any) {
      setError(err.message || 'خطا در دریافت تاریخچه مشارکت‌ها.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'approved':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <CheckCircle2 className="w-3.5 h-3.5" />
            تأیید نهایی شده
          </span>
        );
      case 'rejected':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-rose-500/10 text-rose-400 border border-rose-500/20">
            <XCircle className="w-3.5 h-3.5" />
            رد شده
          </span>
        );
      case 'quarantined':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20">
            <AlertTriangle className="w-3.5 h-3.5" />
            قرنطینه امنیتی
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-sky-500/10 text-sky-400 border border-sky-500/20">
            <Clock className="w-3.5 h-3.5" />
            در حال داوری همتا
          </span>
        );
    }
  };

  return (
    <div className="max-w-5xl mx-auto py-8 px-4 sm:px-6">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-2xl font-bold text-white mb-1">تاریخچه مشارکت‌های حقوقی شما</h2>
          <p className="text-xs text-slate-400">
            پیگیری وضعیت بررسی، تعداد آرای داوران و امتیازهای مکتسبه
          </p>
        </div>
        <button
          onClick={fetchHistory}
          disabled={loading}
          className="p-2.5 rounded-xl border border-slate-800 bg-slate-900 text-slate-300 hover:text-white hover:bg-slate-800 transition-colors"
          title="بروزرسانی"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {error && (
        <div className="mb-6 p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs">
          {error}
        </div>
      )}

      {loading ? (
        <div className="text-center py-16 text-slate-500 text-sm">
          در حال بارگذاری مشارکت‌ها...
        </div>
      ) : history.length === 0 ? (
        <div className="text-center py-16 bg-slate-900 border border-slate-800 rounded-2xl p-8">
          <ShieldCheck className="w-12 h-12 text-slate-600 mx-auto mb-4" />
          <h3 className="text-base font-semibold text-slate-300 mb-1">هنوز مشارکتی ثبت نکرده‌اید</h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto mb-6">
            با ارسال قوانین، آیین‌نامه‌ها و آرای قضایی جدید، در توسعه گراف دانش حقوقی مشارکت کنید.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {history.map((item) => (
            <div
              key={item.id}
              className="p-5 rounded-2xl bg-slate-900 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:border-slate-700 transition-colors"
            >
              <div>
                <div className="flex items-center gap-3 mb-2">
                  <span className="text-base font-bold text-slate-100">{item.title}</span>
                  <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-amber-400 border border-slate-700">
                    {item.document_type}
                  </span>
                </div>
                <div className="flex items-center gap-4 text-xs text-slate-400">
                  <span>شناسه: {item.id.slice(0, 8)}...</span>
                  <span>تاریخ: {new Date(item.created_at).toLocaleDateString('fa-IR')}</span>
                  <span>امتیاز کیفیت: {item.quality_score} / ۱۰۰</span>
                </div>
              </div>

              <div className="flex items-center gap-4">
                <div className="text-left sm:text-right">
                  <div className="text-[11px] text-slate-400">پیشرفت داوری همتا:</div>
                  <div className="text-xs font-mono font-bold text-slate-200">
                    {item.current_approvals} از {item.required_reviewers} رأی تایید
                  </div>
                </div>
                {getStatusBadge(item.status)}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
