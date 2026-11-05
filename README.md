# MAHOUNN Legal Contribution Platform
### سامانه آزاد مشارکت و جمع‌سپاری گراف دانش حقوقی ایران

[![Contribution Platform CI](https://github.com/hajijooncoder/contribution_service/actions/workflows/ci.yml/badge.svg)](https://github.com/hajijooncoder/contribution_service/actions/workflows/ci.yml)
[![Security Audit](https://github.com/hajijooncoder/contribution_service/actions/workflows/security.yml/badge.svg)](https://github.com/hajijooncoder/contribution_service/actions/workflows/security.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-amber.svg)](LICENSE)

---

## ۱. درباره پلتفرم
پلتفرم مشارکت آزاد **MAHOUNN**، سامانه‌ای متن‌باز و مستقل برای جمع‌آوری، استانداردسازی، اعتبارسنجی و داوری همتای (Peer Review) اسناد، قوانین، آیین‌نامه‌ها و آرای قضایی کشور است. 

این سامانه به عنوان یک ماهواره عمومی (Public Satellite) توسعه یافته و به منظور تضمین حاکمیت داده، حفاظت از فناوری انحصاری و امنیت دارایی‌های دانشی، **کاملاً مستقل از هسته استدلال و گراف دانش اختصاصی MAHOUN** عمل می‌کند.

---

## ۲. ویژگی‌های کلیدی
- **داوری همتا با حدنصاب اجماع (Consensus Quorum FSM):** انتقال خودکار وضعیت اسناد بر اساس قوانین قطعی و الزامات اعتبارسنجی مستقل (۲ داور برای قوانین با ریسک بالا).
- **دفتر کل ممیزی تغییرناپذیر (HMAC-SHA256 Audit Ledger):** زنجیره پیوسته ثبت رویدادها با قابلیت تشخیص هرگونه دستکاری یا حذف تاریخی.
- **بهینه‌سازی و نرمال‌سازی متون حقوقی:** رفع ناهماهنگی‌های فونت و اعراب، استخراج خودکار مواد، تبصره‌ها، مراجع تصویب و موجودیت‌های حقوقی.
- **تشخیص هوشمند تکرار و سرقت محتوا (SimHash):** مقایسه ساختاری و محتوایی متون جهت جلوگیری از ورود داده‌های تکراری به پیکره داده.
- **قرنطینه چندلایه‌ای اسناد:** جداسازی فایل‌های آپلودی، بررسی امضای باینری (MIME) و ممانعت از اجرای حملات تزریق یا Traversal.
- **دروازه خروجی تحت کنترل مالک (Owner-Controlled PULL Gateway):** استخراج دسته‌ای داده‌های تأییدشده با توکن رمزنگاری‌شده جهت انتقال فیزیکی به کارخانه دانش (Air-Gapped Foundry).
- **رابط کاربری مدرن، زیبا و فارسی (RTL):** توسعه‌یافته با React 19، TypeScript، Vite و Tailwind CSS 4 بر اساس استانداردهای لاوبل.

---

## ۳. مستندات تفصیلی
- [راهنمای جامع کاربران و داوران (فارسی)](docs/USER_GUIDE_FA.md)
- [سند جامع امنیت و آزمون‌های متخاصم](docs/ADVERSARIAL_SECURITY_AND_RESILIENCE_SPEC.md)
- [راهنمای توسعه‌دهندگان و معماری سامانه](docs/DEVELOPER_GUIDE.md)
- [مرجع جامع API و وب‌سوکت](docs/API_REFERENCE.md)
- [راهنمای آزمون‌ها و اعتبارسنجی کیفیت](docs/TESTING_GUIDE.md)
- [سند معماری جامع](docs/ARCHITECTURE.md)
- [مرزهای امنیتی و ایزولاسیون](docs/SECURITY_BOUNDARIES.md)
- [جریان داده‌های حقوقی](docs/DATA_FLOW.md)
- [مشخصات اندپوینت‌ها و قراردادهای API](docs/API_CONTRACTS.md)
- [معماری خط لوله CI/CD](docs/CI_CD_ARCHITECTURE.md)
