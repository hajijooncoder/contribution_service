# راهنمای اجرای تست‌های سخت‌گیرانه

## تست‌های جدید اضافه‌شده

### `test_enhanced_submission_hardcore.py`
شامل ۶ بخش:
1. **Enhanced Submission Flow** — چرخه preview → force_submit → DB record
2. **Duplicate Detection** — exact / near / force bypass
3. **IDOR Protection** — جداسازی دسترسی contributor‌ها
4. **Export Gateway** — token enforcement، transit SHA-256، JSONL format
5. **Rate Limiting** — bucket saturation و reset
6. **Frontend–Backend Contract** — ۷ مغایرت شناخته‌شده در `client.ts` و `types/index.ts`

### `test_text_enhancement_hardcore_v2.py`
شامل ۴ بخش:
1. **LegalTextEnhancer** — article count، fingerprint، Arabic normalization، quality score
2. **Text Preservation** — sanitize، HTML stripping، max_length
3. **CryptographicAuditLedger** — chain linkage، tamper detection، HMAC key custody
4. **TextFingerprinter** — SimHash، Hamming distance، near-duplicate sensitivity

## دستورات اجرا

```bash
cd /home/haji/Desktop/contribution_service/backend
source ../venv/bin/activate  # یا venv محلی

# اجرای فقط تست‌های جدید
pytest tests/test_enhanced_submission_hardcore.py tests/test_text_enhancement_hardcore_v2.py -v

# اجرای همه تست‌ها
pytest tests/ -v

# اجرای یک بخش خاص
pytest tests/test_enhanced_submission_hardcore.py::TestExportGatewayHardcore -v

# اجرای تست‌های contract mismatch (همه باید FAIL کنند تا bug ثابت شود)
pytest tests/test_enhanced_submission_hardcore.py::TestFrontendBackendContractMismatch -v
```

## تست‌های Contract Mismatch — انتظار FAIL دارند

بخش `TestFrontendBackendContractMismatch` **عمداً fail می‌کند** چون:

| متد | آدرس در `client.ts` | آدرس واقعی backend |
|-----|---------------------|---------------------|
| `submitEnhanced()` | `/contributions/submit/enhanced` | `/contribution/submit/enhanced` |
| `getReviewQueue()` | `/reviews/queue` | `/contribution/review/pending` |
| `submitReview()` | `/reviews/${id}` | `/contribution/review/decision` |
| `getMyHistory()` | `/contributions/history` | `/contribution/history` |
| `uploadDocument()` | `/contributions/upload` | `/contribution/upload` |
| `UserProfile.mcc_credits` | `mcc_credits` | `total_credits` |
| `SubmissionStatus` | `under_review`, `quarantined` | `under_legal_review`, `needs_correction` |

برای رفع این مغایرت‌ها باید `frontend/src/api/client.ts` و `frontend/src/types/index.ts` اصلاح شوند.
