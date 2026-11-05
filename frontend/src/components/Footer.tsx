import React from 'react';
import { Shield, Lock, FileCheck, Scale, CheckCircle2, ExternalLink, Download } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="border-t border-[#112d4e]/80 bg-[#030712]/80 backdrop-blur-md text-xs text-slate-400 font-sans selection:bg-[#00e5ff] selection:text-white relative before:absolute before:top-0 before:left-0 before:right-0 before:h-[1px] before:bg-gradient-to-r before:from-transparent before:via-[#00e5ff]/35 before:to-transparent before:pointer-events-none">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Top 3 Core Pillars */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-10 pb-10 border-b border-[#112d4e]/50">
          <div className="space-y-3">
            <div className="flex items-center space-x-2.5 space-x-reverse text-slate-100 font-bold text-sm">
              <div className="w-7 h-7 rounded-lg bg-[#0b1e36] border border-[#00e5ff]/40 flex items-center justify-center text-[#00e5ff]">
                <Scale className="w-4 h-4" />
              </div>
              <span>پلتفرم مستقل مشارکت MAHOUNN</span>
            </div>
            <p className="text-slate-400 leading-relaxed text-xs">
              سامانه آزاد دریافت، بهینه‌سازی و داوری متون و قوانین رسمی ایران با هدف یکپارچه‌سازی و
              غنی‌سازی پیکره دانش حقوقی کشور با مشارکت جامعه علمی و قضایی.
            </p>
          </div>

          <div className="space-y-3">
            <div className="flex items-center space-x-2.5 space-x-reverse text-slate-100 font-bold text-sm">
              <div className="w-7 h-7 rounded-lg bg-[#0b1e36] border border-sky-500/40 flex items-center justify-center text-sky-400">
                <Lock className="w-4 h-4" />
              </div>
              <span>ایزولاسیون و حفاظت فیزیکی (Air-Gap)</span>
            </div>
            <p className="text-slate-400 leading-relaxed text-xs">
              این پلتفرم یک زیرساخت ایزوله Staging بوده و فاقد هرگونه اتصال شبکه مستقیم به موتورهای
              استدلال یا پایگاه‌های گراف محرمانه است. کلیه اسناد پیش از انتقال ممیزی می‌شوند.
            </p>
          </div>

          <div className="space-y-3">
            <div className="flex items-center space-x-2.5 space-x-reverse text-slate-100 font-bold text-sm">
              <div className="w-7 h-7 rounded-lg bg-[#0b1e36] border border-emerald-500/40 flex items-center justify-center text-emerald-400">
                <FileCheck className="w-4 h-4" />
              </div>
              <span>دفتر کل ضد‌تخریب (HMAC Audit Ledger)</span>
            </div>
            <p className="text-slate-400 leading-relaxed text-xs">
              تمام مشارکت‌ها و آرای داوران در دفتر کل ممیزی تغییرناپذیر ثبت شده و اصالت تاریخی و زنجیره
              استنادی آن‌ها به صورت رمزنگاری‌شده تضمین می‌گردد.
            </p>
          </div>
        </div>

        {/* Bottom Row */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 text-slate-400 text-xs">
          <div className="flex items-center gap-3">
            <span className="font-bold text-white font-mono text-sm tracking-wide">
              MAHOUN<span className="text-[#00e5ff]">N</span>
            </span>
            <span className="text-slate-600">·</span>
            <span>© {new Date().getFullYear()} پلتفرم مشارکت حقوقی MAHOUNN. تمامی حقوق محفوظ است.</span>
          </div>

          <div className="flex items-center gap-4 text-xs font-medium">
            <a
              href="/whitepaper.pdf"
              download="MAHOUNN-Whitepaper.pdf"
              target="_blank"
              rel="noopener noreferrer"
              className="text-[#00e5ff] hover:text-[#38bdf8] flex items-center gap-1.5 transition-colors font-semibold py-1 px-2.5 rounded-lg bg-[#00e5ff]/10 hover:bg-[#00e5ff]/20 border border-[#00e5ff]/30"
              title="دانلود سند وایت‌پیپر پلتفرم MAHOUNN"
            >
              <Download className="w-3.5 h-3.5" />
              <span>دانلود وایت‌پیپر (PDF)</span>
            </a>
            <span className="text-slate-600">|</span>
            <span className="text-[#00e5ff] flex items-center gap-1.5 font-mono">
              <Shield className="w-3.5 h-3.5" />
              <span>TRUSTED LEGAL CORPUS</span>
            </span>
            <span className="text-slate-600">|</span>
            <span className="text-slate-400 hover:text-slate-200 transition-colors">
              اعتماد · شفافیت · مشارکت · استناد
            </span>
          </div>
        </div>
      </div>
    </footer>
  );
};
