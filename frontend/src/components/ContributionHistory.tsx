import React, { useEffect, useState, useCallback } from 'react';
import { ContributionHistoryItem, ContributionSearchItem } from '../types';
import { apiClient } from '../api/client';
import { Clock, CheckCircle2, XCircle, AlertTriangle, ShieldCheck, RefreshCw, Search, Filter, X } from 'lucide-react';

export const ContributionHistory: React.FC = () => {
  const [history, setHistory] = useState<ContributionHistoryItem[]>([]);
  const [searchResults, setSearchResults] = useState<ContributionSearchItem[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Search & filter state
  const [query, setQuery] = useState('');
  const [docType, setDocType] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [authority, setAuthority] = useState('');

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

  const handleSearch = useCallback(async () => {
    const hasFilter = query.trim() || docType || statusFilter || authority.trim();
    if (!hasFilter) {
      setSearchResults(null);
      return;
    }

    setSearching(true);
    setError(null);
    try {
      const res = await apiClient.searchContributions({
        q: query.trim() || undefined,
        document_type: docType || undefined,
        status_filter: statusFilter || undefined,
        issuing_authority: authority.trim() || undefined,
      });
      setSearchResults(res.items);
    } catch (err: any) {
      setError(err.message || 'خطا در جستجوی مشارکت‌ها.');
    } finally {
      setSearching(false);
    }
  }, [query, docType, statusFilter, authority]);

  const clearFilters = () => {
    setQuery('');
    setDocType('');
    setStatusFilter('');
    setAuthority('');
    setSearchResults(null);
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'accepted':
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

  const isSearchActive = Boolean(searchResults !== null);
  const displayedItems = searchResults !== null ? searchResults : history;

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
          onClick={() => {
            if (isSearchActive) {
              handleSearch();
            } else {
              fetchHistory();
            }
          }}
          disabled={loading || searching}
          className="p-2.5 rounded-xl border border-slate-800 bg-slate-900 text-slate-300 hover:text-white hover:bg-slate-800 transition-colors"
          title="بروزرسانی"
        >
          <RefreshCw className={`w-4 h-4 ${loading || searching ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Advanced Search & Filter Bar */}
      <div className="mb-6 p-4 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-3">
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="w-4 h-4 absolute right-3.5 top-3.5 text-slate-500" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="جستجو در عنوان، متن قانون یا مرجع تصویب..."
              className="w-full bg-slate-950 border border-slate-800 rounded-xl pr-10 pl-4 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-amber-500 transition-colors"
            />
            {query && (
              <button
                onClick={() => setQuery('')}
                className="absolute left-3 top-3 text-slate-500 hover:text-slate-300"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>
          <button
            onClick={handleSearch}
            disabled={searching}
            className="px-5 py-2.5 bg-amber-500 hover:bg-amber-600 disabled:opacity-50 text-slate-950 font-bold text-xs rounded-xl flex items-center justify-center gap-2 transition-colors shrink-0"
          >
            <Filter className="w-4 h-4" />
            <span>اعمال فیلتر</span>
          </button>
        </div>

        {/* Filter Dropdowns */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2 border-t border-slate-800/60 text-xs">
          <div>
            <label className="block text-[11px] text-slate-400 mb-1">نوع سند:</label>
            <select
              value={docType}
              onChange={(e) => setDocType(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-slate-300 focus:outline-none focus:border-amber-500"
            >
              <option value="">همه انواع اسناد</option>
              <option value="law">قانون مصوب مجلس</option>
              <option value="regulation">آیین‌نامه و تصویب‌نامه</option>
              <option value="judicial_ruling">رأی قضایی / وحدت رویه</option>
              <option value="circular">بخشنامه رسمی</option>
              <option value="statute">اساسنامه</option>
              <option value="other">سایر اسناد حقوقی</option>
            </select>
          </div>

          <div>
            <label className="block text-[11px] text-slate-400 mb-1">وضعیت داوری:</label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-slate-300 focus:outline-none focus:border-amber-500"
            >
              <option value="">همه وضعیت‌ها</option>
              <option value="submitted">ثبت اولیه در قرنطینه</option>
              <option value="under_legal_review">در حال بررسی داوران</option>
              <option value="accepted">تأیید نهایی شده</option>
              <option value="rejected">رد شده</option>
            </select>
          </div>

          <div>
            <label className="block text-[11px] text-slate-400 mb-1">مرجع تصویب:</label>
            <input
              type="text"
              value={authority}
              onChange={(e) => setAuthority(e.target.value)}
              placeholder="مثلاً: مجلس، دیوان عالی..."
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-slate-300 placeholder-slate-600 focus:outline-none focus:border-amber-500"
            />
          </div>
        </div>

        {isSearchActive && (
          <div className="flex items-center justify-between pt-2 border-t border-slate-800/40 text-xs">
            <span className="text-amber-400">
              نتایج فیلتر: {displayedItems.length} مورد یافت شد
            </span>
            <button
              onClick={clearFilters}
              className="text-slate-400 hover:text-white flex items-center gap-1"
            >
              <X className="w-3.5 h-3.5" />
              <span>پاک کردن فیلترها</span>
            </button>
          </div>
        )}
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
      ) : displayedItems.length === 0 ? (
        <div className="text-center py-16 bg-slate-900 border border-slate-800 rounded-2xl p-8">
          <ShieldCheck className="w-12 h-12 text-slate-600 mx-auto mb-4" />
          <h3 className="text-base font-semibold text-slate-300 mb-1">
            {isSearchActive ? 'موردی مطابق با فیلترهای جستجو یافت نشد' : 'هنوز مشارکتی ثبت نکرده‌اید'}
          </h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto mb-6">
            {isSearchActive
              ? 'لطفاً عبارت جستجو یا شروط فیلتر را تغییر دهید.'
              : 'با ارسال قوانین، آیین‌نامه‌ها و آرای قضایی جدید، در توسعه گراف دانش حقوقی مشارکت کنید.'}
          </p>
          {isSearchActive && (
            <button
              onClick={clearFilters}
              className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs transition-colors"
            >
              مشاهده تمام مشارکت‌ها
            </button>
          )}
        </div>
      ) : (
        <div className="space-y-4">
          {displayedItems.map((item: any) => {
            const itemTitle = item.legal_document_name || item.title || item.source || 'سند حقوقی بدون عنوان';
            const itemDocType = item.document_type || 'قانون';
            const itemDate = item.date || (item.created_at ? new Date(item.created_at).toLocaleDateString('fa-IR') : '—');
            const itemScore = item.quality_score ?? 0;
            const itemApprovals = item.current_approvals ?? 0;
            const itemReq = item.required_reviewers ?? 1;

            return (
              <div
                key={item.id}
                className="p-5 rounded-2xl bg-slate-900 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:border-slate-700 transition-colors"
              >
                <div>
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-base font-bold text-slate-100">{itemTitle}</span>
                    <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-amber-400 border border-slate-700">
                      {itemDocType}
                    </span>
                    {item.issuing_authority && (
                      <span className="text-xs px-2 py-0.5 rounded bg-slate-800/60 text-slate-400">
                        {item.issuing_authority}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-4 text-xs text-slate-400">
                    <span>شناسه: {item.id.slice(0, 8)}...</span>
                    <span>تاریخ: {itemDate}</span>
                    <span>امتیاز کیفیت: {itemScore} / ۱۰۰</span>
                    {item.awarded_credits > 0 && (
                      <span className="text-emerald-400 font-mono">+{item.awarded_credits} اعتبار</span>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-4">
                  <div className="text-left sm:text-right">
                    <div className="text-[11px] text-slate-400">پیشرفت داوری همتا:</div>
                    <div className="text-xs font-mono font-bold text-slate-200">
                      {itemApprovals} از {itemReq} رأی تایید
                    </div>
                  </div>
                  {getStatusBadge(item.status)}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
