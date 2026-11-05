import React, { useState, useEffect } from 'react';
import {
  Users,
  Shield,
  BarChart3,
  Download,
  CheckCircle,
  XCircle,
  AlertCircle,
  Lock,
  RefreshCw,
  Key,
  ShieldCheck,
  Award,
  BookOpen,
  Clock,
  Layers,
  UserCheck,
  UserX,
} from 'lucide-react';
import { apiClient } from '../api/client';
import {
  UserAdminItem,
  AdminOverviewStats,
  AdminExportOverview,
  UserProfile,
} from '../types';

interface AdminPanelProps {
  currentUser: UserProfile | null;
}

export const AdminPanel: React.FC<AdminPanelProps> = ({ currentUser }) => {
  const [activeTab, setActiveTab] = useState<'users' | 'stats' | 'export'>('users');

  // Users state
  const [users, setUsers] = useState<UserAdminItem[]>([]);
  const [totalUsers, setTotalUsers] = useState(0);
  const [roleFilter, setRoleFilter] = useState<string>('');
  const [activeFilter, setActiveFilter] = useState<string>('');
  const [loadingUsers, setLoadingUsers] = useState(false);

  // Stats state
  const [stats, setStats] = useState<AdminOverviewStats | null>(null);
  const [loadingStats, setLoadingStats] = useState(false);

  // Export state
  const [exportOverview, setExportOverview] = useState<AdminExportOverview | null>(null);
  const [gatewayToken, setGatewayToken] = useState('');
  const [isExporting, setIsExporting] = useState(false);
  const [exportMessage, setExportMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // General feedback
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  // Fetch Users
  const fetchUsers = async () => {
    setLoadingUsers(true);
    setActionError(null);
    try {
      const activeParam = activeFilter === 'true' ? true : activeFilter === 'false' ? false : undefined;
      const res = await apiClient.getAdminUsers(roleFilter || undefined, activeParam);
      setUsers(res.users);
      setTotalUsers(res.total);
    } catch (err: any) {
      setActionError(err.message || 'خطا در واکشی فهرست کاربران.');
    } finally {
      setLoadingUsers(false);
    }
  };

  // Fetch Stats
  const fetchStats = async () => {
    setLoadingStats(true);
    try {
      const res = await apiClient.getAdminStats();
      setStats(res);
    } catch (err: any) {
      setActionError(err.message || 'خطا در واکشی آمار سیستم.');
    } finally {
      setLoadingStats(false);
    }
  };

  // Fetch Export Overview
  const fetchExportOverview = async () => {
    try {
      const res = await apiClient.getAdminExportOverview();
      setExportOverview(res);
    } catch (err: any) {
      setActionError(err.message || 'خطا در دریافت وضعیت درگاه استخراج.');
    }
  };

  useEffect(() => {
    if (!currentUser || currentUser.role !== 'admin') return;
    if (activeTab === 'users') fetchUsers();
    if (activeTab === 'stats') fetchStats();
    if (activeTab === 'export') fetchExportOverview();
  }, [activeTab, roleFilter, activeFilter, currentUser]);

  // Actions
  const handleToggleActive = async (userId: string, currentStatus: boolean) => {
    setActionError(null);
    setActionSuccess(null);
    try {
      const res = await apiClient.toggleUserActivation(userId, !currentStatus);
      setActionSuccess(res.message);
      setUsers((prev) =>
        prev.map((u) => (u.id === userId ? { ...u, is_active: !currentStatus } : u))
      );
    } catch (err: any) {
      setActionError(err.message || 'خطا در تغییر وضعیت دسترسی کاربر.');
    }
  };

  const handleRoleChange = async (userId: string, newRole: string) => {
    setActionError(null);
    setActionSuccess(null);
    try {
      const res = await apiClient.updateUserRole(userId, newRole);
      setActionSuccess(res.message);
      setUsers((prev) =>
        prev.map((u) => (u.id === userId ? { ...u, role: newRole as any } : u))
      );
    } catch (err: any) {
      setActionError(err.message || 'خطا در تغییر نقش کاربر.');
    }
  };

  // Export Download Trigger
  const handleDownloadDataset = async () => {
    if (!gatewayToken.trim()) {
      setExportMessage({ type: 'error', text: 'لطفاً توکن اختصاصی درگاه (EXPORT_GATEWAY_TOKEN) را وارد نمایید.' });
      return;
    }

    setIsExporting(true);
    setExportMessage(null);
    try {
      const blob = await apiClient.downloadDatasetJsonl(gatewayToken.trim());
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `dataset_${new Date().toISOString().split('T')[0]}.jsonl`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      setExportMessage({
        type: 'success',
        text: 'بسته داده‌های تاییدشده (dataset.jsonl) با موفقیت تولید و دانلود شد.',
      });
    } catch (err: any) {
      setExportMessage({
        type: 'error',
        text: err.message || 'خطا در دانلود دیتاست استخراجی. از صحت توکن اطمینان حاصل کنید.',
      });
    } finally {
      setIsExporting(false);
    }
  };

  if (!currentUser || currentUser.role !== 'admin') {
    return (
      <div className="max-w-4xl mx-auto py-16 px-4 text-center space-y-4">
        <Lock className="w-16 h-16 text-rose-500 mx-auto" />
        <h2 className="text-2xl font-bold text-white">دسترسی غیرمجاز</h2>
        <p className="text-sm text-slate-400">
          تنها مدیران ارشد سیستم دارای مجوز مشاهده و پیکربندی میزکار مدیریت هستند.
        </p>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-amber-500/30 bg-amber-500/10 text-[11px] font-mono text-amber-400 font-semibold mb-2">
            ADMIN CONSOLE · GOVERNED GATEWAY
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white">
            میزکار مدیریت و درگاه استخراج داده
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            نظارت بر داوران و مشارکت‌کنندگان، بررسی سلامت چرخه داده‌ها و استخراج دستی بسته‌های تاییدشده
          </p>
        </div>

        {/* Navigation Tabs */}
        <div className="flex items-center gap-2 p-1 bg-slate-900 border border-slate-800 rounded-xl">
          <button
            onClick={() => setActiveTab('users')}
            className={`px-4 py-2 rounded-lg text-xs font-semibold flex items-center gap-2 transition-all ${
              activeTab === 'users'
                ? 'bg-amber-500 text-slate-950 shadow-md font-bold'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Users className="w-4 h-4" />
            <span>مدیریت کاربران</span>
          </button>

          <button
            onClick={() => setActiveTab('stats')}
            className={`px-4 py-2 rounded-lg text-xs font-semibold flex items-center gap-2 transition-all ${
              activeTab === 'stats'
                ? 'bg-amber-500 text-slate-950 shadow-md font-bold'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <BarChart3 className="w-4 h-4" />
            <span>آمار کلان</span>
          </button>

          <button
            onClick={() => setActiveTab('export')}
            className={`px-4 py-2 rounded-lg text-xs font-semibold flex items-center gap-2 transition-all ${
              activeTab === 'export'
                ? 'bg-amber-500 text-slate-950 shadow-md font-bold'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Download className="w-4 h-4" />
            <span>درگاه مالک (Export)</span>
          </button>
        </div>
      </div>

      {/* Action Messages */}
      {actionError && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{actionError}</span>
        </div>
      )}
      {actionSuccess && (
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs flex items-center gap-2">
          <CheckCircle className="w-4 h-4 shrink-0" />
          <span>{actionSuccess}</span>
        </div>
      )}

      {/* TAB 1: User Management */}
      {activeTab === 'users' && (
        <div className="space-y-6">
          {/* Filters Bar */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 flex flex-wrap items-center justify-between gap-4">
            <div className="flex flex-wrap items-center gap-4">
              <div>
                <label className="block text-[11px] text-slate-400 mb-1">فیلتر نقش:</label>
                <select
                  value={roleFilter}
                  onChange={(e) => setRoleFilter(e.target.value)}
                  className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-amber-500"
                >
                  <option value="">همه نقش‌ها</option>
                  <option value="contributor">مشارکت‌کننده</option>
                  <option value="reviewer">داور حقوقی</option>
                  <option value="expert">کارشناس ارشد</option>
                  <option value="admin">مدیر سیستم</option>
                </select>
              </div>

              <div>
                <label className="block text-[11px] text-slate-400 mb-1">وضعیت دسترسی:</label>
                <select
                  value={activeFilter}
                  onChange={(e) => setActiveFilter(e.target.value)}
                  className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-amber-500"
                >
                  <option value="">همه وضعیت‌ها</option>
                  <option value="true">فقط فعال</option>
                  <option value="false">فقط غیرفعال</option>
                </select>
              </div>
            </div>

            <button
              onClick={fetchUsers}
              className="px-3 py-1.5 rounded-lg border border-slate-700 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition-all flex items-center gap-1.5"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loadingUsers ? 'animate-spin' : ''}`} />
              <span>به‌روزرسانی لیست</span>
            </button>
          </div>

          {/* Users Table */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
            <div className="overflow-x-auto">
              <table className="w-full text-right text-xs">
                <thead className="bg-slate-950 border-b border-slate-800 text-slate-400 font-semibold">
                  <tr>
                    <th className="p-4">نام کامل</th>
                    <th className="p-4">ایمیل کاربری</th>
                    <th className="p-4">نقش سیستمی</th>
                    <th className="p-4">وضعیت</th>
                    <th className="p-4">امتیازات MCC</th>
                    <th className="p-4 text-center">مدیریت و عملیات</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/80">
                  {users.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="p-8 text-center text-slate-500">
                        کاربری با این مشخصات یافت نشد.
                      </td>
                    </tr>
                  ) : (
                    users.map((u) => (
                      <tr key={u.id} className="hover:bg-slate-850/50 transition-colors">
                        <td className="p-4 font-bold text-slate-200">
                          {u.full_name || 'کاربر بدون نام'}
                        </td>
                        <td className="p-4 font-mono text-slate-400">{u.email}</td>
                        <td className="p-4">
                          <span
                            className={`inline-block px-2.5 py-0.5 rounded-full text-[11px] font-semibold border ${
                              u.role === 'admin'
                                ? 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                                : u.role === 'reviewer'
                                ? 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30'
                                : u.role === 'expert'
                                ? 'bg-purple-500/10 text-purple-400 border-purple-500/30'
                                : 'bg-slate-800 text-slate-300 border-slate-700'
                            }`}
                          >
                            {u.role === 'admin'
                              ? 'مدیر ارشد'
                              : u.role === 'reviewer'
                              ? 'داور حقوقی'
                              : u.role === 'expert'
                              ? 'کارشناس ارشد'
                              : 'مشارکت‌کننده'}
                          </span>
                        </td>
                        <td className="p-4">
                          {u.is_active ? (
                            <span className="inline-flex items-center gap-1 text-emerald-400">
                              <CheckCircle className="w-3.5 h-3.5" />
                              <span>فعال</span>
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 text-rose-400">
                              <XCircle className="w-3.5 h-3.5" />
                              <span>غیرفعال</span>
                            </span>
                          )}
                        </td>
                        <td className="p-4 font-mono font-bold text-amber-400">
                          {u.total_credits.toLocaleString('fa-IR')} MCC
                        </td>
                        <td className="p-4 text-center">
                          <div className="flex items-center justify-center gap-2">
                            {/* Role select */}
                            <select
                              value={u.role}
                              onChange={(e) => handleRoleChange(u.id, e.target.value)}
                              disabled={u.id === currentUser.id}
                              className="bg-slate-950 border border-slate-800 rounded px-2 py-1 text-[11px] text-slate-300 focus:outline-none focus:border-amber-500 disabled:opacity-40"
                            >
                              <option value="contributor">مشارکت‌کننده</option>
                              <option value="reviewer">داور</option>
                              <option value="expert">کارشناس</option>
                              <option value="admin">مدیر</option>
                            </select>

                            {/* Active toggle */}
                            <button
                              onClick={() => handleToggleActive(u.id, u.is_active)}
                              disabled={u.id === currentUser.id}
                              className={`p-1.5 rounded-lg border transition-all disabled:opacity-30 ${
                                u.is_active
                                  ? 'border-rose-500/30 text-rose-400 hover:bg-rose-500/10'
                                  : 'border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/10'
                              }`}
                              title={u.is_active ? 'غیرفعال‌سازی حساب' : 'فعال‌سازی حساب'}
                            >
                              {u.is_active ? (
                                <UserX className="w-3.5 h-3.5" />
                              ) : (
                                <UserCheck className="w-3.5 h-3.5" />
                              )}
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
            <div className="p-3 bg-slate-950 text-slate-400 text-xs border-t border-slate-800">
              تعداد کل کاربران: {totalUsers.toLocaleString('fa-IR')}
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: System Stats & Telemetry */}
      {activeTab === 'stats' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-2">
              <div className="flex items-center justify-between text-slate-400 text-xs font-semibold">
                <span>کل کاربران</span>
                <Users className="w-5 h-5 text-amber-400" />
              </div>
              <div className="text-3xl font-extrabold text-white font-mono">
                {stats?.total_users.toLocaleString('fa-IR')}
              </div>
              <div className="text-[11px] text-slate-500">حساب‌های کاربری فعال و ثبت‌شده</div>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-2">
              <div className="flex items-center justify-between text-slate-400 text-xs font-semibold">
                <span>کل مشارکت‌های دریافتی</span>
                <BookOpen className="w-5 h-5 text-amber-400" />
              </div>
              <div className="text-3xl font-extrabold text-white font-mono">
                {stats?.total_submissions.toLocaleString('fa-IR')}
              </div>
              <div className="text-[11px] text-slate-500">اسناد حقوقی ثبت‌شده در پلتفرم</div>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-2">
              <div className="flex items-center justify-between text-slate-400 text-xs font-semibold">
                <span>در حال داوری و کوئوروم</span>
                <Clock className="w-5 h-5 text-sky-400" />
              </div>
              <div className="text-3xl font-extrabold text-sky-400 font-mono">
                {stats?.pending_reviews.toLocaleString('fa-IR')}
              </div>
              <div className="text-[11px] text-slate-500">نیازمند رأی ۱ تا ۳ داور همتا</div>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-2">
              <div className="flex items-center justify-between text-slate-400 text-xs font-semibold">
                <span>تأیید نهایی و اصیل</span>
                <CheckCircle className="w-5 h-5 text-emerald-400" />
              </div>
              <div className="text-3xl font-extrabold text-emerald-400 font-mono">
                {stats?.accepted_submissions.toLocaleString('fa-IR')}
              </div>
              <div className="text-[11px] text-slate-500">آماده ورود به بسته استخراجی گراف</div>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-2">
              <div className="flex items-center justify-between text-slate-400 text-xs font-semibold">
                <span>مشارکت‌های رد شده</span>
                <XCircle className="w-5 h-5 text-rose-400" />
              </div>
              <div className="text-3xl font-extrabold text-rose-400 font-mono">
                {stats?.rejected_submissions.toLocaleString('fa-IR')}
              </div>
              <div className="text-[11px] text-slate-500">عدم احراز شرایط یا مخدوش بودن سند</div>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-2">
              <div className="flex items-center justify-between text-slate-400 text-xs font-semibold">
                <span>کل اعتبارات MCC توزیع‌شده</span>
                <Award className="w-5 h-5 text-amber-400" />
              </div>
              <div className="text-3xl font-extrabold text-amber-400 font-mono">
                {stats?.total_credits_awarded.toLocaleString('fa-IR')}
              </div>
              <div className="text-[11px] text-amber-500/80">پاداش‌های اقتصادی اختصاص‌یافته</div>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-2">
              <div className="flex items-center justify-between text-slate-400 text-xs font-semibold">
                <span>فایل‌های ایزوله قرنطینه</span>
                <ShieldCheck className="w-5 h-5 text-indigo-400" />
              </div>
              <div className="text-3xl font-extrabold text-indigo-400 font-mono">
                {stats?.quarantine_files_count.toLocaleString('fa-IR')}
              </div>
              <div className="text-[11px] text-slate-500">فایل‌های خام ایزوله‌شده فیزیکی</div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: Owner Export Gateway (Haji Mamad Console) */}
      {activeTab === 'export' && (
        <div className="max-w-4xl mx-auto space-y-6">
          {/* Air-gap Isolation Certificate Box */}
          <div className="p-6 rounded-2xl border-2 border-amber-500/40 bg-gradient-to-b from-amber-500/10 via-slate-900/60 to-slate-900 space-y-4">
            <div className="flex items-center justify-between flex-wrap gap-3 border-b border-slate-800 pb-4">
              <div className="flex items-center gap-3">
                <ShieldCheck className="w-7 h-7 text-amber-400" />
                <div>
                  <h3 className="text-lg font-bold text-white">درگاه استخراج ایزوله مالک (Haji Mamad Gateway)</h3>
                  <p className="text-xs text-amber-400/90 font-mono">
                    Air-Gap Isolation Invariant: STRICTLY ENFORCED · NO DIRECT GRAPH ROUTE
                  </p>
                </div>
              </div>
              <span className="px-3 py-1 rounded-full text-xs font-mono font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                ✓ ISOLATION VERIFIED
              </span>
            </div>

            <p className="text-xs text-slate-300 leading-relaxed">
              این درگاه تنها مسیر مجاز برای دریافت داده‌های نهایی‌شده مشارکت حقوقی است. فایل خروجی به‌صورت
              کاملاً رمزنگاری‌شده با فرمت استانداردی تولید می‌شود که پس از بازرسی و تایید شخصی توسط شما (حاجی ممد)،
              به‌صورت آفلاین و دستی وارد موتور حکمرانی KingMahouN خواهد شد.
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
              <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 space-y-1">
                <span className="text-slate-500 text-[11px]">اسناد تاییدشده آماده خروجی</span>
                <div className="text-2xl font-bold font-mono text-emerald-400">
                  {exportOverview?.total_export_ready.toLocaleString('fa-IR')} سند
                </div>
              </div>

              <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 space-y-1">
                <span className="text-slate-500 text-[11px]">اسکیمای دیتاست</span>
                <div className="text-sm font-bold font-mono text-amber-400 mt-1">
                  {exportOverview?.schema_version || 'mahoun-1.0'}
                </div>
              </div>

              <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 space-y-1">
                <span className="text-slate-500 text-[11px]">مهر اصالت استنادی</span>
                <div className="text-sm font-bold text-slate-200 mt-1">HMAC SHA-256 Provenance</div>
              </div>
            </div>
          </div>

          {/* Export Token & Action */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 sm:p-8 space-y-6">
            <h4 className="text-base font-bold text-white flex items-center gap-2">
              <Key className="w-5 h-5 text-amber-400" />
              <span>کلید امنیتی درگاه استخراج (EXPORT_GATEWAY_TOKEN)</span>
            </h4>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-2">
                توکن اختصاصی احراز هویت درگاه:
              </label>
              <div className="relative">
                <input
                  type="password"
                  value={gatewayToken}
                  onChange={(e) => setGatewayToken(e.target.value)}
                  placeholder="کلید محرمانه اختصاصی استخراج دیتاست را وارد کنید..."
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 pr-10 text-sm font-mono text-slate-200 focus:outline-none focus:border-amber-500 focus:ring-1 focus:ring-amber-500"
                />
                <Key className="w-4 h-4 text-slate-500 absolute right-3.5 top-3.5" />
              </div>
            </div>

            {exportMessage && (
              <div
                className={`p-4 rounded-xl text-xs flex items-center gap-2 ${
                  exportMessage.type === 'success'
                    ? 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-300'
                    : 'bg-rose-500/10 border border-rose-500/20 text-rose-300'
                }`}
              >
                {exportMessage.type === 'success' ? (
                  <CheckCircle className="w-4 h-4 shrink-0" />
                ) : (
                  <AlertCircle className="w-4 h-4 shrink-0" />
                )}
                <span>{exportMessage.text}</span>
              </div>
            )}

            <div className="pt-4 border-t border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-4">
              <div className="text-xs text-slate-400">
                خروجی با فرمت <span className="font-mono text-amber-400 font-bold">dataset.jsonl</span> شامل رکوردهای SourceSpan و ترازنامه‌های اصالت است.
              </div>
              <button
                onClick={handleDownloadDataset}
                disabled={isExporting || !exportOverview?.total_export_ready}
                className="w-full sm:w-auto px-6 py-3 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs transition-all shadow-lg shadow-amber-500/20 disabled:opacity-50 flex items-center justify-center gap-2"
              >
                <Download className={`w-4 h-4 ${isExporting ? 'animate-bounce' : ''}`} />
                <span>{isExporting ? 'در حال پکیج‌بندی و استخراج...' : 'استخراج و دانلود dataset.jsonl'}</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
