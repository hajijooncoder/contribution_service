import React from 'react';
import { LayoutDashboard, BookOpen, History, CheckSquare, Award, LogIn, LogOut, ShieldCheck, Shield } from 'lucide-react';
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
  return (
    <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur-md sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Identity */}
          <div className="flex items-center space-x-3 space-x-reverse">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-amber-500 to-amber-600 flex items-center justify-center shadow-lg shadow-amber-500/20">
              <ShieldCheck className="w-6 h-6 text-slate-950 stroke-[2.5]" />
            </div>
            <div>
              <span className="text-lg font-bold tracking-tight bg-gradient-to-r from-white via-slate-200 to-amber-400 bg-clip-text text-transparent">
                MAHOUNN
              </span>
              <span className="text-xs text-amber-500/90 font-mono block">
                Legal Contribution Platform
              </span>
            </div>
          </div>

          {/* Navigation Tabs */}
          <nav className="flex items-center space-x-1 space-x-reverse">
            <button
              onClick={() => setActiveTab('dashboard')}
              className={`flex items-center space-x-2 space-x-reverse px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                activeTab === 'dashboard'
                  ? 'bg-amber-500 text-slate-950 font-semibold shadow-md shadow-amber-500/20'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800'
              }`}
            >
              <LayoutDashboard className="w-4 h-4" />
              <span>داشبورد</span>
            </button>

            <button
              onClick={() => setActiveTab('submit')}
              className={`flex items-center space-x-2 space-x-reverse px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                activeTab === 'submit'
                  ? 'bg-amber-500 text-slate-950 font-semibold shadow-md shadow-amber-500/20'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800'
              }`}
            >
              <BookOpen className="w-4 h-4" />
              <span>ارسال مشارکت</span>
            </button>

            <button
              onClick={() => setActiveTab('history')}
              className={`flex items-center space-x-2 space-x-reverse px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                activeTab === 'history'
                  ? 'bg-amber-500 text-slate-950 font-semibold shadow-md shadow-amber-500/20'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800'
              }`}
            >
              <History className="w-4 h-4" />
              <span>مشارکت‌های من</span>
            </button>

            {(user?.role === 'reviewer' || user?.role === 'admin' || user?.role === 'expert') && (
              <button
                onClick={() => setActiveTab('reviewer')}
                className={`flex items-center space-x-2 space-x-reverse px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  activeTab === 'reviewer'
                    ? 'bg-amber-500 text-slate-950 font-semibold shadow-md shadow-amber-500/20'
                    : 'text-slate-300 hover:text-white hover:bg-slate-800'
                }`}
              >
                <CheckSquare className="w-4 h-4" />
                <span>میزکار داوری</span>
              </button>
            )}

            {user?.role === 'admin' && (
              <button
                onClick={() => setActiveTab('admin')}
                className={`flex items-center space-x-2 space-x-reverse px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  activeTab === 'admin'
                    ? 'bg-amber-500 text-slate-950 font-semibold shadow-md shadow-amber-500/20'
                    : 'text-slate-300 hover:text-white hover:bg-slate-800'
                }`}
              >
                <Shield className="w-4 h-4" />
                <span>مدیریت سیستم</span>
              </button>
            )}
          </nav>

          {/* User Profile / Login */}
          <div className="flex items-center space-x-4 space-x-reverse">
            {user ? (
              <div className="flex items-center space-x-3 space-x-reverse">
                <div className="text-left">
                  <div className="text-xs font-medium text-slate-200">{user.email}</div>
                  <div className="text-[11px] text-amber-400 flex items-center gap-1">
                    <Award className="w-3 h-3" />
                    <span>{user.total_credits} MCC</span>
                  </div>
                </div>
                <button
                  onClick={onLogoutClick}
                  title="خروج"
                  className="p-2 text-slate-400 hover:text-rose-400 hover:bg-slate-800 rounded-lg transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <button
                onClick={onLoginClick}
                className="flex items-center space-x-2 space-x-reverse px-3.5 py-1.5 rounded-lg border border-slate-700 bg-slate-800 hover:bg-slate-700 text-sm font-medium text-slate-200 transition-colors"
              >
                <LogIn className="w-4 h-4 text-amber-400" />
                <span>ورود / ثبت‌نام</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};
