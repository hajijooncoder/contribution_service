import React, { useEffect, useState } from 'react';
import { ReviewQueueItem } from '../types';
import { apiClient } from '../api/client';
import { CheckCircle2, XCircle, RefreshCw, Globe } from 'lucide-react';

export const ReviewerQueue: React.FC = () => {
  const [queue, setQueue] = useState<ReviewQueueItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const fetchQueue = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiClient.getReviewQueue();
      setQueue(data);
    } catch (err: any) {
      setError(err.message || 'خطا در دریافت صف داوری.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQueue();
  }, []);

  const handleDecision = async (
    submissionId: string,
    decision: 'approved' | 'rejected',
    notes?: string
  ) => {
    setActionLoading(submissionId);
    try {
      await apiClient.submitReview(submissionId, decision, notes);
      setQueue((prev) => prev.filter((item) => item.id !== submissionId));
    } catch (err: any) {
      alert(`خطا در ثبت رأی داوری: ${err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  return (
    <div className="max-w-5xl mx-auto py-8 px-4 sm:px-6">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-2xl font-bold text-white mb-1">میزکار و کارتابل داوری همتا</h2>
          <p className="text-xs text-slate-400">
            بررسی صحت حقوقی، ارزیابی منابع رسمی، و ثبت رأی در چارچوب حدنصاب اجماع (Consensus Quorum)
          </p>
        </div>
        <button
          onClick={fetchQueue}
          disabled={loading}
          className="p-2.5 rounded-xl border border-slate-800 bg-slate-900 text-slate-300 hover:text-white hover:bg-slate-800 transition-colors"
          title="بروزرسانی صف"
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
        <div className="text-center py-16 text-slate-500 text-sm">در حال بارگذاری صف داوری...</div>
      ) : queue.length === 0 ? (
        <div className="text-center py-16 bg-slate-900 border border-slate-800 rounded-2xl p-8">
          <CheckCircle2 className="w-12 h-12 text-emerald-500/80 mx-auto mb-4" />
          <h3 className="text-base font-semibold text-slate-300 mb-1">
            هیچ سندی در انتظار داوری شما نیست
          </h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            تمام مشارکت‌های ارسالی یا بررسی شده‌اند و یا نیاز به داوری جدید ندارند.
          </p>
        </div>
      ) : (
        <div className="space-y-6">
          {queue.map((item) => (
            <div
              key={item.id}
              className="p-6 rounded-2xl bg-slate-900 border border-slate-800 shadow-lg space-y-4"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-4">
                <div>
                  <h3 className="text-lg font-bold text-white">{item.legal_document_name}</h3>
                  <div className="text-xs text-slate-400 flex items-center gap-3 mt-1">
                    <span>مرجع: {item.issuing_authority}</span>
                    <span>•</span>
                    <span>نوع: {item.document_type}</span>
                    <span>•</span>
                    <span>امتیاز کیفی: {item.quality_score}/۱۰۰</span>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <span className="px-3 py-1 rounded-full text-xs font-mono bg-amber-500/10 text-amber-300 border border-amber-500/20">
                    رأی فعلی: {item.current_approvals} از {item.required_reviewers}
                  </span>
                  {item.detected_risk_level === 'HIGH' && (
                    <span className="px-3 py-1 rounded-full text-xs font-mono bg-rose-500/10 text-rose-300 border border-rose-500/20">
                      ریسک بالا (نیازمند ۲ داور)
                    </span>
                  )}
                </div>
              </div>

              {/* Source link */}
              <div className="text-xs flex items-center gap-2 text-slate-400">
                <Globe className="w-3.5 h-3.5 text-amber-400" />
                <span>لینک منبع رسمی:</span>
                <a
                  href={item.source_url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-amber-400 hover:underline truncate max-w-md font-mono"
                >
                  {item.source_url}
                </a>
              </div>

              {/* Legal Text snippet */}
              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-300 font-sans leading-relaxed max-h-48 overflow-y-auto">
                {item.raw_legal_text}
              </div>

              {/* Actions */}
              <div className="flex items-center justify-end space-x-3 space-x-reverse pt-2">
                <button
                  onClick={() => handleDecision(item.id, 'rejected', 'عدم انطباق با منبع رسمی')}
                  disabled={actionLoading === item.id}
                  className="flex items-center space-x-1.5 space-x-reverse px-4 py-2 rounded-xl border border-rose-500/30 hover:bg-rose-500/10 text-rose-300 text-xs font-semibold transition-colors disabled:opacity-50"
                >
                  <XCircle className="w-4 h-4" />
                  <span>رد مشارکت</span>
                </button>

                <button
                  onClick={() => handleDecision(item.id, 'approved', 'تأیید صحت و اصالت سند')}
                  disabled={actionLoading === item.id}
                  className="flex items-center space-x-1.5 space-x-reverse px-5 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 text-xs font-bold transition-all shadow-md shadow-emerald-500/20 disabled:opacity-50"
                >
                  <CheckCircle2 className="w-4 h-4" />
                  <span>تأیید و اعمال رأی</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
