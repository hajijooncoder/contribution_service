import React, { useState, useEffect } from 'react';
import {
  Users,
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

  /* ═══════════ Access Denied ═══════════ */
  if (!currentUser || currentUser.role !== 'admin') {
    return (
      <div className="max-w-4xl mx-auto py-16 px-4 text-center space-y-4">
        <div className="w-16 h-16 mx-auto rounded-full bg-rose-500/10 border border-rose-500/20 flex items-center justify-center">
          <Lock className="w-8 h-8 text-rose-400" />
        </div>
        <h2 className="text-2xl font-bold text-[#e2e8f0]">دسترسی غیرمجاز</h2>
        <p className="text-sm text-[#94a3b8]">
          تنها مدیران ارشد سیستم دارای مجوز مشاهده و پیکربندی میزکار مدیریت هستند.
        </p>
      </div>
    );
  }

  /* ═══════════ Tab Button Helper ═══════════ */
  const TabButton = ({
    tab,
    icon: Icon,
    label,
  }: {
    tab: 'users' | 'stats' | 'export';
    icon: React.ElementType;
    label: string;
  }) => (
    <button
      onClick={() => setActiveTab(tab)}
      className={`px-4 py-2.5 rounded-xl text-xs font-semibold flex items-center gap-2 transition-all duration-200 ${
        activeTab === tab
          ? 'bg-gradient-to-l from-[#00e5ff] via-[#0284c7] to-[#0369a1] text-white shadow-md shadow-[#00e5ff]/20 border border-[#00e5ff]/40 font-bold'
          : 'text-[#94a3b8] hover:text-[#e2e8f0] hover:bg-[#0b1e36]/60'
      }`}
    >
      <Icon className="w-4 h-4" />
      <span>{label}</span>
    </button>
  );

  /* ═══════════ Stat Card Helper ═══════════ */
  const StatCard = ({
    label,
    value,
    subtitle,
    icon: Icon,
    color = 'gold',
    delay = 0,
  }: {
    label: string;
    value: string | undefined;
    subtitle: string;
    icon: React.ElementType;
    color?: 'gold' | 'emerald' | 'sky' | 'rose' | 'indigo';
    delay?: number;
  }) => {
    const colorMap = {
      gold: { icon: 'text-[#00e5ff]', value: 'text-[#00e5ff]', subtitle: 'text-[#00e5ff]/70' },
      emerald: { icon: 'text-emerald-400', value: 'text-emerald-400', subtitle: 'text-[#94a3b8]' },
      sky: { icon: 'text-sky-400', value: 'text-sky-400', subtitle: 'text-[#94a3b8]' },
      rose: { icon: 'text-rose-400', value: 'text-rose-400', subtitle: 'text-[#94a3b8]' },
      indigo: { icon: 'text-indigo-400', value: 'text-indigo-400', subtitle: 'text-[#94a3b8]' },
    };
    const c = colorMap[color];

    return (
      <div
        className="bg-[#071527]/90 border border-[#112d4e] border-t-[#00e5ff]/30 rounded-2xl p-5 space-y-2 hover:border-[#00e5ff]/40 hover:border-t-[#00e5ff]/60 transition-all duration-300 animate-slide-up"
        style={{ animationDelay: `${delay}ms` }}
      >
        <div className="flex items-center justify-between text-[#94a3b8] text-xs font-semibold">
          <span>{label}</span>
          <div className="w-9 h-9 rounded-xl bg-[#0b1e36] flex items-center justify-center">
            <Icon className={`w-5 h-5 ${c.icon}`} />
          </div>
        </div>
        <div className={`text-3xl font-extrabold font-mono ${c.value}`}>
          {value ?? '—'}
        </div>
        <div className={`text-[11px] ${c.subtitle}`}>{subtitle}</div>
      </div>
    );
  };

  return (
    <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8 space-y-8">
      {/* ═══════ Header ═══════ */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#112d4e] pb-6">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-[#00e5ff]/30 bg-[#00e5ff]/5 text-[11px] font-mono text-[#00e5ff] font-semibold mb-2">
            ADMIN CONSOLE · GOVERNED GATEWAY
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-[#e2e8f0]">
            میزکار مدیریت و درگاه استخراج داده
          </h1>
          <p className="text-xs text-[#94a3b8] mt-1">
            نظارت بر داوران و مشارکت‌کنندگان، بررسی سلامت چرخه داده‌ها و استخراج دستی بسته‌های تاییدشده
          </p>
        </div>

        {/* Navigation Tabs */}
        <div className="flex items-center gap-1.5 p-1.5 bg-[#071527] border border-[#112d4e] rounded-2xl">
          <TabButton tab="users" icon={Users} label="مدیریت کاربران" />
          <TabButton tab="stats" icon={BarChart3} label="آمار کلان" />
          <TabButton tab="export" icon={Download} label="درگاه مالک (Export)" />
        </div>
      </div>

      {/* ═══════ Action Messages ═══════ */}
      {actionError && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center gap-2 animate-fade-in">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{actionError}</span>
        </div>
      )}
      {actionSuccess && (
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs flex items-center gap-2 animate-fade-in">
          <CheckCircle className="w-4 h-4 shrink-0" />
          <span>{actionSuccess}</span>
        </div>
      )}

      {/* ═══════════ TAB 1: User Management ═══════════ */}
      {activeTab === 'users' && (
        <div className="space-y-6 animate-fade-in">
          {/* Filters Bar */}
          <div className="bg-[#071527]/60 border border-[#112d4e] rounded-2xl p-4 flex flex-wrap items-center justify-between gap-4">
            <div className="flex flex-wrap items-center gap-4">
              <div>
                <label className="block text-[11px] text-[#94a3b8] mb-1">فیلتر نقش:</label>
                <select
                  value={roleFilter}
                  onChange={(e) => setRoleFilter(e.target.value)}
                  className="bg-[#030712] border border-[#112d4e] rounded-xl px-3 py-1.5 text-xs text-[#e2e8f0] focus:outline-none focus:border-[#00e5ff] transition-colors"
                >
                  <option value="">همه نقش‌ها</option>
                  <option value="contributor">مشارکت‌کننده</option>
                  <option value="reviewer">داور حقوقی</option>
                  <option value="expert">کارشناس ارشد</option>
                  <option value="admin">مدیر سیستم</option>
                </select>
              </div>

              <div>
                <label className="block text-[11px] text-[#94a3b8] mb-1">وضعیت دسترسی:</label>
                <select
                  value={activeFilter}
                  onChange={(e) => setActiveFilter(e.target.value)}
                  className="bg-[#030712] border border-[#112d4e] rounded-xl px-3 py-1.5 text-xs text-[#e2e8f0] focus:outline-none focus:border-[#00e5ff] transition-colors"
                >
                  <option value="">همه وضعیت‌ها</option>
                  <option value="true">فقط فعال</option>
                  <option value="false">فقط غیرفعال</option>
                </select>
              </div>
            </div>

            <button
              onClick={fetchUsers}
              className="px-4 py-2 rounded-xl border border-[#112d4e] bg-[#0b1e36] hover:bg-[#112d4e] text-[#e2e8f0] text-xs font-medium transition-all duration-200 flex items-center gap-1.5 hover:border-[#00e5ff]/40"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loadingUsers ? 'animate-spin' : ''}`} />
              <span>به‌روزرسانی لیست</span>
            </button>
          </div>

          {/* Users Table */}
          <div className="bg-[#071527] border border-[#112d4e] rounded-2xl overflow-hidden shadow-xl shadow-[#030712]/50">
            <div className="overflow-x-auto">
              <table className="w-full text-right text-xs">
                <thead className="bg-[#030712] border-b border-[#112d4e] text-[#94a3b8] font-semibold">
                  <tr>
                    <th className="p-4">نام کامل</th>
                    <th className="p-4">ایمیل کاربری</th>
                    <th className="p-4">نقش سیستمی</th>
                    <th className="p-4">وضعیت</th>
                    <th className="p-4">امتیازات MCC</th>
                    <th className="p-4 text-center">مدیریت و عملیات</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#112d4e]/60">
                  {users.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="p-8 text-center text-[#64748b]">
                        کاربری با این مشخصات یافت نشد.
                      </td>
                    </tr>
                  ) : (
                    users.map((u) => (
                      <tr key={u.id} className="hover:bg-[#0b1e36]/50 transition-colors duration-150">
                        <td className="p-4 font-bold text-[#e2e8f0]">
                          {u.full_name || 'کاربر بدون نام'}
                        </td>
                        <td className="p-4 font-mono text-[#94a3b8]">{u.email}</td>
                        <td className="p-4">
                          <span
                            className={`inline-block px-2.5 py-0.5 rounded-full text-[11px] font-semibold border ${
                              u.role === 'admin'
                                ? 'bg-[#00e5ff]/10 text-[#00e5ff] border-[#00e5ff]/30'
                                : u.role === 'reviewer'
                                ? 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30'
                                : u.role === 'expert'
                                ? 'bg-purple-500/10 text-purple-400 border-purple-500/30'
                                : 'bg-[#0b1e36] text-[#94a3b8] border-[#112d4e]'
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
                        <td className="p-4 font-mono font-bold text-[#00e5ff]">
                          {u.total_credits.toLocaleString('fa-IR')} MCC
                        </td>
                        <td className="p-4 text-center">
                          <div className="flex items-center justify-center gap-2">
                            {/* Role select */}
                            <select
                              value={u.role}
                              onChange={(e) => handleRoleChange(u.id, e.target.value)}
                              disabled={u.id === currentUser.id}
                              className="bg-[#030712] border border-[#112d4e] rounded-lg px-2 py-1 text-[11px] text-[#e2e8f0] focus:outline-none focus:border-[#00e5ff] disabled:opacity-40 transition-colors"
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
                              className={`p-1.5 rounded-lg border transition-all duration-200 disabled:opacity-30 ${
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
            <div className="p-3 bg-[#030712] text-[#94a3b8] text-xs border-t border-[#112d4e]">
              تعداد کل کاربران: {totalUsers.toLocaleString('fa-IR')}
            </div>
          </div>
        </div>
      )}

      {/* ═══════════ TAB 2: System Stats & Telemetry ═══════════ */}
      {activeTab === 'stats' && (
        <div className="space-y-6 animate-fade-in">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard
              label="کل کاربران"
              value={stats?.total_users.toLocaleString('fa-IR')}
              subtitle="حساب‌های کاربری فعال و ثبت‌شده"
              icon={Users}
              color="gold"
              delay={0}
            />
            <StatCard
              label="کل مشارکت‌های دریافتی"
              value={stats?.total_submissions.toLocaleString('fa-IR')}
              subtitle="اسناد حقوقی ثبت‌شده در پلتفرم"
              icon={BookOpen}
              color="gold"
              delay={60}
            />
            <StatCard
              label="در حال داوری و کوئوروم"
              value={stats?.pending_reviews.toLocaleString('fa-IR')}
              subtitle="نیازمند رأی ۱ تا ۳ داور همتا"
              icon={Clock}
              color="sky"
              delay={120}
            />
            <StatCard
              label="تأیید نهایی و اصیل"
              value={stats?.accepted_submissions.toLocaleString('fa-IR')}
              subtitle="آماده ورود به بسته استخراجی گراف"
              icon={CheckCircle}
              color="emerald"
              delay={180}
            />
            <StatCard
              label="مشارکت‌های رد شده"
              value={stats?.rejected_submissions.toLocaleString('fa-IR')}
              subtitle="عدم احراز شرایط یا مخدوش بودن سند"
              icon={XCircle}
              color="rose"
              delay={240}
            />
            <StatCard
              label="کل اعتبارات MCC توزیع‌شده"
              value={stats?.total_credits_awarded.toLocaleString('fa-IR')}
              subtitle="پاداش‌های اقتصادی اختصاص‌یافته"
              icon={Award}
              color="gold"
              delay={300}
            />
            <StatCard
              label="فایل‌های ایزوله قرنطینه"
              value={stats?.quarantine_files_count.toLocaleString('fa-IR')}
              subtitle="فایل‌های خام ایزوله‌شده فیزیکی"
              icon={ShieldCheck}
              color="indigo"
              delay={360}
            />
          </div>
        </div>
      )}

      {/* ═══════════ TAB 3: Owner Export Gateway ═══════════ */}
      {activeTab === 'export' && (
        <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
          {/* Air-gap Isolation Certificate Box */}
          <div className="p-6 rounded-2xl border-2 border-[#00e5ff]/30 bg-gradient-to-b from-[#00e5ff]/5 via-[#071527]/60 to-[#071527] space-y-4">
            <div className="flex items-center justify-between flex-wrap gap-3 border-b border-[#112d4e] pb-4">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-xl bg-[#00e5ff]/10 border border-[#00e5ff]/20 flex items-center justify-center">
                  <ShieldCheck className="w-7 h-7 text-[#00e5ff]" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-[#e2e8f0]">درگاه استخراج ایزوله مالک (Haji Mamad Gateway)</h3>
                  <p className="text-xs text-[#00e5ff]/80 font-mono">
                    Air-Gap Isolation Invariant: STRICTLY ENFORCED · NO DIRECT GRAPH ROUTE
                  </p>
                </div>
              </div>
              <span className="px-3 py-1.5 rounded-full text-xs font-mono font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                ✓ ISOLATION VERIFIED
              </span>
            </div>

            <p className="text-xs text-[#cbd5e1] leading-relaxed">
              این درگاه تنها مسیر مجاز برای دریافت داده‌های نهایی‌شده مشارکت حقوقی است. فایل خروجی به‌صورت
              کاملاً رمزنگاری‌شده با فرمت استانداردی تولید می‌شود که پس از بازرسی و تایید شخصی توسط شما (حاجی ممد)،
              به‌صورت آفلاین و دستی وارد موتور حکمرانی KingMahouN خواهد شد.
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
              <div className="p-4 rounded-xl bg-[#030712]/80 border border-[#112d4e] space-y-1 hover:border-[#00e5ff]/30 transition-colors">
                <span className="text-[#64748b] text-[11px]">اسناد تاییدشده آماده خروجی</span>
                <div className="text-2xl font-bold font-mono text-emerald-400">
                  {exportOverview?.total_export_ready.toLocaleString('fa-IR')} سند
                </div>
              </div>

              <div className="p-4 rounded-xl bg-[#030712]/80 border border-[#112d4e] space-y-1 hover:border-[#00e5ff]/30 transition-colors">
                <span className="text-[#64748b] text-[11px]">اسکیمای دیتاست</span>
                <div className="text-sm font-bold font-mono text-[#00e5ff] mt-1">
                  {exportOverview?.schema_version || 'mahoun-1.0'}
                </div>
              </div>

              <div className="p-4 rounded-xl bg-[#030712]/80 border border-[#112d4e] space-y-1 hover:border-[#00e5ff]/30 transition-colors">
                <span className="text-[#64748b] text-[11px]">مهر اصالت استنادی</span>
                <div className="text-sm font-bold text-[#e2e8f0] mt-1">HMAC SHA-256 Provenance</div>
              </div>
            </div>
          </div>

          {/* Export Token & Action */}
          <div className="bg-[#071527] border border-[#112d4e] rounded-2xl p-6 sm:p-8 space-y-6">
            <h4 className="text-base font-bold text-[#e2e8f0] flex items-center gap-2">
              <Key className="w-5 h-5 text-[#00e5ff]" />
              <span>کلید امنیتی درگاه استخراج (EXPORT_GATEWAY_TOKEN)</span>
            </h4>

            <div>
              <label className="block text-xs font-semibold text-[#cbd5e1] mb-2">
                توکن اختصاصی احراز هویت درگاه:
              </label>
              <div className="relative">
                <input
                  type="password"
                  value={gatewayToken}
                  onChange={(e) => setGatewayToken(e.target.value)}
                  placeholder="کلید محرمانه اختصاصی استخراج دیتاست را وارد کنید..."
                  className="w-full bg-[#030712] border border-[#112d4e] rounded-xl px-4 py-3 pr-10 text-sm font-mono text-[#e2e8f0] focus:outline-none focus:border-[#00e5ff] focus:ring-1 focus:ring-[#00e5ff]/30 transition-all"
                />
                <Key className="w-4 h-4 text-[#64748b] absolute right-3.5 top-3.5" />
              </div>
            </div>

            {exportMessage && (
              <div
                className={`p-4 rounded-xl text-xs flex items-center gap-2 animate-fade-in ${
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

            <div className="pt-4 border-t border-[#112d4e] flex flex-col sm:flex-row items-center justify-between gap-4">
              <div className="text-xs text-[#94a3b8]">
                خروجی با فرمت <span className="font-mono text-[#00e5ff] font-bold">dataset.jsonl</span> شامل رکوردهای SourceSpan و ترازنامه‌های اصالت است.
              </div>
              <button
                onClick={handleDownloadDataset}
                disabled={isExporting || !exportOverview?.total_export_ready}
                className="w-full sm:w-auto px-6 py-3 rounded-xl bg-gradient-to-l from-[#00e5ff] via-[#0284c7] to-[#0369a1] hover:from-[#38bdf8] hover:to-[#0284c7] text-white font-bold text-xs transition-all duration-300 shadow-lg shadow-[#00e5ff]/20 border border-[#00e5ff]/40 disabled:opacity-50 flex items-center justify-center gap-2"
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
