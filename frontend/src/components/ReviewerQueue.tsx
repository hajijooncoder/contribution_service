import React, { useEffect, useState } from 'react';
import { ReviewQueueItem } from '../types';
import { apiClient } from '../api/client';
import {
  CheckCircle2,
  XCircle,
  RefreshCw,
  Globe,
  Scale,
  ShieldCheck,
  AlertTriangle,
  FileText,
  ExternalLink,
  Award,
} from 'lucide-react';

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
      const mappedDecision = decision === 'approved' ? 'approve' : 'reject';
      await apiClient.submitReview(submissionId, mappedDecision, notes);
      setQueue((prev) => prev.filter((item) => item.id !== submissionId));
    } catch (err: any) {
      alert(`خطا در ثبت رأی داوری: ${err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  return (
    <div className="max-w-5xl mx-auto py-10 px-4 sm:px-6 font-sans">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-[#00e5ff]/40 bg-[#0b1e36] text-[11px] font-mono text-[#00e5ff] font-semibold mb-2">
            <Scale className="w-3.5 h-3.5" />
            <span>PEER REVIEW CONSOLE</span>
          </div>
          <h2 className="text-2xl font-bold text-white mb-1">میزکار و کارتابل داوری همتا</h2>
          <p className="text-xs text-slate-400">
            بررسی صحت حقوقی، ارزیابی منابع رسمی، و ثبت رأی در چارچوب حدنصاب اجماع (Consensus Quorum)
          </p>
        </div>
        <button
          onClick={fetchQueue}
          disabled={loading}
          className="p-2.5 rounded-xl border border-[#112d4e] bg-[#071527] text-slate-300 hover:text-white hover:bg-[#0b1e36] hover:border-[#00e5ff]/40 transition-all self-start sm:self-auto shadow-sm"
          title="بروزرسانی صف"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {error && (
        <div className="mb-6 p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs shadow-md">
          {error}
        </div>
      )}

      {loading ? (
        <div className="text-center py-20 text-slate-400 text-sm">
          در حال بارگذاری صف داوری...
        </div>
      ) : queue.length === 0 ? (
        <div className="text-center py-20 bg-[#071527] border border-[#112d4e] rounded-2xl p-8 shadow-xl">
          <div className="w-16 h-16 rounded-2xl bg-[#0b1e36] border border-emerald-500/30 flex items-center justify-center mx-auto mb-4 text-emerald-400 shadow-md">
            <CheckCircle2 className="w-8 h-8" />
          </div>
          <h3 className="text-base font-bold text-slate-200 mb-1">
            هیچ سندی در انتظار داوری شما نیست
          </h3>
          <p className="text-xs text-slate-400 max-w-sm mx-auto leading-relaxed">
            تمام مشارکت‌های ارسالی یا بررسی شده‌اند و یا نیاز به داوری جدید ندارند.
          </p>
        </div>
      ) : (
        <div className="space-y-6">
          {queue.map((item) => (
            <div
              key={item.id}
              className="p-6 sm:p-7 rounded-2xl bg-[#071527] border border-[#112d4e] shadow-xl space-y-5 hover:border-[#112d4e]/90 transition-all"
            >
              {/* Document Header */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#112d4e] pb-4">
                <div>
                  <h3 className="text-lg font-bold text-white tracking-tight">
                    {item.legal_document_name}
                  </h3>
                  <div className="text-xs text-slate-400 flex items-center gap-3 mt-1.5 flex-wrap">
                    <span className="font-medium text-slate-300">مرجع: {item.issuing_authority}</span>
                    <span>•</span>
                    <span className="px-2 py-0.5 rounded bg-[#0b1e36] text-[#00e5ff] font-mono text-[11px] border border-[#00e5ff]/30">
                      نوع: {item.document_type}
                    </span>
                    <span>•</span>
                    <span className="font-mono text-slate-300">
                      امتیاز کیفی: {item.quality_score}/۱۰۰
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-2 flex-wrap">
                  <span className="px-3.5 py-1.5 rounded-xl text-xs font-mono bg-[#0b1e36] text-[#00e5ff] border border-[#00e5ff]/30 font-bold shadow-sm">
                    رأی فعلی: {item.current_approvals} از {item.required_reviewers}
                  </span>
                  {item.detected_risk_level === 'HIGH' && (
                    <span className="px-3.5 py-1.5 rounded-xl text-xs font-mono bg-rose-500/10 text-rose-300 border border-rose-500/30 flex items-center gap-1 font-bold">
                      <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
                      <span>ریسک بالا (نیازمند ۲ داور)</span>
                    </span>
                  )}
                </div>
              </div>

              {/* Source Link Reference */}
              <div className="text-xs flex items-center gap-2 p-3 rounded-xl bg-[#030712] border border-[#112d4e] text-slate-400">
                <Globe className="w-4 h-4 text-[#00e5ff] shrink-0" />
                <span className="shrink-0 font-medium text-slate-300">لینک منبع رسمی:</span>
                <a
                  href={item.source_url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-[#00e5ff] hover:underline truncate max-w-md font-mono flex items-center gap-1"
                >
                  <span className="truncate">{item.source_url}</span>
                  <ExternalLink className="w-3 h-3 shrink-0" />
                </a>
              </div>

              {/* Legal Text Review Box */}
              <div className="space-y-1.5">
                <span className="text-xs font-semibold text-slate-400 block">
                  متن ماده قانونی / دادنامه جهت انطباق با منبع رسمی:
                </span>
                <div className="p-4 rounded-xl bg-[#030712] border border-[#112d4e] text-xs text-slate-200 font-sans leading-relaxed max-h-52 overflow-y-auto">
                  {item.raw_legal_text}
                </div>
              </div>

              {/* Decision Actions */}
              <div className="flex items-center justify-between pt-2 border-t border-[#112d4e] flex-wrap gap-3">
                <div className="text-xs text-slate-400 flex items-center gap-1.5">
                  <ShieldCheck className="w-4 h-4 text-[#00e5ff]" />
                  <span>آرای داوری پس از تطبیق با استانداردهای استنادی ثبت نهایی می‌شوند.</span>
                </div>

                <div className="flex items-center space-x-3 space-x-reverse">
                  <button
                    onClick={() => handleDecision(item.id, 'rejected', 'عدم انطباق با منبع رسمی')}
                    disabled={actionLoading === item.id}
                    className="flex items-center space-x-1.5 space-x-reverse px-4 py-2.5 rounded-xl border border-rose-500/40 hover:bg-rose-500/10 text-rose-300 text-xs font-semibold transition-all disabled:opacity-50"
                  >
                    <XCircle className="w-4 h-4" />
                    <span>رد مشارکت</span>
                  </button>

                  <button
                    onClick={() => handleDecision(item.id, 'approved', 'تأیید صحت و اصالت سند')}
                    disabled={actionLoading === item.id}
                    className="flex items-center space-x-1.5 space-x-reverse px-5 py-2.5 rounded-xl bg-gradient-to-r from-emerald-500 to-emerald-600 hover:from-emerald-400 hover:to-emerald-500 text-slate-950 text-xs font-bold transition-all shadow-md shadow-emerald-500/20 disabled:opacity-50"
                  >
                    <CheckCircle2 className="w-4 h-4" />
                    <span>تأیید و اعمال رأی</span>
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
