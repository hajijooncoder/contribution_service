import React from 'react';
import { Shield, Lock, FileCheck } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="border-t border-slate-800 bg-slate-950 py-10 text-xs text-slate-400">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-8">
          <div>
            <div className="flex items-center space-x-2 space-x-reverse text-slate-200 font-semibold mb-2">
              <Shield className="w-4 h-4 text-amber-500" />
              <span>پلتفرم مستقل مشارکت MAHOUNN</span>
            </div>
            <p className="text-slate-400 leading-relaxed">
              سامانه آزاد دریافت، بهینه‌سازی و داوری متون و قوانین رسمی ایران به منظور غنی‌سازی پیکره
              حقوقی کشور.
            </p>
          </div>

          <div>
            <div className="flex items-center space-x-2 space-x-reverse text-slate-200 font-semibold mb-2">
              <Lock className="w-4 h-4 text-amber-500" />
              <span>ایزولاسیون و حفاظت فیزیکی (Air-Gap)</span>
            </div>
            <p className="text-slate-400 leading-relaxed">
              این پلتفرم یک زیرساخت ایزوله Staging بوده و فاقد هرگونه اتصال شبکه مستقیم به موتورهای
              استدلال یا پایگاه‌های گراف محرمانه است.
            </p>
          </div>

          <div>
            <div className="flex items-center space-x-2 space-x-reverse text-slate-200 font-semibold mb-2">
              <FileCheck className="w-4 h-4 text-amber-500" />
              <span>دفتر کل ضد‌تخریب (HMAC Audit Ledger)</span>
            </div>
            <p className="text-slate-400 leading-relaxed">
              تمام مشارکت‌ها و آرای داوران در دفتر کل ممیزی تغییرناپذیر ثبت شده و اصالت تاریخی آن‌ها
              تضمین می‌گردد.
            </p>
          </div>
        </div>

        <div className="border-t border-slate-800/80 pt-6 flex flex-col sm:flex-row items-center justify-between gap-4 text-slate-500">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-slate-300 font-mono">Mahoun<span className="text-amber-400">N</span></span>
            <span>·</span>
            <span>© {new Date().getFullYear()} پلتفرم مشارکت حقوقی MAHOUNN</span>
          </div>
          <div className="flex items-center gap-2 text-xs font-medium text-amber-400/90">
            <Shield className="w-3.5 h-3.5 text-amber-400" />
            <span>اعتماد · شفافیت · مشارکت · تأیید · اثر</span>
          </div>
        </div>
      </div>
    </footer>
  );
};
