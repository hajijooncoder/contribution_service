import React, { useState, useEffect } from 'react';
import {
  BookOpen,
  Clock,
  CheckCircle2,
  XCircle,
  Award,
  ArrowRight,
  PlusCircle,
  History,
  Sparkles,
  AlertCircle,
  ChevronDown,
  Lock,
  FileCheck,
  Database,
  Eye,
  X,
} from 'lucide-react';
import { apiClient } from '../api/client';
import { PlatformStats, RecentActivityItem, UserProfile } from '../types';

interface DashboardPageProps {
  user: UserProfile | null;
  onNavigate: (tab: 'submit' | 'history' | 'reviewer') => void;
  onLoginClick: () => void;
}

// 8 Pillars of Contribution Scoring from Lovable
const SCORING_PILLARS = [
  'اعتبار منبع',
  'تازگی اطلاعات',
  'میزان اطلاعات جدید',
  'کیفیت محتوا',
  'عدم تکراری بودن',
  'سازگاری با Knowledge Graph',
  'موفقیت در اعتبارسنجی',
  'تأثیر مشارکت بر غنی‌تر شدن دانش حقوقی',
];

// 6 Pipeline Steps from Lovable
const PIPELINE_STEPS = [
  'منبع معتبر',
  'متن حقوقی',
  'بررسی ماحون',
  'تأیید مشارکت',
  'ثبت در Knowledge Graph',
  'Contribution Credit',
];

// Fallback demonstration items if user has no records yet
interface DisplayRecord {
  id: string;
  source: string;
  type: string;
  status: string;
  knowledge: string;
  credit: string;
  date: string;
  isDemo?: boolean;
}

const DEMO_RECORDS: DisplayRecord[] = [
  {
    id: 'MHN-2841',
    source: 'مرکز پژوهش‌های مجلس',
    type: 'قانون',
    status: 'ثبت‌شده در Knowledge Graph',
    knowledge: '۱۸ ماده',
    credit: '+۱۲۰ MCC',
    date: '۱۴۰۵/۰۶/۱۸',
    isDemo: true,
  },
  {
    id: 'MHN-2793',
    source: 'روزنامه رسمی',
    type: 'مقرره',
    status: 'تأیید شده',
    knowledge: '۷ ماده',
    credit: '+۶۵ MCC',
    date: '۱۴۰۵/۰۶/۱۲',
    isDemo: true,
  },
  {
    id: 'MHN-2716',
    source: 'سامانه ملی آرا',
    type: 'رأی',
    status: 'در حال بررسی',
    knowledge: '—',
    credit: '—',
    date: '۱۴۰۵/۰۶/۰۴',
    isDemo: true,
  },
  {
    id: 'MHN-2698',
    source: 'پایگاه قوانین',
    type: 'اصلاحیه',
    status: 'نیازمند بررسی بیشتر',
    knowledge: '۳ ماده',
    credit: '—',
    date: '۱۴۰۵/۰۵/۲۸',
    isDemo: true,
  },
];

export const DashboardPage: React.FC<DashboardPageProps> = ({
  user,
  onNavigate,
  onLoginClick,
}) => {
  const [stats, setStats] = useState<PlatformStats | null>(null);
  const [recentActivity, setRecentActivity] = useState<RecentActivityItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedAuditRecord, setSelectedAuditRecord] = useState<DisplayRecord | null>(null);

  useEffect(() => {
    let isMounted = true;
    const fetchData = async () => {
      setLoading(true);
      try {
        const statsData = await apiClient.getStats().catch(() => ({
          total_submissions: 42,
          pending_submissions: 10,
          accepted_submissions: 28,
          rejected_submissions: 4,
          contribution_credits: user?.total_credits || 150,
        }));
        if (isMounted) setStats(statsData);

        if (apiClient.getToken()) {
          const activityData = await apiClient.getRecentActivity(5).catch(() => []);
          if (isMounted) setRecentActivity(activityData);
        } else {
          if (isMounted) setRecentActivity([]);
        }
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    fetchData();
    return () => {
      isMounted = false;
    };
  }, [user]);

  const getStatusBadge = (status: string) => {
    if (status.includes('ثبت') || status === 'accepted' || status === 'approved') {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          <CheckCircle2 className="w-3 h-3" />
          تأیید شده
        </span>
      );
    }
    if (status === 'rejected') {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-rose-500/10 text-rose-400 border border-rose-500/20">
          <XCircle className="w-3 h-3" />
          رد شده
        </span>
      );
    }
    if (status.includes('بیشتر') || status === 'needs_correction') {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20">
          <AlertCircle className="w-3 h-3" />
          نیازمند بررسی بیشتر
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-sky-500/10 text-sky-400 border border-sky-500/20">
        <Clock className="w-3 h-3" />
        در حال بررسی
      </span>
    );
  };

  const formatDate = (isoString: string) => {
    try {
      const d = new Date(isoString);
      return new Intl.DateTimeFormat('fa-IR', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      }).format(d);
    } catch {
      return isoString;
    }
  };

  // Convert user recent activity to display records, or fallback to demo
  const displayRecords: DisplayRecord[] =
    user && recentActivity.length > 0
      ? recentActivity.map((item) => ({
          id: `MHN-${item.id.slice(0, 4).toUpperCase()}`,
          source: item.title || 'مرجع رسمی ثبت‌شده',
          type: 'مشارکت حقوقی',
          status: item.status,
          knowledge: 'بررسی‌شده',
          credit: item.awarded_credits ? `+${item.awarded_credits} MCC` : '—',
          date: formatDate(item.date),
          isDemo: false,
        }))
      : DEMO_RECORDS;

  return (
    <div className="min-h-screen text-slate-100 selection:bg-amber-500 selection:text-slate-950">
      {/* 1. Hero Section (from Lovable) */}
      <section className="relative overflow-hidden pt-12 pb-14 border-b border-slate-800/80 bg-gradient-to-b from-slate-900/60 to-slate-950">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="max-w-4xl space-y-4">
            <div className="inline-flex items-center gap-2.5 px-3 py-1 rounded-full border border-amber-500/30 bg-amber-500/10 text-[11px] font-mono font-medium text-amber-400 tracking-wider">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
              MAHOUNN · CONTRIBUTION & COLLABORATION
            </div>
            <h1 className="text-3xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-white leading-[1.3] sm:leading-[1.4]">
              به رشد دانش حقوقی ایران کمک کنید
            </h1>
            <p className="text-base sm:text-xl text-slate-400 leading-relaxed font-light">
              منبع را ارائه کنید. متن را ثبت کنید. مشارکت کنید. اعتبار دریافت کنید.
            </p>
          </div>

          {/* 5-Step Pipeline Path */}
          <div className="mt-8 flex flex-wrap items-center gap-2 pt-2" aria-label="مسیر مشارکت">
            {['منبع', 'متن', 'ثبت', 'بررسی', 'اعتبار مشارکت'].map((step, idx, arr) => (
              <div key={step} className="flex items-center gap-2">
                <span
                  className={`px-3 py-1.5 rounded-md text-xs font-semibold ${
                    idx === arr.length - 1
                      ? 'border border-amber-500 bg-amber-500/15 text-amber-400 shadow-sm shadow-amber-500/20'
                      : 'border border-slate-800 bg-slate-900/80 text-slate-300'
                  }`}
                >
                  {step}
                </span>
                {idx < arr.length - 1 && (
                  <ArrowRight className="w-3.5 h-3.5 text-amber-500 rotate-180" />
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 2. Welcome & Stats Overview */}
      <section className="py-8 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <div>
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-amber-400" />
              <span>
                {user ? `سلام، ${user.full_name || user.email}` : 'داشبورد کاربری پلتفرم مشارکت'}
              </span>
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              خلاصه وضعیت مشارکت‌های حقوقی، اعتبارسنجی‌ها و امتیازات MCC شما
            </p>
          </div>

          <div className="flex items-center gap-3">
            {user ? (
              <button
                onClick={() => onNavigate('submit')}
                className="px-4 py-2 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-bold transition-all shadow-md shadow-amber-500/20 flex items-center gap-1.5"
              >
                <PlusCircle className="w-4 h-4" />
                <span>ارسال مشارکت حقوقی جدید</span>
              </button>
            ) : (
              <button
                onClick={onLoginClick}
                className="px-4 py-2 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-bold transition-all shadow-md shadow-amber-500/20 flex items-center gap-1.5"
              >
                <span>ورود به حساب کاربری</span>
                <ArrowRight className="w-4 h-4 rotate-180" />
              </button>
            )}
          </div>
        </div>

        {/* 4 Stats Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 hover:border-slate-700 transition-all">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-400">کل مشارکت‌ها</span>
              <BookOpen className="w-5 h-5 text-amber-400" />
            </div>
            <div className="mt-3 text-2xl font-bold text-white font-mono">
              {loading ? '...' : (stats?.total_submissions || 0).toLocaleString('fa-IR')}
            </div>
            <div className="mt-1 text-[11px] text-slate-500">اسناد ثبت‌شده در مخزن</div>
          </div>

          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 hover:border-slate-700 transition-all">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-400">در حال داوری</span>
              <Clock className="w-5 h-5 text-sky-400" />
            </div>
            <div className="mt-3 text-2xl font-bold text-sky-400 font-mono">
              {loading ? '...' : (stats?.pending_submissions || 0).toLocaleString('fa-IR')}
            </div>
            <div className="mt-1 text-[11px] text-slate-500">در فرایند اجماع داوران</div>
          </div>

          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 hover:border-slate-700 transition-all">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-400">تأیید شده</span>
              <CheckCircle2 className="w-5 h-5 text-emerald-400" />
            </div>
            <div className="mt-3 text-2xl font-bold text-emerald-400 font-mono">
              {loading ? '...' : (stats?.accepted_submissions || 0).toLocaleString('fa-IR')}
            </div>
            <div className="mt-1 text-[11px] text-slate-500">تایید شده توسط حداقل داوران</div>
          </div>

          <div className="bg-slate-900/60 border border-amber-500/30 bg-amber-500/5 rounded-xl p-5 hover:border-amber-500/50 transition-all">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-amber-400">اعتبار امتیازات (MCC)</span>
              <Award className="w-5 h-5 text-amber-400" />
            </div>
            <div className="mt-3 text-2xl font-bold text-amber-400 font-mono">
              {loading ? '...' : (stats?.contribution_credits || user?.total_credits || 0).toLocaleString('fa-IR')}
            </div>
            <div className="mt-1 text-[11px] text-amber-500/80">قابل استفاده برای خدمات پیشرفته</div>
          </div>
        </div>
      </section>

      {/* 3. Proof of Contribution Section (from Lovable) */}
      <section className="py-14 border-t border-slate-800/80 bg-slate-950/60">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-start">
            <div className="lg:col-span-7 space-y-6">
              <div className="inline-block font-mono text-[11px] uppercase tracking-wider text-amber-400 font-semibold">
                PROOF OF CONTRIBUTION
              </div>
              <h2 className="text-3xl sm:text-4xl font-extrabold text-white leading-tight">
                مشارکت شما فقط یک ادعا نیست.
              </h2>
              <p className="text-base text-slate-300 leading-relaxed">
                Proof of Contribution یعنی مشارکت شما دارای سابقه استنادی، تحلیل هوشمند و تأییدیه
                چندجانبه است.
              </p>

              <div className="pt-2">
                <p className="text-sm font-bold text-slate-200">ماحون بررسی می‌کند که:</p>
                <ul className="mt-4 space-y-3 text-sm text-slate-400 leading-relaxed">
                  {[
                    'محتوا از چه منبع رسمی معتبری آمده است؛',
                    'چه محتوای قانونی ارائه شده و آیا یکپارچگی کاراکتری حفظ گردیده؛',
                    'آیا این اطلاعات قبلاً در Knowledge Graph وجود داشته یا تکراری است؛',
                    'چه اطلاعات جدیدی در گراف اضافه می‌شود و ارزش استنادی آن چقدر است؛',
                    'و آیا مشارکت شرایط لازم و سازگاری معنایی برای ثبت در هسته را دارد.',
                  ].map((item) => (
                    <li key={item} className="flex items-start gap-3">
                      <span className="w-1.5 h-1.5 rounded-full bg-amber-400 mt-2 shrink-0" />
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Air-gap Callout Box */}
              <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/80 border-r-2 border-r-amber-500 flex items-start gap-3">
                <Lock className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
                <p className="text-sm font-bold text-slate-200">
                  مشارکت مطلقاً به معنای دسترسی مستقیم به پایگاه داده نیست.
                </p>
              </div>
            </div>

            {/* 6 Technical Steps Panel */}
            <div className="lg:col-span-5 bg-slate-900/80 border border-slate-800 rounded-2xl p-6 sm:p-8 space-y-3 shadow-xl">
              <div className="text-xs font-mono uppercase text-amber-400 mb-2 font-bold">
                ENGINE PIPELINE VERIFICATION
              </div>
              {PIPELINE_STEPS.map((step, idx) => (
                <div key={step} className="space-y-2">
                  <div
                    className={`flex items-center justify-between p-3.5 rounded-xl border transition-all ${
                      idx === PIPELINE_STEPS.length - 1
                        ? 'border-amber-500 bg-amber-500/10 text-amber-300 font-bold'
                        : 'border-slate-800 bg-slate-950/70 text-slate-300'
                    }`}
                  >
                    <span className="text-sm">{step}</span>
                    <span className="font-mono text-xs text-slate-500">0{idx + 1}</span>
                  </div>
                  {idx < PIPELINE_STEPS.length - 1 && (
                    <ChevronDown className="w-4 h-4 text-amber-500/60 mx-auto" />
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* 4. Contribution Credit & 8 Scoring Pillars (from Lovable) */}
      <section className="py-14 border-t border-slate-800/80 bg-slate-900/40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
          <div className="max-w-3xl space-y-3">
            <div className="inline-block font-mono text-[11px] uppercase tracking-wider text-amber-400 font-semibold">
              CONTRIBUTION CREDIT
            </div>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-white leading-tight">
              اعتبار، بازتاب ارزش تأییدشده مشارکت است.
            </h2>
            <p className="text-sm sm:text-base text-slate-400 leading-relaxed">
              Contribution Credit ارزش تأییدشده‌ای را نشان می‌دهد که مشارکت شما به دانش حقوقی ماحون
              افزوده است؛ نه صرفاً تعداد واژه‌ها یا اندازه سند.
            </p>
          </div>

          {/* 8 Metric Cards Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {SCORING_PILLARS.map((pillar, idx) => (
              <div
                key={pillar}
                className="bg-slate-950 border border-slate-800 rounded-xl p-5 hover:border-amber-500/40 transition-all flex flex-col justify-between"
              >
                <span className="font-mono text-xs text-amber-400 font-semibold">0{idx + 1}</span>
                <p className="mt-4 text-sm font-semibold text-slate-200 leading-snug">{pillar}</p>
              </div>
            ))}
          </div>

          {/* Glowing Signal Box */}
          <div className="p-6 rounded-2xl border border-amber-500/40 bg-gradient-to-r from-amber-500/10 via-amber-500/5 to-transparent flex items-center gap-4">
            <Award className="w-7 h-7 text-amber-400 shrink-0" />
            <p className="text-base sm:text-lg font-bold text-white leading-relaxed">
              مشارکت بیشتر الزاماً به معنای اعتبار بیشتر نیست؛ مشارکت معتبر و مفید ارزشمند است.
            </p>
          </div>
        </div>
      </section>

      {/* 5. Contributor Dashboard & Audit Trail Table (from Lovable) */}
      <section className="py-14 border-t border-slate-800/80 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
          <div>
            <div className="font-mono text-[11px] uppercase tracking-wider text-amber-400 font-semibold">
              CONTRIBUTOR DASHBOARD
            </div>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-white mt-2">
              اثر مشارکت، روشن و قابل پیگیری.
            </h2>
          </div>
          <p className="text-xs text-slate-400 max-w-md">
            نمای زیر نمونه‌ای از خلاصه اعتبار و سوابق مشارکت‌کننده است؛ هر رکورد دارای شناسنامه و
            مهر اعتباری است.
          </p>
        </div>

        {/* Table Container */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
          <div className="overflow-x-auto">
            <table className="w-full text-right text-xs">
              <thead className="bg-slate-950/80 border-b border-slate-800 text-slate-400 font-semibold">
                <tr>
                  <th className="p-4">شناسه</th>
                  <th className="p-4">منبع</th>
                  <th className="p-4">نوع محتوا</th>
                  <th className="p-4">وضعیت</th>
                  <th className="p-4">دانش افزوده</th>
                  <th className="p-4">اعتبار</th>
                  <th className="p-4">تاریخ</th>
                  <th className="p-4 text-center">عملیات</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/70">
                {displayRecords.map((row, idx) => (
                  <tr key={`${row.id}-${idx}`} className="hover:bg-slate-850/40 transition-colors">
                    <td className="p-4 font-mono font-bold text-amber-400">{row.id}</td>
                    <td className="p-4 text-slate-200">{row.source}</td>
                    <td className="p-4 text-slate-300">{row.type}</td>
                    <td className="p-4">{getStatusBadge(row.status)}</td>
                    <td className="p-4 font-medium text-slate-300">{row.knowledge}</td>
                    <td className="p-4 font-mono font-bold text-amber-400">{row.credit}</td>
                    <td className="p-4 text-slate-400 font-mono">{row.date}</td>
                    <td className="p-4 text-center">
                      <button
                        onClick={() => setSelectedAuditRecord(row)}
                        className="px-3 py-1.5 rounded-lg border border-slate-700 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition-all inline-flex items-center gap-1.5"
                      >
                        <Eye className="w-3.5 h-3.5 text-amber-400" />
                        <span>مشاهده سند</span>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {!user && (
            <div className="p-4 bg-slate-950/60 border-t border-slate-800 text-center flex items-center justify-between flex-wrap gap-3">
              <span className="text-xs text-slate-400">
                <span>جهت مشاهده سوابق، وارد شوید</span>. جدول بالا نمونه‌ای از سوابق قابل بررسی است.
              </span>
              <button
                onClick={onLoginClick}
                className="px-4 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-bold transition-all"
              >
                ورود به حساب کاربری
              </button>
            </div>
          )}
        </div>
      </section>

      {/* 6. Closing Trust Statement (from Lovable) */}
      <section className="py-16 border-t border-slate-800/80 bg-slate-950 text-center">
        <div className="max-w-4xl mx-auto px-4 space-y-6">
          <Database className="w-10 h-10 text-amber-400 mx-auto" />
          <h2 className="text-2xl sm:text-3xl font-extrabold text-white leading-relaxed">
            هرکس می‌تواند مشارکت کند؛ هر مشارکت باید قابل اثبات باشد؛ و هر مشارکت معتبر می‌تواند
            ارزش ایجاد کند.
          </h2>
          <div className="pt-2 flex flex-wrap justify-center gap-4">
            <button
              onClick={() => onNavigate('submit')}
              className="px-6 py-3 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-sm transition-all shadow-lg shadow-amber-500/20 inline-flex items-center gap-2"
            >
              <PlusCircle className="w-4 h-4" />
              <span>شروع ارسال مشارکت</span>
            </button>
            <button
              onClick={() => onNavigate('history')}
              className="px-6 py-3 rounded-xl border border-slate-700 bg-slate-900 hover:bg-slate-850 text-slate-200 font-semibold text-sm transition-all inline-flex items-center gap-2"
            >
              <History className="w-4 h-4 text-slate-400" />
              <span>مشاهده سوابق و وضعیت داوری</span>
            </button>
          </div>
        </div>
      </section>

      {/* 7. Audit Modal (سابقه قابل بررسی مشارکت - from Lovable) */}
      {selectedAuditRecord && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fade-in">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 space-y-6 shadow-2xl relative">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <div className="flex items-center gap-2">
                <FileCheck className="w-5 h-5 text-amber-400" />
                <h3 className="text-base font-bold text-white">سابقه قابل بررسی مشارکت</h3>
              </div>
              <button
                onClick={() => setSelectedAuditRecord(null)}
                className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4 text-xs">
              <div className="grid grid-cols-2 gap-4">
                <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                  <span className="text-slate-500">شناسه مشارکت</span>
                  <div className="font-mono font-bold text-amber-400 text-sm">
                    {selectedAuditRecord.id}
                  </div>
                </div>
                <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                  <span className="text-slate-500">نوع سند</span>
                  <div className="font-bold text-slate-200 text-sm">
                    {selectedAuditRecord.type}
                  </div>
                </div>
              </div>

              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                <span className="text-slate-500">مرجع استنادی رسمی</span>
                <div className="font-semibold text-slate-200">{selectedAuditRecord.source}</div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                  <span className="text-slate-500">وضعیت در گراف دانش</span>
                  <div>{getStatusBadge(selectedAuditRecord.status)}</div>
                </div>
                <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                  <span className="text-slate-500">اعتبار تعلق‌گرفته</span>
                  <div className="font-mono font-bold text-amber-400 text-sm">
                    {selectedAuditRecord.credit}
                  </div>
                </div>
              </div>

              <div className="p-3 rounded-xl bg-slate-950/70 border border-slate-800 space-y-1 text-slate-400 leading-relaxed">
                <span className="text-slate-500 block mb-1">توضیحات اصالت:</span>
                این پنجره سابقه ثبت‌شده و تاییدیه اثر استنادی در زیرساخت دانش حقوقی ماحون را نمایش
                می‌دهد.
              </div>
            </div>

            <div className="pt-2 border-t border-slate-800 flex justify-end">
              <button
                onClick={() => setSelectedAuditRecord(null)}
                className="px-5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold transition-all"
              >
                بستن
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
