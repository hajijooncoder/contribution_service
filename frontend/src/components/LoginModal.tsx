import React, { useState } from 'react';
import { apiClient } from '../api/client';
import { UserProfile } from '../types';
import { X, Lock, Mail, UserPlus, AlertCircle, Scale } from 'lucide-react';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (user: UserProfile) => void;
}

export const LoginModal: React.FC<Props> = ({ isOpen, onClose, onSuccess }) => {
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      if (isRegister) {
        // Register API
        const response = await fetch('/api/v1/auth/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password, full_name: fullName }),
        });
        if (!response.ok) {
          const err = await response.json();
          throw new Error(err.detail || 'ثبت‌نام ناموفق بود.');
        }
      }

      // Login
      const formData = new URLSearchParams();
      formData.append('username', email);
      formData.append('password', password);

      await apiClient.login(formData);
      const profile = await apiClient.getMe();
      onSuccess(profile);
      onClose();
    } catch (err: any) {
      setError(err.message || 'خطا در احراز هویت.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-[#030712]/85 backdrop-blur-sm flex items-center justify-center p-4 font-sans animate-fade-in">
      <div className="bg-[#071527] border border-[#112d4e] border-t-[#00e5ff]/35 rounded-2xl max-w-md w-full p-6 sm:p-8 shadow-2xl relative text-right">
        <button
          onClick={onClose}
          className="absolute left-6 top-6 text-slate-400 hover:text-white transition-colors p-1 rounded-lg hover:bg-[#0b1e36]"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="text-center mb-6">
          <div className="w-12 h-12 rounded-2xl bg-[#0b1e36] border border-[#00e5ff]/40 text-[#00e5ff] flex items-center justify-center mx-auto mb-3 shadow-md">
            {isRegister ? <UserPlus className="w-6 h-6" /> : <Lock className="w-6 h-6" />}
          </div>
          <h3 className="text-xl font-bold text-white tracking-tight">
            {isRegister ? 'ثبت‌نام پژوهشگر جدید' : 'ورود به حساب کاربری'}
          </h3>
          <p className="text-xs text-slate-400 mt-1 leading-relaxed">
            {isRegister
              ? 'با ایجاد حساب از امتیازهای مشارکت و ثبت رسمی اعتبار بهره‌مند شوید'
              : 'جهت پیگیری سوابق و داوری متون وارد شوید'}
          </p>
        </div>

        {error && (
          <div className="mb-4 p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {isRegister && (
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                نام و نام خانوادگی
              </label>
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="مثال: علی محمدی"
                className="w-full bg-[#030712] border border-[#112d4e] rounded-xl px-4 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-[#00e5ff] transition-colors"
              />
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">پست الکترونیکی</label>
            <div className="relative">
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="contributor@example.com"
                className="w-full bg-[#030712] border border-[#112d4e] rounded-xl px-4 py-2.5 pr-10 text-sm text-slate-200 focus:outline-none focus:border-[#00e5ff] font-mono transition-colors"
              />
              <Mail className="w-4 h-4 text-slate-500 absolute right-3.5 top-3" />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">کلمه عبور</label>
            <div className="relative">
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full bg-[#030712] border border-[#112d4e] rounded-xl px-4 py-2.5 pr-10 text-sm text-slate-200 focus:outline-none focus:border-[#00e5ff] font-mono transition-colors"
              />
              <Lock className="w-4 h-4 text-slate-500 absolute right-3.5 top-3" />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 rounded-xl bg-gradient-to-r from-[#00e5ff] via-[#0284c7] to-[#0369a1] hover:from-[#38bdf8] hover:to-[#0284c7] text-white font-bold text-sm transition-all shadow-md shadow-[#00e5ff]/20 border border-[#00e5ff]/30 disabled:opacity-50 mt-2"
          >
            {loading ? 'در حال پردازش...' : isRegister ? 'ثبت‌نام و ورود' : 'ورود به سامانه'}
          </button>
        </form>

        <div className="mt-6 text-center text-xs text-slate-400 border-t border-[#112d4e] pt-4">
          {isRegister ? (
            <span>
              قبلاً ثبت‌نام کرده‌اید؟{' '}
              <button
                type="button"
                onClick={() => setIsRegister(false)}
                className="text-[#00e5ff] hover:underline font-semibold"
              >
                وارد شوید
              </button>
            </span>
          ) : (
            <span>
              حساب کاربری ندارید؟{' '}
              <button
                type="button"
                onClick={() => setIsRegister(true)}
                className="text-[#00e5ff] hover:underline font-semibold"
              >
                ایجاد حساب مشارکت‌کننده
              </button>
            </span>
          )}
        </div>
      </div>
    </div>
  );
};
