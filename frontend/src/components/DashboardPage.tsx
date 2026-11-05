import React, { useState, useEffect } from 'react';
import {
  LayoutDashboard,
  BookOpen,
  Clock,
  CheckCircle2,
  XCircle,
  Award,
  ArrowRight,
  PlusCircle,
  History,
  ShieldCheck,
  Sparkles,
  ExternalLink,
  AlertCircle
} from 'lucide-react';
import { apiClient } from '../api/client';
import { PlatformStats, RecentActivityItem, UserProfile } from '../types';

interface DashboardPageProps {
  user: UserProfile | null;
  onNavigate: (tab: 'submit' | 'history' | 'reviewer') => void;
  onLoginClick: () => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({
  user,
  onNavigate,
  onLoginClick,
}) => {
  const [stats, setStats] = useState<PlatformStats | null>(null);
  const [recentActivity, setRecentActivity] = useState<RecentActivityItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        const statsData = await apiClient.getStats().catch(() => ({
          total_submissions: 0,
          pending_submissions: 0,
          accepted_submissions: 0,
          rejected_submissions: 0,
          contribution_credits: user?.total_credits || 0,
        }));
        setStats(statsData);

        if (apiClient.getToken()) {
          const activityData = await apiClient.getRecentActivity(5).catch(() => []);
          setRecentActivity(activityData);
        } else {
          setRecentActivity([]);
        }
      } catch (err: any) {
        setError(err.message || 'خطا در بارگذاری اطلاعات داشبورد.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [user]);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'accepted':
      case 'approved':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <CheckCircle2 className="w-3.5 h-3.5" />
            تأیید نهایی
          </span>
        );
      case 'rejected':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-rose-500/10 text-rose-400 border border-rose-500/20">
            <XCircle className="w-3.5 h-3.5" />
            رد شده
          </span>
        );
      case 'needs_correction':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20">
            <AlertCircle className="w-3.5 h-3.5" />
            نیازمند اصلاح
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-sky-500/10 text-sky-400 border border-sky-500/20">
            <Clock className="w-3.5 h-3.5" />
            در حال داوری
          </span>
        );
    }
  };

  const formatDate = (isoString: string) => {
    try {
      const date = new Date(isoString);
      return new Intl.DateTimeFormat('fa-IR', {
        dateStyle: 'medium',
        timeStyle: 'short',
      }).format(date);
    } catch {
      return isoString;
    }
  };

  return (
    <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8 space-y-8" dir="rtl">
      {/* Welcome Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-slate-900 via-slate-850 to-slate-900 border border-slate-800 p-6 sm:p-8 shadow-xl">
        <div className="absolute top-0 left-0 -mt-8 -ml-8 w-64 h-64 bg-amber-500/10 rounded-full blur-3xl pointer-events-none" />
        
        <div className="relative flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/20 text-amber-400 text-xs font-medium">
              <Sparkles className="w-3.5 h-3.5" />
              <span>پلتفرم پالایش و مشارکت حقوقی ماحون</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
              {user ? `سلام، ${user.full_name || user.email}` : 'داشبورد کاربری پلتفرم مشارکت'}
            </h1>
            <p className="text-slate-400 text-sm max-w-2xl leading-relaxed">
              با مشارکت در ثبت، تقطیع و داوری اسناد قوانین، مقررات و آراء قضایی، به غنای گراف دانش ماحون کمک کنید و اعتبار MCC برای بهره‌مندی از خدمات اختصاصی به دست آورید.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 w-full md:w-auto">
            {user ? (
              <div className="bg-slate-950/80 border border-amber-500/30 rounded-xl px-5 py-3 flex items-center justify-between md:justify-center gap-4 shadow-inner">
                <div className="flex items-center gap-2.5">
                  <div className="w-9 h-9 rounded-lg bg-amber-500/20 flex items-center justify-center text-amber-400">
                    <Award className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="text-[11px] text-slate-400">اعتبار اندوخته شما</div>
                    <div className="text-lg font-bold text-amber-400 font-mono">
                      {user.total_credits} <span className="text-xs font-sans text-amber-500/80">MCC</span>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <button
                onClick={onLoginClick}
                className="px-5 py-3 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 text-slate-950 font-bold text-sm shadow-lg shadow-amber-500/20 hover:from-amber-400 hover:to-amber-500 transition-all flex items-center justify-center gap-2"
              >
                <span>ورود به حساب کاربری</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Submissions */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 hover:border-slate-700 transition-all">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-slate-400">کل مشارکت‌های مخزن</span>
            <div className="w-9 h-9 rounded-lg bg-indigo-500/10 text-indigo-400 flex items-center justify-center">
              <BookOpen className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-white font-mono">
              {loading ? '...' : stats?.total_submissions.toLocaleString('fa-IR')}
            </span>
            <span className="text-xs text-slate-500">سند</span>
          </div>
          <div className="mt-2 text-xs text-slate-400">مجموع اسناد ثبتی جامعه حقوقی</div>
        </div>

        {/* Pending Submissions */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 hover:border-slate-700 transition-all">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-slate-400">در حال داوری و پالایش</span>
            <div className="w-9 h-9 rounded-lg bg-sky-500/10 text-sky-400 flex items-center justify-center">
              <Clock className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-sky-400 font-mono">
              {loading ? '...' : stats?.pending_submissions.toLocaleString('fa-IR')}
            </span>
            <span className="text-xs text-slate-500">سند</span>
          </div>
          <div className="mt-2 text-xs text-slate-400">در انتظار حدنصاب آرای داوران</div>
        </div>

        {/* Accepted Submissions */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 hover:border-slate-700 transition-all">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-slate-400">تأیید قطعی و آماده گراف</span>
            <div className="w-9 h-9 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center">
              <CheckCircle2 className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-emerald-400 font-mono">
              {loading ? '...' : stats?.accepted_submissions.toLocaleString('fa-IR')}
            </span>
            <span className="text-xs text-slate-500">سند</span>
          </div>
          <div className="mt-2 text-xs text-slate-400">دارای مهر اصالت سه‌جانبه</div>
        </div>

        {/* Total MCC Credits */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 hover:border-slate-700 transition-all">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-slate-400">اعتبار انباشته کل (MCC)</span>
            <div className="w-9 h-9 rounded-lg bg-amber-500/10 text-amber-400 flex items-center justify-center">
              <Award className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-amber-400 font-mono">
              {loading ? '...' : (stats?.contribution_credits || 0).toLocaleString('fa-IR')}
            </span>
            <span className="text-xs text-amber-500/80 font-mono">MCC</span>
          </div>
          <div className="mt-2 text-xs text-slate-400">پاداش‌های تخصیص‌یافته به مشارکت‌کنندگان</div>
        </div>
      </div>

      {/* Main Content Layout: Activity + Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Recent Activity (2 Cols) */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <History className="w-5 h-5 text-amber-400" />
              <h2 className="text-lg font-bold text-white">آخرین فعالیت‌های شما</h2>
            </div>
            {user && recentActivity.length > 0 && (
              <button
                onClick={() => onNavigate('history')}
                className="text-xs text-amber-400 hover:text-amber-300 font-medium flex items-center gap-1 transition-colors"
              >
                <span>مشاهده همه</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

          <div className="bg-slate-900/60 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
            {!user ? (
              <div className="p-8 text-center space-y-3">
                <ShieldCheck className="w-12 h-12 text-slate-600 mx-auto" />
                <h3 className="text-base font-semibold text-slate-200">جهت مشاهده سوابق، وارد شوید</h3>
                <p className="text-xs text-slate-400 max-w-sm mx-auto">
                  با ورود به حساب کاربری، می‌توانید وضعیت داوری مشارکت‌ها و امتیازات دریافتی خود را رهگیری نمایید.
                </p>
                <button
                  onClick={onLoginClick}
                  className="mt-2 px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold transition-all"
                >
                  ورود به حساب
                </button>
              </div>
            ) : recentActivity.length === 0 ? (
              <div className="p-8 text-center space-y-3">
                <BookOpen className="w-12 h-12 text-slate-600 mx-auto" />
                <h3 className="text-base font-semibold text-slate-200">هنوز مشارکتی ثبت نکرده‌اید</h3>
                <p className="text-xs text-slate-400 max-w-sm mx-auto">
                  شما می‌توانید اولین سند حقوقی یا مصوبه را ثبت کنید و اولین اعتبارات MCC خود را دریافت کنید.
                </p>
                <button
                  onClick={() => onNavigate('submit')}
                  className="mt-2 px-4 py-2 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-bold transition-all inline-flex items-center gap-1.5"
                >
                  <PlusCircle className="w-4 h-4" />
                  <span>ثبت اولین مشارکت</span>
                </button>
              </div>
            ) : (
              <div className="divide-y divide-slate-800/80">
                {recentActivity.map((item) => (
                  <div
                    key={item.id}
                    className="p-4 flex items-center justify-between gap-4 hover:bg-slate-850/50 transition-colors"
                  >
                    <div className="space-y-1 min-w-0 flex-1">
                      <div className="text-sm font-semibold text-slate-200 truncate">
                        {item.title}
                      </div>
                      <div className="text-[11px] text-slate-500">
                        {formatDate(item.date)}
                      </div>
                    </div>

                    <div className="flex items-center gap-3 shrink-0">
                      {item.awarded_credits ? (
                        <span className="text-xs font-bold text-amber-400 font-mono">
                          +{item.awarded_credits} MCC
                        </span>
                      ) : null}
                      {getStatusBadge(item.status)}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Quick Actions & Protocol Guide (1 Col) */}
        <div className="space-y-6">
          {/* Quick Actions Card */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 space-y-3">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-amber-400" />
              <span>اقدامات سریع</span>
            </h3>

            <div className="space-y-2 pt-1">
              <button
                onClick={() => onNavigate('submit')}
                className="w-full px-4 py-3 rounded-lg bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 font-bold text-xs flex items-center justify-between shadow-md shadow-amber-500/10 transition-all"
              >
                <div className="flex items-center gap-2">
                  <PlusCircle className="w-4 h-4" />
                  <span>ارسال مشارکت حقوقی جدید</span>
                </div>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>

              <button
                onClick={() => onNavigate('history')}
                className="w-full px-4 py-3 rounded-lg bg-slate-800/80 hover:bg-slate-800 text-slate-200 font-medium text-xs flex items-center justify-between border border-slate-700/60 transition-all"
              >
                <div className="flex items-center gap-2">
                  <History className="w-4 h-4 text-slate-400" />
                  <span>پیگیری سوابق مشارکت‌ها</span>
                </div>
                <ArrowRight className="w-3.5 h-3.5 text-slate-400" />
              </button>

              {(user?.role === 'reviewer' || user?.role === 'admin' || user?.role === 'expert') && (
                <button
                  onClick={() => onNavigate('reviewer')}
                  className="w-full px-4 py-3 rounded-lg bg-indigo-950/40 hover:bg-indigo-950/60 text-indigo-300 font-medium text-xs flex items-center justify-between border border-indigo-800/40 transition-all"
                >
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-indigo-400" />
                    <span>ورود به میزکار داوری همتا</span>
                  </div>
                  <ArrowRight className="w-3.5 h-3.5 text-indigo-400" />
                </button>
              )}
            </div>
          </div>

          {/* Protocol Information Box */}
          <div className="bg-slate-900/40 border border-slate-800/80 rounded-xl p-5 space-y-3">
            <h4 className="text-xs font-bold text-slate-300 flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-amber-500" />
              <span>اصول حاکمیت داده پلتفرم</span>
            </h4>
            <ul className="text-[11px] text-slate-400 space-y-2 leading-relaxed">
              <li className="flex items-start gap-1.5">
                <span className="text-amber-500 font-bold">•</span>
                <span>فقط منابع دارای دامنه رسمی قانون‌گذاری و قضایی کشور مجاز به ثبت هستند.</span>
              </li>
              <li className="flex items-start gap-1.5">
                <span className="text-amber-500 font-bold">•</span>
                <span>اسناد پرریسک (نسخ و اصلاح) نیازمند اجماع مستقل داوران هستند.</span>
              </li>
              <li className="flex items-start gap-1.5">
                <span className="text-amber-500 font-bold">•</span>
                <span>اعتبار MCC منحصراً به گزاره‌های حقوقی تأییدشده تخصیص می‌یابد.</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};
