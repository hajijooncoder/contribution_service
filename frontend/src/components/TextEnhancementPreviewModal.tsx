import React from 'react';
import { EnhancedTextPreview, DuplicateCheckResult } from '../types';
import { CheckCircle2, AlertTriangle, Sparkles, X, FileText, ArrowLeft } from 'lucide-react';

interface Props {
  preview: EnhancedTextPreview | null;
  duplicateCheck: DuplicateCheckResult | null;
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  isSubmitting: boolean;
}

export const TextEnhancementPreviewModal: React.FC<Props> = ({
  preview,
  duplicateCheck,
  isOpen,
  onClose,
  onConfirm,
  isSubmitting,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-3xl w-full p-6 shadow-2xl relative text-right">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute left-6 top-6 text-slate-400 hover:text-white transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center space-x-3 space-x-reverse mb-6">
          <div className="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white">پیش‌نمایش ارتقای کیفیت و تحلیل متن</h3>
            <p className="text-xs text-slate-400">
              موتور هوشمند متن ارسالی شما را اعتبارسنجی و بهینه‌سازی کرده است.
            </p>
          </div>
        </div>

        {/* Duplicate Warning if any */}
        {duplicateCheck && duplicateCheck.is_duplicate && (
          <div className="mb-6 p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-200">
            <div className="flex items-start space-x-3 space-x-reverse">
              <AlertTriangle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
              <div>
                <h4 className="font-semibold text-sm mb-1">هشدار تشابه یا تکرار سند!</h4>
                <p className="text-xs leading-relaxed opacity-90">{duplicateCheck.message}</p>
                <div className="mt-2 text-xs font-mono text-amber-300">
                  درصد شباهت: {(duplicateCheck.similarity * 100).toFixed(1)}% | سطح:{' '}
                  {duplicateCheck.level}
                </div>
              </div>
            </div>
          </div>
        )}

        {preview && (
          <div className="space-y-6">
            {/* Metrics */}
            <div className="grid grid-cols-3 gap-4">
              <div className="p-3.5 rounded-xl bg-slate-800/60 border border-slate-800 text-center">
                <div className="text-xs text-slate-400 mb-1">امتیاز کیفیت متن</div>
                <div className="text-xl font-bold text-amber-400">
                  {preview.quality_score.toFixed(0)} / ۱۰۰
                </div>
              </div>
              <div className="p-3.5 rounded-xl bg-slate-800/60 border border-slate-800 text-center">
                <div className="text-xs text-slate-400 mb-1">اصلاحات نگارشی</div>
                <div className="text-xl font-bold text-emerald-400">
                  {preview.changes_count} مورد
                </div>
              </div>
              <div className="p-3.5 rounded-xl bg-slate-800/60 border border-slate-800 text-center">
                <div className="text-xs text-slate-400 mb-1">تعداد مواد شناسایی‌شده</div>
                <div className="text-xl font-bold text-sky-400">
                  {preview.metadata.article_count} ماده
                </div>
              </div>
            </div>

            {/* Extracted Metadata Pills */}
            <div className="p-4 rounded-xl bg-slate-800/40 border border-slate-800">
              <div className="text-xs font-semibold text-slate-300 mb-2 flex items-center gap-1.5">
                <FileText className="w-3.5 h-3.5 text-amber-400" />
                <span>موجودیت‌ها و اطلاعات استخراج‌شده:</span>
              </div>
              <div className="flex flex-wrap gap-2 text-xs">
                {preview.metadata.legal_entities.map((ent, idx) => (
                  <span
                    key={idx}
                    className="px-2.5 py-1 rounded-md bg-slate-800 text-slate-300 border border-slate-700 font-mono"
                  >
                    {ent}
                  </span>
                ))}
                {preview.metadata.references.map((ref, idx) => (
                  <span
                    key={`ref-${idx}`}
                    className="px-2.5 py-1 rounded-md bg-amber-500/10 text-amber-300 border border-amber-500/20"
                  >
                    ارجاع: {ref}
                  </span>
                ))}
              </div>
            </div>

            {/* Sample Changes */}
            {preview.changes.length > 0 && (
              <div>
                <div className="text-xs font-semibold text-slate-300 mb-2">
                  نمونه اصلاحات استانداردسازی اعمال‌شده:
                </div>
                <div className="max-h-40 overflow-y-auto space-y-2 pr-1 font-mono text-xs">
                  {preview.changes.slice(0, 5).map((ch, idx) => (
                    <div
                      key={idx}
                      className="p-2.5 rounded-lg bg-slate-800/60 border border-slate-800/80 flex items-center justify-between"
                    >
                      <div className="flex items-center gap-2">
                        <span className="text-rose-400 line-through">{ch.original}</span>
                        <ArrowLeft className="w-3 h-3 text-slate-500" />
                        <span className="text-emerald-400">{ch.corrected}</span>
                      </div>
                      <span className="text-[11px] text-slate-400">{ch.reason}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Actions */}
        <div className="mt-8 flex items-center justify-end space-x-3 space-x-reverse">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl text-sm font-medium text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            انصراف و ویرایش
          </button>
          <button
            onClick={onConfirm}
            disabled={isSubmitting}
            className="flex items-center space-x-2 space-x-reverse px-5 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-semibold text-sm transition-all shadow-lg shadow-amber-500/20 disabled:opacity-50"
          >
            <CheckCircle2 className="w-4 h-4" />
            <span>{isSubmitting ? 'در حال ثبت نهایی...' : 'تأیید و ارسال مشارکت'}</span>
          </button>
        </div>
      </div>
    </div>
  );
};
