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
  ShieldCheck,
  Scale,
  TrendingUp,
  Medal,
  Check,
  Download,
} from 'lucide-react';
import { apiClient } from '../api/client';
import { PlatformStats, RecentActivityItem, UserProfile } from '../types';

interface DashboardPageProps {
  user: UserProfile | null;
  onNavigate: (tab: 'submit' | 'history' | 'reviewer') => void;
  onLoginClick: () => void;
}

// 8 Pillars of Contribution Scoring
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

// 6 Pipeline Steps
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
          total_submissions: 75,
          pending_submissions: 10,
          accepted_submissions: 39,
          rejected_submissions: 4,
          contribution_credits: user?.total_credits || 221,
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
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
          <CheckCircle2 className="w-3.5 h-3.5" />
          تأیید شده
        </span>
      );
    }
    if (status === 'rejected') {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-rose-500/10 text-rose-400 border border-rose-500/30">
          <XCircle className="w-3.5 h-3.5" />
          رد شده
        </span>
      );
    }
    if (status.includes('بیشتر') || status === 'needs_correction') {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-amber-500/10 text-amber-400 border border-amber-500/30">
          <AlertCircle className="w-3.5 h-3.5" />
          نیازمند بررسی بیشتر
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-sky-500/10 text-sky-400 border border-sky-500/30">
        <Clock className="w-3.5 h-3.5" />
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

  const userCredits = user?.total_credits || stats?.contribution_credits || 0;
  const userRankTier =
    userCredits >= 200
      ? 'عضو مجمع نخبگان و هیئت داوران'
      : userCredits >= 50
      ? 'پژوهشگر ارشد اسناد رسمی'
      : 'پژوهشگر نوپای حقوقی';

  return (
    <div className="min-h-screen text-slate-100 font-sans selection:bg-[#00e5ff] selection:text-white">
      {/* 1. Hero Section with Cyber Knowledge Graph Visual */}
      <section className="relative overflow-hidden pt-14 pb-16 border-b border-[#112d4e]/80 bg-gradient-to-b from-[#020813]/40 via-transparent to-transparent relative after:absolute after:bottom-0 after:left-0 after:right-0 after:h-[1px] after:bg-gradient-to-r after:from-transparent after:via-[#00e5ff]/50 after:to-transparent after:pointer-events-none">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="max-w-4xl space-y-4">
            <div className="inline-flex items-center gap-2.5 px-3.5 py-1 rounded-full border border-[#00e5ff]/40 bg-[#0b1e36]/80 text-[11px] font-mono font-semibold text-[#00e5ff] tracking-wider shadow-sm">
              <span className="w-2 h-2 rounded-full bg-[#00e5ff] animate-pulse" />
              MAHOUNN · LEGAL KNOWLEDGE PLATFORM
            </div>

            <h1 className="text-2xl sm:text-4xl lg:text-5xl font-extrabold tracking-tight text-white leading-tight">
              <span className="block">عدالت تنها یک هدف نیست...</span>
              <span className="block mt-1 sm:mt-2 text-[#00e5ff]">عدالت یک مسیر است...</span>
            </h1>

            <p className="text-sm sm:text-base lg:text-lg text-slate-300 leading-relaxed font-light mt-3 max-w-3xl">
              <span className="block">پلتفرم توسعه گراف دانش حقوقی ایران با مشارکت حقوقدانان، وکلای دادگستری،</span>
              <span className="block mt-1">دانشجویان حقوق و کلیه متخصصین حقوقی و قضایی ایران...</span>
            </p>

            {/* Whitepaper CTA in Hero (Prominent & Expanded) */}
            <div className="pt-3 flex flex-wrap items-center gap-3">
              <a
                href="/whitepaper.pdf"
                download="MAHOUNN-Whitepaper.pdf"
                target="_blank"
                rel="noopener noreferrer"
                className="px-6 py-3.5 sm:px-7 sm:py-4 rounded-2xl border-2 border-[#00e5ff]/60 bg-gradient-to-r from-[#0b1e36]/90 via-[#071527]/90 to-[#0b1e36]/90 hover:from-[#00e5ff]/20 hover:to-[#0284c7]/30 hover:border-[#00e5ff] text-[#00e5ff] hover:text-white text-sm sm:text-base font-extrabold transition-all duration-300 shadow-xl shadow-[#00e5ff]/20 hover:shadow-[#00e5ff]/40 flex items-center gap-3.5 group backdrop-blur-md active:scale-98"
                title="دانلود سند جامع وایت‌پیپر MAHOUNN (نسخه PDF)"
              >
                <div className="w-9 h-9 rounded-xl bg-[#00e5ff]/15 border border-[#00e5ff]/40 flex items-center justify-center text-[#00e5ff] group-hover:bg-[#00e5ff] group-hover:text-[#030712] transition-all">
                  <Download className="w-5 h-5 group-hover:translate-y-0.5 transition-transform" />
                </div>
                <div className="flex flex-col text-right">
                  <span className="leading-tight">دانلود وایت‌پیپر پلتفرم (Whitepaper)</span>
                  <span className="text-[11px] font-mono text-slate-400 group-hover:text-slate-200 font-normal mt-0.5">
                    نسخه کامل و مستند PDF · ۵۴۱ کیلوبایت
                  </span>
                </div>
              </a>
            </div>
          </div>

          {/* 5-Step Pipeline Path */}
          <div className="mt-8 flex flex-wrap items-center gap-2 pt-2" aria-label="مسیر مشارکت">
            {['منبع', 'متن', 'ثبت', 'بررسی', 'اعتبار مشارکت'].map((step, idx, arr) => (
              <div key={step} className="flex items-center gap-2">
                <span
                  className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all ${
                    idx === arr.length - 1
                      ? 'border border-[#00e5ff] bg-[#0b1e36] text-[#00e5ff] shadow-sm shadow-[#00e5ff]/20 font-bold'
                      : 'border border-[#112d4e] bg-[#071527]/90 text-slate-300'
                  }`}
                >
                  {step}
                </span>
                {idx < arr.length - 1 && (
                  <ArrowRight className="w-3.5 h-3.5 text-[#00e5ff] rotate-180" />
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 2. Welcome & High-Quality KPI Cards */}
      <section className="py-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
          <div>
            <h2 className="text-xl font-bold text-white flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-[#0b1e36] border border-[#00e5ff]/30 flex items-center justify-center text-[#00e5ff]">
                <Scale className="w-4 h-4" />
              </div>
              <span>
                {user ? `سلام، ${user.full_name || user.email}` : 'داشبورد کاربری پلتفرم مشارکت'}
              </span>
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              خلاصه وضعیت مشارکت‌های حقوقی، اعتبارسنجی‌ها و امتیازات MCC شما
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {user ? (
              <button
                onClick={() => onNavigate('submit')}
                className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-[#00e5ff] via-[#0284c7] to-[#0369a1] hover:from-[#38bdf8] hover:to-[#0284c7] text-white text-xs font-bold transition-all shadow-lg shadow-[#00e5ff]/20 border border-[#00e5ff]/30 flex items-center gap-2"
              >
                <PlusCircle className="w-4 h-4" />
                <span>ارسال مشارکت حقوقی جدید</span>
              </button>
            ) : (
              <button
                onClick={onLoginClick}
                className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-[#00e5ff] via-[#0284c7] to-[#0369a1] hover:from-[#38bdf8] hover:to-[#0284c7] text-white text-xs font-bold transition-all shadow-lg shadow-[#00e5ff]/20 border border-[#00e5ff]/30 flex items-center gap-2"
              >
                <span>ورود به حساب کاربری</span>
                <ArrowRight className="w-4 h-4 rotate-180" />
              </button>
            )}

            <a
              href="/whitepaper.pdf"
              download="MAHOUNN-Whitepaper.pdf"
              target="_blank"
              rel="noopener noreferrer"
              className="px-4.5 py-2.5 rounded-xl border border-[#00e5ff]/40 bg-[#071527]/90 hover:bg-[#0b1e36] hover:border-[#00e5ff] text-[#00e5ff] hover:text-white text-xs sm:text-sm font-bold transition-all shadow-md flex items-center gap-2"
              title="دانلود وایت‌پیپر"
            >
              <Download className="w-4 h-4 text-[#00e5ff]" />
              <span>دانلود وایت‌پیپر (PDF)</span>
            </a>
          </div>
        </div>

        {/* 4 Premium KPI Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-[#071527]/90 border border-[#112d4e] border-t-[#00e5ff]/30 rounded-2xl p-5 hover:border-[#00e5ff]/40 hover:border-t-[#00e5ff]/60 transition-all shadow-lg shadow-black/30">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-400">کل مشارکت‌ها</span>
              <div className="w-8 h-8 rounded-xl bg-[#0b1e36] border border-[#112d4e] flex items-center justify-center text-[#00e5ff]">
                <BookOpen className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-4 text-3xl font-extrabold text-white font-mono">
              {loading ? '...' : (stats?.total_submissions || 0).toLocaleString('fa-IR')}
            </div>
            <div className="mt-1 text-[11px] text-slate-500">اسناد ثبت‌شده در مخزن</div>
          </div>

          <div className="bg-[#071527]/90 border border-[#112d4e] border-t-[#00e5ff]/30 rounded-2xl p-5 hover:border-sky-500/40 hover:border-t-[#00e5ff]/60 transition-all shadow-lg shadow-black/30">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-400">در حال داوری</span>
              <div className="w-8 h-8 rounded-xl bg-[#0b1e36] border border-[#112d4e] flex items-center justify-center text-sky-400">
                <Clock className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-4 text-3xl font-extrabold text-sky-400 font-mono">
              {loading ? '...' : (stats?.pending_submissions || 0).toLocaleString('fa-IR')}
            </div>
            <div className="mt-1 text-[11px] text-slate-500">در فرایند اجماع داوران</div>
          </div>

          <div className="bg-[#071527]/90 border border-[#112d4e] border-t-[#00e5ff]/30 rounded-2xl p-5 hover:border-emerald-500/40 hover:border-t-[#00e5ff]/60 transition-all shadow-lg shadow-black/30">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-400">تأیید شده</span>
              <div className="w-8 h-8 rounded-xl bg-[#0b1e36] border border-[#112d4e] flex items-center justify-center text-emerald-400">
                <CheckCircle2 className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-4 text-3xl font-extrabold text-emerald-400 font-mono">
              {loading ? '...' : (stats?.accepted_submissions || 0).toLocaleString('fa-IR')}
            </div>
            <div className="mt-1 text-[11px] text-slate-500">تایید شده توسط حداقل داوران</div>
          </div>

          <div className="bg-gradient-to-br from-[#0b1e36] to-[#071527] border border-[#00e5ff]/40 border-t-[#00e5ff]/45 rounded-2xl p-5 hover:border-[#00e5ff]/70 hover:border-t-[#00e5ff]/75 transition-all shadow-lg shadow-[#00e5ff]/10">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-[#00e5ff]">اعتبار امتیازات (MCC)</span>
              <div className="w-8 h-8 rounded-xl bg-[#071527] border border-[#00e5ff]/40 flex items-center justify-center text-[#00e5ff]">
                <Award className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-4 text-3xl font-extrabold text-[#00e5ff] font-mono">
              {loading ? '...' : (stats?.contribution_credits || user?.total_credits || 0).toLocaleString('fa-IR')}
            </div>
            <div className="mt-1 text-[11px] text-slate-400">قابل استفاده برای خدمات پیشرفته</div>
          </div>
        </div>
      </section>

      {/* 3. Leaderboard & Contributor Reputation Section (Deliverable D) */}
      <section className="py-12 border-t border-[#112d4e]/80 bg-[#05101f]/35 backdrop-blur-[2px] relative before:absolute before:top-0 before:left-0 before:right-0 before:h-[1px] before:bg-gradient-to-r before:from-transparent before:via-[#00e5ff]/35 before:to-transparent before:pointer-events-none">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
            <div>
              <div className="inline-flex items-center gap-2 font-mono text-[11px] uppercase tracking-wider text-[#00e5ff] font-bold">
                <Medal className="w-3.5 h-3.5" />
                LEADERBOARD & REPUTATION SYSTEM
              </div>
              <h2 className="text-2xl sm:text-3xl font-extrabold text-white mt-1">
                تالار افتخارات، رتبه‌بندی و اعتبار علمی پژوهشگران
              </h2>
            </div>
            <p className="text-xs text-slate-400 max-w-md">
              امتیازات بر مبنای کیفیت استنادها، پالایش مواد قانونی و تایید در نصاب داوری به صورت
              رمزنگاری‌شده در دفتر کل ثبت می‌شود.
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* User Reputation Status Card */}
            <div className="p-6 rounded-2xl bg-[#071527] border border-[#112d4e] space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-400 font-semibold">سطح علمی و اعتبار شما</span>
                <span className="px-2.5 py-1 rounded-full text-[11px] font-bold bg-[#0b1e36] border border-[#00e5ff]/40 text-[#00e5ff]">
                  {userRankTier}
                </span>
              </div>

              <div className="p-4 rounded-xl bg-[#030712] border border-[#112d4e]/80 space-y-2">
                <div className="flex justify-between items-center text-xs">
                  <span className="text-slate-400">مجموع اعتبارات اختصاص‌یافته:</span>
                  <span className="font-mono font-bold text-[#00e5ff] text-sm">
                    {userCredits} MCC
                  </span>
                </div>
                <div className="w-full bg-[#0b1e36] h-2 rounded-full overflow-hidden">
                  <div
                    className="bg-gradient-to-r from-[#0284c7] to-[#00e5ff] h-full rounded-full transition-all duration-500"
                    style={{ width: `${Math.min(100, Math.max(15, (userCredits / 200) * 100))}%` }}
                  />
                </div>
                <div className="flex justify-between text-[10px] text-slate-500">
                  <span>پژوهشگر نوپا (۰)</span>
                  <span>ارشد (۵۰)</span>
                  <span>مجمع نخبگان (۲۰۰)</span>
                </div>
              </div>

              <div className="space-y-2 pt-1 text-xs">
                <span className="text-slate-400 block font-semibold mb-1">مدال‌های کسب‌شده:</span>
                <div className="space-y-1.5">
                  <div className="flex items-center gap-2 p-2 rounded-lg bg-[#0b1e36]/60 border border-[#112d4e]/60 text-slate-300">
                    <Check className="w-3.5 h-3.5 text-[#00e5ff]" />
                    <span>نشان استناد رسمی به قوانین حاکمیتی</span>
                  </div>
                  <div className="flex items-center gap-2 p-2 rounded-lg bg-[#0b1e36]/60 border border-[#112d4e]/60 text-slate-300">
                    <Check className="w-3.5 h-3.5 text-emerald-400" />
                    <span>نشان اصالت محتوا و تایید در SimHash</span>
                  </div>
                  <div className="flex items-center gap-2 p-2 rounded-lg bg-[#0b1e36]/60 border border-[#112d4e]/60 text-slate-300">
                    <Check className="w-3.5 h-3.5 text-sky-400" />
                    <span>نشان ثبت در حدنصاب اجماع داوران</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Transparent Earning Rules */}
            <div className="p-6 rounded-2xl bg-[#071527] border border-[#112d4e] space-y-4">
              <div className="flex items-center gap-2 text-xs font-bold text-slate-200">
                <TrendingUp className="w-4 h-4 text-[#00e5ff]" />
                <span>جدول شفاف محاسبه امتیازات مشارکت (MCC)</span>
              </div>
              <div className="space-y-2.5 text-xs">
                <div className="p-3 rounded-xl bg-[#030712] border border-[#112d4e] flex items-center justify-between">
                  <span className="text-slate-300">ثبت ماده قانونی مصوب مجلس با ارجاعات</span>
                  <span className="font-mono font-bold text-emerald-400">+۲۰ MCC</span>
                </div>
                <div className="p-3 rounded-xl bg-[#030712] border border-[#112d4e] flex items-center justify-between">
                  <span className="text-slate-300">آراء وحدت رویه و دادنامه‌های قضایی</span>
                  <span className="font-mono font-bold text-emerald-400">+۱۵ MCC</span>
                </div>
                <div className="p-3 rounded-xl bg-[#030712] border border-[#112d4e] flex items-center justify-between">
                  <span className="text-slate-300">داوری و ثبت استدلال در حدنصاب اجماع</span>
                  <span className="font-mono font-bold text-[#00e5ff]">+۱۰ MCC</span>
                </div>
                <div className="p-3 rounded-xl bg-[#030712] border border-[#112d4e] flex items-center justify-between">
                  <span className="text-slate-300">استخراج و تصحیح ارتباطات متنی گراف</span>
                  <span className="font-mono font-bold text-sky-400">+۸ MCC</span>
                </div>
              </div>
            </div>

            {/* Platform Integrity & Consensus Indicator */}
            <div className="p-6 rounded-2xl bg-[#071527] border border-[#112d4e] space-y-4 flex flex-col justify-between">
              <div>
                <div className="flex items-center gap-2 text-xs font-bold text-slate-200 mb-2">
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                  <span>شاخص سلامت اجماع داوری همتا</span>
                </div>
                <p className="text-xs text-slate-400 leading-relaxed">
                  هیچ سندی به صورت انفرادی یا بدون بررسی خودکار پیش‌پردازش متنی وارد پایگاه نمی‌شود. هر
                  سند بر مبنای حساسیت محتوا به حداقل ۱ تا ۲ رأی داور مستقل نیاز دارد.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-[#0b1e36] border border-[#112d4e] space-y-2 text-xs">
                <div className="flex items-center justify-between text-slate-300">
                  <span>نرخ پذیرش در داوری:</span>
                  <span className="font-mono font-bold text-white">
                    {stats?.total_submissions && stats.total_submissions > 0
                      ? `${Math.round(((stats.accepted_submissions || 0) / stats.total_submissions) * 100)}%`
                      : '۷۸%'}
                  </span>
                </div>
                <div className="flex items-center justify-between text-slate-300">
                  <span>پایداری اعتبارسنجی:</span>
                  <span className="font-mono font-bold text-emerald-400">۱۰۰٪ (Air-Gap)</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 4. Proof of Contribution Section */}
      <section className="py-14 border-t border-[#112d4e]/80 bg-[#030712]/30 backdrop-blur-[2px]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-start">
            <div className="lg:col-span-7 space-y-6">
              <div className="inline-block font-mono text-[11px] uppercase tracking-wider text-[#00e5ff] font-semibold">
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
                      <span className="w-1.5 h-1.5 rounded-full bg-[#00e5ff] mt-2 shrink-0" />
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Air-gap Callout Box */}
              <div className="p-4 rounded-xl border border-[#112d4e] bg-[#071527] border-r-4 border-r-[#00e5ff] flex items-start gap-3 shadow-md">
                <Lock className="w-5 h-5 text-[#00e5ff] shrink-0 mt-0.5" />
                <p className="text-sm font-bold text-slate-200">
                  مشارکت مطلقاً به معنای دسترسی مستقیم به پایگاه داده نیست.
                </p>
              </div>
            </div>

            {/* 6 Technical Steps Panel */}
            <div className="lg:col-span-5 bg-[#071527] border border-[#112d4e] rounded-2xl p-6 sm:p-8 space-y-3 shadow-xl">
              <div className="text-xs font-mono uppercase text-[#00e5ff] mb-2 font-bold tracking-wider">
                ENGINE PIPELINE VERIFICATION
              </div>
              {PIPELINE_STEPS.map((step, idx) => (
                <div key={step} className="space-y-2">
                  <div
                    className={`flex items-center justify-between p-3.5 rounded-xl border transition-all ${
                      idx === PIPELINE_STEPS.length - 1
                        ? 'border-[#00e5ff] bg-[#0b1e36] text-[#00e5ff] font-bold shadow-sm'
                        : 'border-[#112d4e] bg-[#030712]/80 text-slate-300'
                    }`}
                  >
                    <span className="text-sm font-medium">{step}</span>
                    <span className="font-mono text-xs text-slate-500">0{idx + 1}</span>
                  </div>
                  {idx < PIPELINE_STEPS.length - 1 && (
                    <ChevronDown className="w-4 h-4 text-[#00e5ff]/60 mx-auto" />
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* 5. Contribution Credit & 8 Scoring Pillars */}
      <section className="py-14 border-t border-[#112d4e]/80 bg-[#05101f]/35 backdrop-blur-[2px] relative before:absolute before:top-0 before:left-0 before:right-0 before:h-[1px] before:bg-gradient-to-r before:from-transparent before:via-[#00e5ff]/35 before:to-transparent before:pointer-events-none">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
          <div className="max-w-3xl space-y-3">
            <div className="inline-block font-mono text-[11px] uppercase tracking-wider text-[#00e5ff] font-semibold">
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
                className="bg-[#071527] border border-[#112d4e] border-t-[#00e5ff]/25 rounded-xl p-5 hover:border-[#00e5ff]/40 hover:border-t-[#00e5ff]/50 transition-all flex flex-col justify-between shadow-md"
              >
                <span className="font-mono text-xs text-[#00e5ff] font-semibold">0{idx + 1}</span>
                <p className="mt-4 text-sm font-semibold text-slate-200 leading-snug">{pillar}</p>
              </div>
            ))}
          </div>

          {/* Signal Box */}
          <div className="p-6 rounded-2xl border border-[#00e5ff]/40 bg-gradient-to-r from-[#0b1e36] via-[#071527] to-[#030712] flex items-center gap-4 shadow-lg shadow-black/30 relative before:absolute before:top-0 before:left-6 before:right-6 before:h-[1px] before:bg-[#00e5ff]/30 before:pointer-events-none">
            <div className="w-12 h-12 rounded-xl bg-[#030712] border border-[#00e5ff]/40 flex items-center justify-center shrink-0 text-[#00e5ff]">
              <Award className="w-6 h-6" />
            </div>
            <p className="text-base sm:text-lg font-bold text-white leading-relaxed">
              مشارکت بیشتر الزاماً به معنای اعتبار بیشتر نیست؛ مشارکت معتبر و مفید ارزشمند است.
            </p>
          </div>
        </div>
      </section>

      {/* 6. Contributor Dashboard & Audit Trail Table */}
      <section className="py-14 border-t border-[#112d4e]/80 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
          <div>
            <div className="font-mono text-[11px] uppercase tracking-wider text-[#00e5ff] font-semibold">
              CONTRIBUTOR DASHBOARD
            </div>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-white mt-1">
              اثر مشارکت، روشن و قابل پیگیری.
            </h2>
          </div>
          <p className="text-xs text-slate-400 max-w-md">
            نمای زیر نمونه‌ای از خلاصه اعتبار و سوابق مشارکت‌کننده است؛ هر رکورد دارای شناسنامه و
            مهر اعتباری است.
          </p>
        </div>

        {/* Table Container */}
        <div className="bg-[#071527] border border-[#112d4e] rounded-2xl overflow-hidden shadow-xl">
          <div className="overflow-x-auto">
            <table className="w-full text-right text-xs">
              <thead className="bg-[#030712] border-b border-[#112d4e] text-slate-400 font-semibold">
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
              <tbody className="divide-y divide-[#112d4e]/70">
                {displayRecords.map((row, idx) => (
                  <tr key={`${row.id}-${idx}`} className="hover:bg-[#0b1e36]/50 transition-colors">
                    <td className="p-4 font-mono font-bold text-[#00e5ff]">{row.id}</td>
                    <td className="p-4 text-slate-200 font-medium">{row.source}</td>
                    <td className="p-4 text-slate-300">{row.type}</td>
                    <td className="p-4">{getStatusBadge(row.status)}</td>
                    <td className="p-4 font-medium text-slate-300">{row.knowledge}</td>
                    <td className="p-4 font-mono font-bold text-[#00e5ff]">{row.credit}</td>
                    <td className="p-4 text-slate-400 font-mono">{row.date}</td>
                    <td className="p-4 text-center">
                      <button
                        onClick={() => setSelectedAuditRecord(row)}
                        className="px-3.5 py-1.5 rounded-xl border border-[#112d4e] bg-[#0b1e36] hover:bg-[#0f2d52] hover:border-[#00e5ff]/50 text-slate-200 text-xs font-medium transition-all inline-flex items-center gap-1.5 shadow-sm"
                      >
                        <Eye className="w-3.5 h-3.5 text-[#00e5ff]" />
                        <span>مشاهده سند</span>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {!user && (
            <div className="p-4 bg-[#030712] border-t border-[#112d4e] text-center flex items-center justify-between flex-wrap gap-3">
              <span className="text-xs text-slate-400">
                <span>جهت مشاهده سوابق، وارد شوید</span>. جدول بالا نمونه‌ای از سوابق قابل بررسی است.
              </span>
              <button
                onClick={onLoginClick}
                className="px-4 py-2 rounded-xl bg-gradient-to-r from-[#00e5ff] via-[#0284c7] to-[#0369a1] text-white text-xs font-bold transition-all shadow-md border border-[#00e5ff]/30"
              >
                ورود به حساب کاربری
              </button>
            </div>
          )}
        </div>
      </section>

      {/* 7. Closing Trust Statement */}
      <section className="py-16 border-t border-[#112d4e]/80 bg-[#030712]/40 backdrop-blur-[2px] text-center relative before:absolute before:top-0 before:left-0 before:right-0 before:h-[1px] before:bg-gradient-to-r before:from-transparent before:via-[#00e5ff]/30 before:to-transparent before:pointer-events-none">
        <div className="max-w-4xl mx-auto px-4 space-y-6">
          <div className="w-14 h-14 rounded-2xl bg-[#0b1e36] border border-[#00e5ff]/40 flex items-center justify-center mx-auto text-[#00e5ff] shadow-lg shadow-black/40 relative before:absolute before:inset-0 before:rounded-2xl before:border before:border-[#00e5ff]/20 before:pointer-events-none">
            <Database className="w-7 h-7" />
          </div>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-white leading-relaxed">
            هرکس می‌تواند مشارکت کند؛ هر مشارکت باید قابل اثبات باشد؛ و هر مشارکت معتبر می‌تواند
            ارزش ایجاد کند.
          </h2>
          <div className="pt-2 flex flex-wrap justify-center gap-4">
            <button
              onClick={() => onNavigate('submit')}
              className="px-6 py-3 rounded-xl bg-gradient-to-r from-[#00e5ff] via-[#0284c7] to-[#0369a1] hover:from-[#38bdf8] hover:to-[#0284c7] text-white font-bold text-sm transition-all shadow-lg shadow-[#00e5ff]/20 border border-[#00e5ff]/30 inline-flex items-center gap-2"
            >
              <PlusCircle className="w-4 h-4" />
              <span>شروع ارسال مشارکت</span>
            </button>
            <button
              onClick={() => onNavigate('history')}
              className="px-6 py-3 rounded-xl border border-[#112d4e] bg-[#071527] hover:bg-[#0b1e36] text-slate-200 font-semibold text-sm transition-all inline-flex items-center gap-2 shadow-md border-t-[#00e5ff]/25"
            >
              <History className="w-4 h-4 text-[#00e5ff]" />
              <span>مشاهده سوابق و وضعیت داوری</span>
            </button>
          </div>
        </div>
      </section>

      {/* 8. Audit Modal */}
      {selectedAuditRecord && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[#030712]/85 backdrop-blur-sm animate-fade-in">
          <div className="bg-[#071527] border border-[#112d4e] rounded-2xl max-w-lg w-full p-6 space-y-6 shadow-2xl relative">
            <div className="flex items-center justify-between border-b border-[#112d4e] pb-4">
              <div className="flex items-center gap-2">
                <FileCheck className="w-5 h-5 text-[#00e5ff]" />
                <h3 className="text-base font-bold text-white">سابقه قابل بررسی مشارکت</h3>
              </div>
              <button
                onClick={() => setSelectedAuditRecord(null)}
                className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-[#0b1e36] transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4 text-xs">
              <div className="grid grid-cols-2 gap-4">
                <div className="p-3.5 rounded-xl bg-[#030712] border border-[#112d4e] space-y-1">
                  <span className="text-slate-500">شناسه مشارکت</span>
                  <div className="font-mono font-bold text-[#00e5ff] text-sm">
                    {selectedAuditRecord.id}
                  </div>
                </div>
                <div className="p-3.5 rounded-xl bg-[#030712] border border-[#112d4e] space-y-1">
                  <span className="text-slate-500">نوع سند</span>
                  <div className="font-bold text-slate-200 text-sm">
                    {selectedAuditRecord.type}
                  </div>
                </div>
              </div>

              <div className="p-3.5 rounded-xl bg-[#030712] border border-[#112d4e] space-y-1">
                <span className="text-slate-500">مرجع استنادی رسمی</span>
                <div className="font-semibold text-slate-200">{selectedAuditRecord.source}</div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="p-3.5 rounded-xl bg-[#030712] border border-[#112d4e] space-y-1">
                  <span className="text-slate-500">وضعیت در گراف دانش</span>
                  <div>{getStatusBadge(selectedAuditRecord.status)}</div>
                </div>
                <div className="p-3.5 rounded-xl bg-[#030712] border border-[#112d4e] space-y-1">
                  <span className="text-slate-500">اعتبار تعلق‌گرفته</span>
                  <div className="font-mono font-bold text-[#00e5ff] text-sm">
                    {selectedAuditRecord.credit}
                  </div>
                </div>
              </div>

              <div className="p-3.5 rounded-xl bg-[#030712]/70 border border-[#112d4e] space-y-1 text-slate-400 leading-relaxed">
                <span className="text-slate-500 block mb-1">توضیحات اصالت:</span>
                این پنجره سابقه ثبت‌شده و تاییدیه اثر استنادی در زیرساخت دانش حقوقی ماحون را نمایش
                می‌دهد.
              </div>
            </div>

            <div className="pt-2 border-t border-[#112d4e] flex justify-end">
              <button
                onClick={() => setSelectedAuditRecord(null)}
                className="px-5 py-2 rounded-xl bg-[#0b1e36] hover:bg-[#0f2d52] text-slate-200 text-xs font-semibold transition-all border border-[#112d4e]"
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
