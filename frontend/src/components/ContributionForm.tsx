import React, { useState, useEffect } from 'react';
import {
  DocumentType,
  EnhancedSubmissionRequest,
  EnhancedSubmissionResponse,
  UrlValidationResponse,
} from '../types';
import { apiClient } from '../api/client';
import { TextEnhancementPreviewModal } from './TextEnhancementPreviewModal';
import {
  FileText,
  Globe,
  Building,
  Sparkles,
  AlertCircle,
  CheckCircle,
  ShieldCheck,
  Loader2,
  Lock,
} from 'lucide-react';

interface Props {
  onSuccess: () => void;
}

export const ContributionForm: React.FC<Props> = ({ onSuccess }) => {
  const [documentType, setDocumentType] = useState<DocumentType>('law');
  const [sourceTitle, setSourceTitle] = useState('');
  const [legalDocumentName, setLegalDocumentName] = useState('');
  const [issuingAuthority, setIssuingAuthority] = useState('');
  const [sourceUrl, setSourceUrl] = useState('');
  const [rawLegalText, setRawLegalText] = useState('');
  const [contributorNotes, setContributorNotes] = useState('');
  const [skipEnhancement, setSkipEnhancement] = useState(false);

  // URL Real-time validation state
  const [isValidatingUrl, setIsValidatingUrl] = useState(false);
  const [urlValidation, setUrlValidation] = useState<UrlValidationResponse | null>(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Preview modal state
  const [previewResponse, setPreviewResponse] = useState<EnhancedSubmissionResponse | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isSubmittingFinal, setIsSubmittingFinal] = useState(false);

  // Debounced Real-time URL Validation (Deliverable 2)
  useEffect(() => {
    const trimmed = sourceUrl.trim();
    if (trimmed.length < 5) {
      setUrlValidation(null);
      setIsValidatingUrl(false);
      return;
    }

    setIsValidatingUrl(true);
    const timer = setTimeout(async () => {
      try {
        const res = await apiClient.validateUrl(trimmed);
        setUrlValidation(res);
        if (res.valid && res.authority && !issuingAuthority) {
          setIssuingAuthority(res.authority);
        }
      } catch {
        setUrlValidation({
          valid: false,
          error: 'خطا در ارتباط با سرویس اعتبارسنجی منبع.',
        });
      } finally {
        setIsValidatingUrl(false);
      }
    }, 450);

    return () => clearTimeout(timer);
  }, [sourceUrl]);

  const handleSubmit = async (e: React.FormEvent, force = false) => {
    e.preventDefault();
    setError(null);
    setSuccessMessage(null);

    if (rawLegalText.trim().length < 20) {
      setError('متن سند حقوقی باید حداقل ۲۰ کاراکتر باشد.');
      return;
    }

    setLoading(true);

    const payload: EnhancedSubmissionRequest = {
      source_title: sourceTitle || legalDocumentName,
      legal_document_name: legalDocumentName,
      raw_legal_text: rawLegalText,
      source_url: sourceUrl,
      document_type: documentType,
      issuing_authority: issuingAuthority,
      contributor_notes: contributorNotes || undefined,
      skip_enhancement: skipEnhancement,
      force_submit: force,
    };

    try {
      const res = await apiClient.submitEnhanced(payload);
      if (res.status === 'preview' || res.status === 'duplicate_detected') {
        setPreviewResponse(res);
        setIsModalOpen(true);
      } else if (res.status === 'submitted') {
        setSuccessMessage('مشارکت شما با موفقیت ثبت شد و وارد صف داوری همتا گردید.');
        resetForm();
        onSuccess();
      }
    } catch (err: any) {
      setError(err.message || 'خطا در ثبت مشارکت.');
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmFinal = async () => {
    setIsSubmittingFinal(true);
    setError(null);

    const payload: EnhancedSubmissionRequest = {
      source_title: sourceTitle || legalDocumentName,
      legal_document_name: legalDocumentName,
      raw_legal_text: rawLegalText,
      source_url: sourceUrl,
      document_type: documentType,
      issuing_authority: issuingAuthority,
      contributor_notes: contributorNotes || undefined,
      skip_enhancement: skipEnhancement,
      force_submit: true, // User verified
    };

    try {
      await apiClient.submitEnhanced(payload);
      setSuccessMessage('مشارکت شما با موفقیت ثبت شد و وارد چرخه داوری گردید.');
      setIsModalOpen(false);
      resetForm();
      onSuccess();
    } catch (err: any) {
      setError(err.message || 'خطا در ثبت نهایی.');
    } finally {
      setIsSubmittingFinal(false);
    }
  };

  const resetForm = () => {
    setSourceTitle('');
    setLegalDocumentName('');
    setIssuingAuthority('');
    setSourceUrl('');
    setRawLegalText('');
    setContributorNotes('');
  };

  return (
    <div className="max-w-4xl mx-auto py-8 px-4 sm:px-6">
      {/* Intro Hero */}
      <div className="text-center mb-10">
        <h1 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight mb-4">
          به غنی‌سازی پیکره دانش حقوقی ایران کمک کنید
        </h1>
        <p className="text-slate-400 text-sm sm:text-base max-w-2xl mx-auto leading-relaxed">
          منبع رسمی را ارائه کنید. متن حقوقی را ثبت کنید. با تایید داوران امتیاز MCC و رتبه پژوهشی
          دریافت کنید.
        </p>
      </div>

      {error && (
        <div className="mb-6 p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-sm flex items-center space-x-3 space-x-reverse">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {successMessage && (
        <div className="mb-6 p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-sm flex items-center space-x-3 space-x-reverse">
          <CheckCircle className="w-5 h-5 flex-shrink-0" />
          <span>{successMessage}</span>
        </div>
      )}

      {/* Main Form */}
      <form
        onSubmit={(e) => handleSubmit(e, false)}
        className="bg-slate-900 border border-slate-800 rounded-2xl p-6 sm:p-8 shadow-xl space-y-6"
      >
        {/* Document Type & Authority */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-2">نوع سند حقوقی</label>
            <select
              value={documentType}
              onChange={(e) => setDocumentType(e.target.value as DocumentType)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-amber-500 focus:ring-1 focus:ring-amber-500"
            >
              <option value="law">قانون مصوب مجلس</option>
              <option value="regulation">آیین‌نامه / تصویب‌نامه هیئت وزیران</option>
              <option value="precedent">رأی وحدت رویه دیوان عالی کشور</option>
              <option value="circular">بخشنامه / دستورالعمل اجرایی</option>
              <option value="court_order">دادنامه / رأی دادگاه</option>
              <option value="statute">اساسنامه</option>
              <option value="other">سایر اسناد معتبر حقوقی</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-2">
              مرجع صادرکننده / تصویب‌کننده
            </label>
            <div className="relative">
              <input
                type="text"
                required
                value={issuingAuthority}
                onChange={(e) => setIssuingAuthority(e.target.value)}
                placeholder="مثال: مجلس شورای اسلامی، دیوان عالی کشور"
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 pr-10 text-sm text-slate-200 focus:outline-none focus:border-amber-500 focus:ring-1 focus:ring-amber-500"
              />
              <Building className="w-4 h-4 text-slate-500 absolute right-3.5 top-3" />
            </div>
          </div>
        </div>

        {/* Title */}
        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-2">عنوان رسمی سند</label>
          <div className="relative">
            <input
              type="text"
              required
              value={legalDocumentName}
              onChange={(e) => setLegalDocumentName(e.target.value)}
              placeholder="مثال: قانون شوراهای حل اختلاف، رأی وحدت رویه شماره ۸۳۵"
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 pr-10 text-sm text-slate-200 focus:outline-none focus:border-amber-500 focus:ring-1 focus:ring-amber-500"
            />
            <FileText className="w-4 h-4 text-slate-500 absolute right-3.5 top-3" />
          </div>
        </div>

        {/* Source URL with Whitelist Hint & Real-time Validation (Deliverable 2) */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="text-xs font-semibold text-slate-300">لینک منبع رسمی (دولت/قوه قضاییه)</label>
            <span className="text-[11px] text-amber-500/90 font-mono">
              دامنه معتبر: rrk.ir, dotic.ir, rc.majlis.ir, qavanin.ir, ...
            </span>
          </div>
          <div className="relative">
            <input
              type="url"
              required
              value={sourceUrl}
              onChange={(e) => setSourceUrl(e.target.value)}
              placeholder="https://rrk.ir/laws/show/... یا https://rc.majlis.ir/fa/law/..."
              className={`w-full bg-slate-950 border rounded-xl px-4 py-2.5 pr-10 text-sm text-slate-200 focus:outline-none focus:ring-1 ${
                urlValidation?.valid
                  ? 'border-emerald-500/70 focus:border-emerald-500 focus:ring-emerald-500'
                  : urlValidation && !urlValidation.valid
                  ? 'border-rose-500/70 focus:border-rose-500 focus:ring-rose-500'
                  : 'border-slate-800 focus:border-amber-500 focus:ring-amber-500'
              }`}
            />
            <Globe className="w-4 h-4 text-slate-500 absolute right-3.5 top-3" />
          </div>

          {/* Real-time Validation Feedback */}
          {isValidatingUrl && (
            <div className="mt-2 flex items-center gap-2 text-xs text-amber-400/90">
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
              <span>در حال اعتبارسنجی دامنه مرجع رسمی...</span>
            </div>
          )}

          {!isValidatingUrl && urlValidation?.valid && (
            <div className="mt-2 flex items-center gap-2 p-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs font-medium">
              <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
              <span>
                مرجع رسمی تایید شد: <strong>{urlValidation.authority}</strong>
              </span>
            </div>
          )}

          {!isValidatingUrl && urlValidation && !urlValidation.valid && (
            <div className="mt-2 flex items-center gap-2 p-2.5 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs font-medium">
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
              <span>{urlValidation.error}</span>
            </div>
          )}
        </div>

        {/* Legal Text */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="text-xs font-semibold text-slate-300">متن کامل ماده یا سند حقوقی</label>
            <span
              className={`text-xs font-mono ${
                rawLegalText.length > 10000 || (rawLegalText.length > 0 && rawLegalText.length < 20)
                  ? 'text-rose-400 font-bold'
                  : 'text-slate-400'
              }`}
            >
              {rawLegalText.length.toLocaleString('fa-IR')} / ۱۰٬۰۰۰ نویسه
            </span>
          </div>
          <textarea
            required
            rows={8}
            value={rawLegalText}
            onChange={(e) => setRawLegalText(e.target.value)}
            placeholder="متن کامل ماده، تبصره‌ها و مفاد قانونی را در این قسمت وارد کنید..."
            className="w-full bg-slate-950 border border-slate-800 rounded-xl p-4 text-sm text-slate-200 focus:outline-none focus:border-amber-500 focus:ring-1 focus:ring-amber-500 font-sans leading-relaxed"
          />
          {rawLegalText.length > 0 && rawLegalText.length < 20 && (
            <p className="mt-1 text-xs text-rose-400">متن حقوقی باید حداقل ۲۰ نویسه داشته باشد.</p>
          )}
          {rawLegalText.length > 10000 && (
            <p className="mt-1 text-xs text-rose-400">متن حقوقی نباید بیشتر از ۱۰٬۰۰۰ نویسه باشد.</p>
          )}
        </div>

        {/* Air-gap Policy Callout (from Lovable) */}
        <div className="p-3.5 rounded-xl border border-slate-800 bg-slate-950/70 flex items-start gap-3 border-r-2 border-r-amber-500">
          <Lock className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
          <div className="text-xs leading-relaxed text-slate-300">
            <span className="font-bold text-amber-400">مشارکت مطلقاً به معنای دسترسی مستقیم به پایگاه داده نیست:</span>{' '}
            تمام محتوای ارسالی ابتدا قرنطینه و توسط داوران همتا ارزیابی می‌شود و مستقیماً وارد گراف دانش مرجع نخواهد شد.
          </div>
        </div>

        {/* Options */}
        <div className="flex items-center space-x-3 space-x-reverse pt-2">
          <input
            type="checkbox"
            id="skipEnhance"
            checked={skipEnhancement}
            onChange={(e) => setSkipEnhancement(e.target.checked)}
            className="rounded border-slate-700 bg-slate-950 text-amber-500 focus:ring-amber-500"
          />
          <label htmlFor="skipEnhance" className="text-xs text-slate-400">
            ارسال خام متن بدون پیش‌پردازش هوشمند (صرفاً برای بازبینی انسانی)
          </label>
        </div>

        {/* Submit Button */}
        <div className="pt-4 border-t border-slate-800 flex items-center justify-between">
          <div className="text-xs text-slate-500">
            تمام مشارکت‌ها قبل از انتشار توسط داوران حقوقی اعتبارسنجی می‌شوند.
          </div>
          <button
            type="submit"
            disabled={loading}
            className="flex items-center space-x-2 space-x-reverse px-6 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-sm transition-all shadow-lg shadow-amber-500/20 disabled:opacity-50"
          >
            <Sparkles className="w-4 h-4" />
            <span>{loading ? 'در حال تحلیل...' : 'پیش‌نمایش و ثبت مشارکت'}</span>
          </button>
        </div>
      </form>

      {/* Preview Modal */}
      <TextEnhancementPreviewModal
        isOpen={isModalOpen}
        preview={previewResponse?.enhanced_preview || null}
        duplicateCheck={previewResponse?.duplicate_check || null}
        onClose={() => setIsModalOpen(false)}
        onConfirm={handleConfirmFinal}
        isSubmitting={isSubmittingFinal}
      />
    </div>
  );
};
