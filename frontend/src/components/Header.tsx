import React, { useState } from 'react';
import {
  LayoutDashboard,
  BookOpen,
  History,
  CheckSquare,
  Award,
  LogIn,
  LogOut,
  Shield,
  Menu,
  X,
  ChevronLeft,
  Scale,
  Download,
} from 'lucide-react';
import { UserProfile } from '../types';

interface HeaderProps {
  user: UserProfile | null;
  activeTab: 'dashboard' | 'submit' | 'history' | 'reviewer' | 'admin';
  setActiveTab: (tab: 'dashboard' | 'submit' | 'history' | 'reviewer' | 'admin') => void;
  onLoginClick: () => void;
  onLogoutClick: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  user,
  activeTab,
  setActiveTab,
  onLoginClick,
  onLogoutClick,
}) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const getRoleLabel = (role?: string) => {
    switch (role) {
      case 'admin':
        return 'مدیر ارشد سامانه';
      case 'reviewer':
        return 'داور رسمی حقوقی';
      case 'expert':
        return 'کارشناس ارشد';
      default:
        return 'پژوهشگر حقوقی';
    }
  };

  const getBreadcrumbTitle = (tab: string) => {
    switch (tab) {
      case 'dashboard':
        return 'داشبورد و وضعیت کلان';
      case 'submit':
        return 'ثبت و ارسال مشارکت حقوقی';
      case 'history':
        return 'تاریخچه و پیگیری مشارکت‌ها';
      case 'reviewer':
        return 'کارتابل داوری همتا و حدنصاب اجماع';
      case 'admin':
        return 'کنسول مدیریت و استخراج ایزوله';
      default:
        return 'میزکار پژوهشی';
    }
  };

  const navItems = [
    {
      id: 'dashboard' as const,
      label: 'داشبورد',
      icon: LayoutDashboard,
      visible: true,
    },
    {
      id: 'submit' as const,
      label: 'ارسال مشارکت',
      icon: BookOpen,
      visible: true,
    },
    {
      id: 'history' as const,
      label: 'مشارکت‌های من',
      icon: History,
      visible: true,
    },
    {
      id: 'reviewer' as const,
      label: 'میزکار داوری',
      icon: CheckSquare,
      visible: Boolean(user?.role === 'reviewer' || user?.role === 'admin' || user?.role === 'expert'),
    },
    {
      id: 'admin' as const,
      label: 'مدیریت سیستم',
      icon: Shield,
      visible: Boolean(user?.role === 'admin'),
    },
  ];

  const handleSelectTab = (tab: 'dashboard' | 'submit' | 'history' | 'reviewer' | 'admin') => {
    setActiveTab(tab);
    setMobileMenuOpen(false);
  };

  return (
    <header className="sticky top-0 z-40 bg-[#030712]/95 backdrop-blur-md border-b border-[#112d4e]/80 shadow-lg shadow-black/40 relative after:absolute after:bottom-0 after:left-0 after:right-0 after:h-[1px] after:bg-gradient-to-r after:from-transparent after:via-[#00e5ff]/40 after:to-transparent after:pointer-events-none">
      {/* Top Breadcrumb Micro-bar */}
      <div className="hidden lg:block border-b border-[#112d4e]/50 bg-[#040e1c]/90 px-4 sm:px-6 lg:px-8 py-1">
        <div className="max-w-7xl mx-auto flex items-center justify-between text-[11px] text-slate-400">
          <div className="flex items-center gap-1.5 font-sans">
            <span className="text-slate-400">پلتفرم مستقل مشارکت MAHOUNN</span>
            <ChevronLeft className="w-3 h-3 text-slate-600" />
            <span className="text-[#00e5ff] font-medium">{getBreadcrumbTitle(activeTab)}</span>
          </div>
          <div className="flex items-center gap-3.5 text-[10px] text-slate-400 font-mono">
            <a
              href="/whitepaper.pdf"
              download="MAHOUNN-Whitepaper.pdf"
              target="_blank"
              rel="noopener noreferrer"
              className="text-[#00e5ff] hover:text-[#38bdf8] flex items-center gap-1.5 font-sans font-semibold transition-colors py-0.5 px-2 rounded-md bg-[#00e5ff]/10 hover:bg-[#00e5ff]/20 border border-[#00e5ff]/30"
              title="دانلود سند وایت‌پیپر پلتفرم MAHOUNN"
            >
              <Download className="w-3 h-3 text-[#00e5ff]" />
              <span>دانلود وایت‌پیپر (PDF)</span>
            </a>
            <span className="text-slate-600">|</span>
            <span className="flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              AIR-GAP ENCLAVE VERIFIED
            </span>
            <span className="text-[#00e5ff]/70 border-r border-[#112d4e] pr-4">HMAC AUDIT LEDGER v2.1</span>
          </div>
        </div>
      </div>

      {/* Main Navigation Bar */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand Identity */}
          <div className="flex items-center space-x-3.5 space-x-reverse">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#0b1e36] to-[#071527] border border-[#00e5ff]/40 flex items-center justify-center shadow-md shadow-black/40 relative before:absolute before:inset-0 before:rounded-xl before:border before:border-[#00e5ff]/20 before:pointer-events-none">
              <Scale className="w-5 h-5 text-[#00e5ff]" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xl font-extrabold tracking-tight text-white font-mono">
                  <span aria-hidden="true">MahounN</span>
                  <span className="sr-only">MAHOUNN</span>
                </span>
                <span className="hidden sm:inline-block px-1.5 py-0.5 rounded text-[10px] font-mono bg-[#0b1e36] border border-[#112d4e] text-[#00e5ff]">
                  LEGAL TECH
                </span>
              </div>
              <span className="text-[10px] text-slate-400 block -mt-0.5">
                Legal Contribution Platform
              </span>
            </div>
          </div>

          {/* Desktop Navigation Tabs */}
          <nav className="hidden md:flex items-center space-x-1 space-x-reverse" aria-label="ناوبری اصلی">
            {navItems
              .filter((item) => item.visible)
              .map((item) => {
                const Icon = item.icon;
                const isActive = activeTab === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => handleSelectTab(item.id)}
                    className={`flex items-center space-x-2 space-x-reverse px-3.5 py-2 rounded-xl text-xs font-medium transition-all ${
                      isActive
                        ? 'bg-[#0b1e36] text-[#00e5ff] border border-[#00e5ff]/50 font-bold shadow-sm shadow-[#00e5ff]/10 relative after:absolute after:bottom-0 after:left-3 after:right-3 after:h-[1px] after:bg-[#00e5ff]/50'
                        : 'text-slate-300 hover:text-white hover:bg-[#0b1e36]/60 border border-transparent'
                    }`}
                  >
                    <Icon className={`w-4 h-4 ${isActive ? 'text-[#00e5ff]' : 'text-slate-400'}`} />
                    <span>{item.label}</span>
                  </button>
                );
              })}
          </nav>

          {/* User Profile / Status / Login Action */}
          <div className="flex items-center space-x-3 space-x-reverse">
            {user ? (
              <div className="flex items-center space-x-3 space-x-reverse">
                <div className="text-left">
                  <div className="text-xs font-semibold text-slate-200 truncate max-w-[170px]">
                    {user.email}
                  </div>
                  <div className="flex items-center gap-2 text-[11px] mt-0.5">
                    <span className="text-slate-400 hidden sm:inline">{getRoleLabel(user.role)}</span>
                    <span className="text-slate-600 hidden sm:inline">|</span>
                    <span className="text-[#00e5ff] font-mono font-bold flex items-center gap-1">
                      <Award className="w-3 h-3 text-[#00e5ff]" />
                      <span>{user.total_credits} MCC</span>
                    </span>
                  </div>
                </div>

                <button
                  onClick={onLogoutClick}
                  title="خروج"
                  className="p-2 text-slate-400 hover:text-rose-400 hover:bg-[#0b1e36] rounded-xl border border-transparent hover:border-[#112d4e] transition-all"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <button
                onClick={onLoginClick}
                className="flex items-center space-x-2 space-x-reverse px-4 py-2 rounded-xl bg-gradient-to-r from-[#00e5ff] via-[#0284c7] to-[#0369a1] hover:from-[#38bdf8] hover:to-[#0284c7] text-white font-bold text-xs transition-all shadow-md shadow-[#00e5ff]/20 border border-[#00e5ff]/30"
              >
                <LogIn className="w-4 h-4" />
                <span>ورود / ثبت‌نام</span>
              </button>
            )}

            {/* Mobile Hamburger Toggle */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden p-2 text-slate-300 hover:text-white hover:bg-[#0b1e36] rounded-xl border border-[#112d4e]"
              aria-label="منوی موبایل"
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>
      </div>

      {/* Responsive Mobile Navigation Drawer */}
      {mobileMenuOpen && (
        <div className="md:hidden border-t border-[#112d4e] bg-[#071527] px-4 pt-4 pb-6 space-y-3">
          <div className="space-y-1">
            {navItems
              .filter((item) => item.visible)
              .map((item) => {
                const Icon = item.icon;
                const isActive = activeTab === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => handleSelectTab(item.id)}
                    className={`w-full flex items-center justify-between px-4 py-3 rounded-xl text-xs font-medium transition-all ${
                      isActive
                        ? 'bg-[#0b1e36] text-[#00e5ff] border border-[#00e5ff]/40 font-bold'
                        : 'text-slate-300 hover:text-white hover:bg-[#0b1e36]/50'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <Icon className={`w-4 h-4 ${isActive ? 'text-[#00e5ff]' : 'text-slate-400'}`} />
                      <span>{item.label}</span>
                    </div>
                    {isActive && <span className="w-1.5 h-1.5 rounded-full bg-[#00e5ff]" />}
                  </button>
                );
              })}
          </div>

          <div className="pt-2 border-t border-[#112d4e]/60">
            <a
              href="/whitepaper.pdf"
              download="MAHOUNN-Whitepaper.pdf"
              target="_blank"
              rel="noopener noreferrer"
              className="w-full flex items-center justify-between px-4 py-3 rounded-xl text-xs font-bold bg-[#0b1e36] text-[#00e5ff] border border-[#00e5ff]/30 shadow-sm hover:bg-[#0f2d52] transition-colors"
            >
              <div className="flex items-center gap-2.5">
                <Download className="w-4 h-4 text-[#00e5ff]" />
                <span>دانلود وایت‌پیپر پلتفرم (PDF)</span>
              </div>
              <span className="font-mono text-[10px] text-slate-400">۵۴۱ کیلوبایت</span>
            </a>
          </div>

          {!user && (
            <div className="pt-2">
              <button
                onClick={() => {
                  setMobileMenuOpen(false);
                  onLoginClick();
                }}
                className="w-full flex items-center justify-center gap-2 py-3 rounded-xl bg-gradient-to-r from-[#00e5ff] via-[#0284c7] to-[#0369a1] text-white font-bold text-xs shadow-md border border-[#00e5ff]/30"
              >
                <LogIn className="w-4 h-4" />
                <span>ورود به حساب یا ثبت‌نام</span>
              </button>
            </div>
          )}
        </div>
      )}
    </header>
  );
};
