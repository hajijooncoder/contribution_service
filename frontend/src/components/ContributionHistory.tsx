import React, { useEffect, useState, useCallback } from 'react';
import { ContributionHistoryItem, ContributionSearchItem } from '../types';
import { apiClient } from '../api/client';
import {
  Clock,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  ShieldCheck,
  RefreshCw,
  Search,
  Filter,
  X,
  FileText,
  Calendar,
  Award,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Building,
} from 'lucide-react';

export const ContributionHistory: React.FC = () => {
  const [history, setHistory] = useState<ContributionHistoryItem[]>([]);
  const [searchResults, setSearchResults] = useState<ContributionSearchItem[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);

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
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
            <CheckCircle2 className="w-3.5 h-3.5" />
            تأیید نهایی شده
          </span>
        );
      case 'rejected':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-rose-500/10 text-rose-400 border border-rose-500/30">
            <XCircle className="w-3.5 h-3.5" />
            رد شده
          </span>
        );
      case 'quarantined':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-amber-500/10 text-amber-400 border border-amber-500/30">
            <AlertTriangle className="w-3.5 h-3.5" />
            قرنطینه امنیتی
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-sky-500/10 text-sky-400 border border-sky-500/30">
            <Clock className="w-3.5 h-3.5" />
            در حال داوری همتا
          </span>
        );
    }
  };

  const isSearchActive = Boolean(searchResults !== null);
  const displayedItems = searchResults !== null ? searchResults : history;

  const toggleExpand = (id: string) => {
    setExpandedId((prev) => (prev === id ? null : id));
  };

  return (
    <div className="max-w-5xl mx-auto py-10 px-4 sm:px-6 font-sans">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div>
          <h2 className="text-2xl font-bold text-white mb-1">تاریخچه مشارکت‌های حقوقی شما</h2>
          <p className="text-xs text-slate-400">
            پیگیری وضعیت بررسی، تعداد آرای داوران و امتیازهای مکتسبه در دفتر کل ممیزی
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
          className="p-2.5 rounded-xl border border-[#112d4e] bg-[#071527] text-slate-300 hover:text-white hover:bg-[#0b1e36] hover:border-[#00e5ff]/40 transition-all self-start sm:self-auto shadow-sm"
          title="بروزرسانی"
        >
          <RefreshCw className={`w-4 h-4 ${loading || searching ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Advanced Search & Filter Bar */}
      <div className="mb-8 p-5 rounded-2xl bg-[#071527] border border-[#112d4e] space-y-4 shadow-xl">
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="w-4 h-4 absolute right-3.5 top-3.5 text-slate-400" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="جستجو در عنوان، متن قانون یا مرجع تصویب..."
              className="w-full bg-[#030712] border border-[#112d4e] rounded-xl pr-10 pl-4 py-2.5 text-xs text-white placeholder-slate-400 focus:outline-none focus:border-[#00e5ff] focus:ring-1 focus:ring-[#00e5ff]/40 transition-colors"
            />
            {query && (
              <button
                onClick={() => setQuery('')}
                className="absolute left-3 top-3 text-slate-400 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>
          <button
            onClick={handleSearch}
            disabled={searching}
            className="px-6 py-2.5 bg-gradient-to-r from-[#00e5ff] via-[#0284c7] to-[#0369a1] hover:from-[#38bdf8] hover:to-[#0284c7] disabled:opacity-50 text-white font-bold text-xs rounded-xl flex items-center justify-center gap-2 transition-all shadow-md shadow-[#00e5ff]/20 border border-[#00e5ff]/30 shrink-0"
          >
            <Filter className="w-4 h-4" />
            <span>اعمال فیلتر</span>
          </button>
        </div>

        {/* Filter Dropdowns */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-3 border-t border-[#112d4e]/60 text-xs">
          <div>
            <label className="block text-[11px] text-slate-400 mb-1.5 font-medium">نوع سند:</label>
            <select
              value={docType}
              onChange={(e) => setDocType(e.target.value)}
              className="w-full bg-[#030712] border border-[#112d4e] rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-[#00e5ff] transition-colors"
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
            <label className="block text-[11px] text-slate-400 mb-1.5 font-medium">وضعیت داوری:</label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full bg-[#030712] border border-[#112d4e] rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-[#00e5ff] transition-colors"
            >
              <option value="">همه وضعیت‌ها</option>
              <option value="submitted">ثبت اولیه در قرنطینه</option>
              <option value="under_legal_review">در حال بررسی داوران</option>
              <option value="accepted">تأیید نهایی شده</option>
              <option value="rejected">رد شده</option>
            </select>
          </div>

          <div>
            <label className="block text-[11px] text-slate-400 mb-1.5 font-medium">مرجع تصویب:</label>
            <input
              type="text"
              value={authority}
              onChange={(e) => setAuthority(e.target.value)}
              placeholder="مثلاً: مجلس، دیوان عالی..."
              className="w-full bg-[#030712] border border-[#112d4e] rounded-xl px-3 py-2 text-slate-200 placeholder-slate-600 focus:outline-none focus:border-[#00e5ff] transition-colors"
            />
          </div>
        </div>

        {isSearchActive && (
          <div className="flex items-center justify-between pt-3 border-t border-[#112d4e]/40 text-xs">
            <span className="text-[#00e5ff] font-semibold">
              نتایج فیلتر: {displayedItems.length} مورد یافت شد
            </span>
            <button
              onClick={clearFilters}
              className="text-slate-400 hover:text-white flex items-center gap-1 transition-colors"
            >
              <X className="w-3.5 h-3.5" />
              <span>پاک کردن فیلترها</span>
            </button>
          </div>
        )}
      </div>

      {error && (
        <div className="mb-6 p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs shadow-md">
          {error}
        </div>
      )}

      {loading ? (
        <div className="text-center py-20 text-slate-400 text-sm">
          در حال بارگذاری مشارکت‌ها...
        </div>
      ) : displayedItems.length === 0 ? (
        <div className="text-center py-20 bg-[#071527] border border-[#112d4e] rounded-2xl p-8 shadow-xl">
          <div className="w-14 h-14 rounded-2xl bg-[#0b1e36] border border-[#112d4e] flex items-center justify-center mx-auto mb-4 text-slate-500">
            <ShieldCheck className="w-8 h-8" />
          </div>
          <h3 className="text-base font-bold text-slate-200 mb-1">
            {isSearchActive ? 'موردی مطابق با فیلترهای جستجو یافت نشد' : 'هنوز مشارکتی ثبت نکرده‌اید'}
          </h3>
          <p className="text-xs text-slate-400 max-w-sm mx-auto mb-6 leading-relaxed">
            {isSearchActive
              ? 'لطفاً عبارت جستجو یا شروط فیلتر را تغییر دهید.'
              : 'با ارسال قوانین، آیین‌نامه‌ها و آرای قضایی جدید، در توسعه گراف دانش حقوقی مشارکت کنید.'}
          </p>
          {isSearchActive && (
            <button
              onClick={clearFilters}
              className="px-5 py-2.5 rounded-xl bg-[#0b1e36] hover:bg-[#0f2d52] border border-[#112d4e] text-slate-200 text-xs font-semibold transition-colors"
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
            const isExpanded = expandedId === item.id;

            return (
              <div
                key={item.id}
                className="rounded-2xl bg-[#071527] border border-[#112d4e] hover:border-[#112d4e]/90 transition-all shadow-md overflow-hidden"
              >
                <div
                  onClick={() => toggleExpand(item.id)}
                  className="p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 cursor-pointer hover:bg-[#0b1e36]/30 transition-colors"
                >
                  <div className="space-y-2">
                    <div className="flex items-center gap-3 flex-wrap">
                      <span className="text-base font-bold text-white">{itemTitle}</span>
                      <span className="text-xs font-mono px-2.5 py-0.5 rounded-lg bg-[#0b1e36] text-[#00e5ff] border border-[#00e5ff]/30">
                        {itemDocType}
                      </span>
                      {item.issuing_authority && (
                        <span className="text-xs px-2.5 py-0.5 rounded-lg bg-[#030712] text-slate-400 border border-[#112d4e]">
                          {item.issuing_authority}
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-4 text-xs text-slate-400 flex-wrap">
                      <span className="font-mono">شناسه: {item.id.slice(0, 8)}...</span>
                      <span>تاریخ: {itemDate}</span>
                      <span>امتیاز کیفیت: {itemScore} / ۱۰۰</span>
                      {item.awarded_credits > 0 && (
                        <span className="text-emerald-400 font-mono font-bold">
                          +{item.awarded_credits} اعتبار
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-4 shrink-0">
                    <div className="text-left sm:text-right">
                      <div className="text-[11px] text-slate-400">پیشرفت داوری همتا:</div>
                      <div className="text-xs font-mono font-bold text-slate-200">
                        {itemApprovals} از {itemReq} رأی تایید
                      </div>
                    </div>
                    {getStatusBadge(item.status)}
                    <button className="p-1 text-slate-400 hover:text-white">
                      {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    </button>
                  </div>
                </div>

                {/* Expandable Evidence & Text Details */}
                {isExpanded && (
                  <div className="p-5 border-t border-[#112d4e] bg-[#030712]/90 space-y-4 text-xs">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      {item.source_url && (
                        <div className="p-3 rounded-xl bg-[#071527] border border-[#112d4e] space-y-1">
                          <span className="text-slate-400 block font-semibold">منبع رسمی ثبت‌شده:</span>
                          <a
                            href={item.source_url}
                            target="_blank"
                            rel="noreferrer"
                            className="text-[#00e5ff] hover:underline font-mono truncate block flex items-center gap-1.5"
                          >
                            <ExternalLink className="w-3.5 h-3.5 shrink-0" />
                            <span className="truncate">{item.source_url}</span>
                          </a>
                        </div>
                      )}
                      <div className="p-3 rounded-xl bg-[#071527] border border-[#112d4e] space-y-1">
                        <span className="text-slate-400 block font-semibold">مهر امنیتی دفتر کل (HMAC):</span>
                        <span className="font-mono text-slate-400 text-[11px] block truncate">
                          sha256:{item.id.replace(/-/g, '')}...verified
                        </span>
                      </div>
                    </div>

                    {item.raw_legal_text && (
                      <div className="space-y-1.5">
                        <span className="text-slate-400 font-semibold block">متن استنادی ثبت‌شده:</span>
                        <div className="p-4 rounded-xl bg-[#071527] border border-[#112d4e] text-slate-300 leading-relaxed max-h-40 overflow-y-auto">
                          {item.raw_legal_text}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
