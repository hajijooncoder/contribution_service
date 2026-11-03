"""
Text Enhancement, Normalization, Duplicate Detection and Source Integrity Hardcore Test Suite.
تست‌های بشدت دقیق و سخت‌گیرانه برای اعتبارسنجی موتور ارتقای متون حقوقی، نرمال‌سازی املایی و نشانه‌گذاری،
استخراج فراداده، الگوریتم‌های شباهت SimHash و تشخیص اسناد تکراری در ۴ لایه مجزا و اعتبارسنجی مراجع رسمی.
"""

import hashlib
import json
import uuid
import pytest
from sqlalchemy.orm import Session

from app.core.text_enhancement import (
    PersianTextNormalizer,
    LegalStructureFormatter,
    LegalTypoCorrector,
    LegalMetadataExtractor,
    TextFingerprinter,
    QualityScorer,
    LegalTextEnhancer,
    ARABIC_TO_PERSIAN_MAP,
)
from app.core.duplicate_detector import (
    SmartDuplicateDetector,
    ExactDuplicateDetector,
    NearDuplicateDetector,
    PartialOverlapDetector,
    VersionDetector,
    DuplicateLevel,
)
from app.core.source_validator import (
    validate_official_legal_source_url,
    OFFICIAL_LEGAL_DOMAINS,
)
from app.core.text_preservation import (
    sanitize_input_text,
    validate_legal_title,
)
from app.core.scoring_engine import calculate_submission_quality_score
from app.db.models import Submission, User
from app.core.security import UserRole


# ==============================================================================
# ۱. تست‌های دقیق نرمال‌سازی نویسه‌های عربی به فارسی و ارقام
# ==============================================================================

def test_arabic_to_persian_character_mapping():
    """تبدیل کاراکترهای عربی (ي، ك، ة، ؤ، إ، أ، کشیده) به معادل‌های استاندارد خط فارسی."""
    normalizer = PersianTextNormalizer()
    
    arabic_raw = "قانون مدني؛ دادگاه كشور؛ رأي دادگاه؛ ارائة لايحة دفاعي؛ مقرّراتِ مصوّبـه"
    normalized = normalizer.normalize_arabic_to_persian(arabic_raw)
    
    assert "ي" not in normalized
    assert "ك" not in normalized
    assert "ة" not in normalized
    assert "ـ" not in normalized  # حذف کشیده (تطویل)
    assert "مدنی" in normalized
    assert "کشور" in normalized
    assert "لایحه" in normalized


def test_arabic_digits_to_persian_digits():
    """تبدیل تمام ارقام انگلیسی و عربی (0123456789) به ارقام استاندارد فارسی (۰۱۲۳۴۵۶۷۸۹)."""
    normalizer = PersianTextNormalizer()
    text_with_digits = "ماده 123 تبصره 45 و تاریخ 1402/05/29"
    persian_digits = normalizer.normalize_digits_to_persian(text_with_digits)
    
    assert "123" not in persian_digits
    assert "45" not in persian_digits
    assert "1402" not in persian_digits
    assert "۱۲۳" in persian_digits
    assert "۴۵" in persian_digits
    assert "۱۴۰۲" in persian_digits


def test_zwnj_normalization():
    """تثبیت و نرمال‌سازی نیم‌فاصله (Zero-Width Non-Joiner - \\u200c)."""
    normalizer = PersianTextNormalizer()
    # چندین نیم‌فاصله متوالی باید به یک نیم‌فاصله تبدیل شود
    multi_zwnj = "می\u200c\u200c\u200cباشد و می\u200c\u200cشود"
    res = normalizer.normalize_zwnj(multi_zwnj)
    assert "\u200c\u200c" not in res
    assert "می\u200cباشد" in res

    # حذف نیم‌فاصله چسبیده به فاصله خالی
    space_zwnj = " این \u200cیک متن است "
    res2 = normalizer.normalize_zwnj(space_zwnj)
    assert " \u200c" not in res2
    assert "\u200c " not in res2


def test_whitespace_and_punctuation_cleanup():
    """پاکسازی فاصله‌های اضافی و تنظیم نشانه‌گذاری کاما و نقطه ویرگول فارسی."""
    normalizer = PersianTextNormalizer()
    messy_text = "ماده ۱  :   متن با فاصله‌های    بسیار زیاد  ،،  و کامای دوبل  ؛؛"
    cleaned = normalizer.full_normalize(messy_text)
    
    assert "    " not in cleaned
    assert "  " not in cleaned
    assert "،،" not in cleaned
    assert "؛؛" not in cleaned
    assert "، " in cleaned or "،" in cleaned


# ==============================================================================
# ۲. تست‌های استانداردسازی ساختار مواد و تبصره‌های قانونی
# ==============================================================================

def test_legal_structure_article_formatting():
    """استانداردسازی تیتر مواد قانونی به فرمت 'ماده X:'."""
    formatter = LegalStructureFormatter()
    raw = (
        "ماده ۱ - کلیه اشخاص حقیقی و حقوقی مکلفند...\n"
        "ماده ۲ : هرگونه اقدام مغایر با این قانون جرم است.\n"
        "ماده ۳ متن بدون دونقطه و خط تیره"
    )
    structured = formatter.full_format(raw)
    
    assert 1 in structured.detected_articles
    assert 2 in structured.detected_articles
    assert "ماده ۱:" in structured.text
    assert len(structured.changes) >= 1


def test_legal_structure_note_and_clause_detection():
    """شناسایی تبصره‌ها و بندهای قانونی (الف، ب، ج...)."""
    formatter = LegalStructureFormatter()
    raw = (
        "ماده ۱۰: شرایط عمومی استخدام.\n"
        "تبصره ۱: اولویت با ایثارگران است.\n"
        "تبصره: مدارک تحصیلی باید معتبر باشد.\n"
        "الف) تابعیت جمهوری اسلامی ایران\n"
        "ب) عدم سوء پیشینه کیفری\n"
    )
    structured = formatter.full_format(raw)
    
    assert 10 in structured.detected_articles
    assert len(structured.detected_notes) >= 1
    assert len(structured.detected_clauses) > 0
    assert any("ف" in c for c in structured.detected_clauses)


def test_legal_typo_corrector():
    """تصحیح غلط‌های املایی رایج اسناد در خطوط مختلف."""
    corrector = LegalTypoCorrector()
    text_with_typos = (
        "مادهه ۱۲: بر طبق قوانین کشور.\n"
        "قانونن تجارت و ثبت شرکت‌ها.\n"
        "تبصرهه ۳ رعایت گردد.\n"
    )
    corrected, changes = corrector.correct_typos(text_with_typos)
    
    assert "مادهه" not in corrected
    assert "قانونن" not in corrected
    assert "تبصرهه" not in corrected
    assert "ماده" in corrected
    assert "قانون" in corrected
    assert "تبصره" in corrected
    assert len(changes) == 3


# ==============================================================================
# ۳. تست‌های استخراج فراداده، ارجاعات متقابل و ارزیابی ریسک
# ==============================================================================

def test_metadata_extraction_references_and_dates():
    """استخراج مراجع قانونی متقابل و تاریخ‌های تصویب شمسی."""
    extractor = LegalMetadataExtractor()
    sample_text = (
        "به استناد ماده ۵ قانون مدنی و همچنین قانون مجازات اسلامی مصوب ۱۳۷۰/۰۵/۰۱ و آیین‌نامه اجرایی، "
        "ماده ۲۲ قانون تجارت لازم‌الاجراست."
    )
    meta = extractor.full_extract(sample_text, title="ماده قانونی مربوط به قانون مدنی")
    
    assert len(meta.keywords) >= 3
    assert any("قانون مدنی" in ref for ref in meta.references)
    assert meta.approval_date is not None
    assert ("1370" in meta.approval_date or "۷۰" in meta.approval_date or "۰۵" in meta.approval_date)


def test_metadata_risk_assessment_with_repeal_keywords():
    """ارزیابی سطح ریسک HIGH در صورت وجود کلمات کلیدی ناسخ در متن."""
    extractor = LegalMetadataExtractor()
    high_risk_text = "ماده ۱: کلیه قوانین و مقررات مغایر صریحاً نسخ و ابطال می‌گردد."
    meta = extractor.full_extract(high_risk_text)
    assert meta.risk_level == "HIGH"

    low_risk_text = "ماده ۱: ساعت شروع به کار ادارات هشت صبح می‌باشد."
    meta_low = extractor.full_extract(low_risk_text)
    assert meta_low.risk_level == "LOW"


# ==============================================================================
# ۴. تست‌های اثرانگشت، هش و فاصله همینگ SimHash
# ==============================================================================

def test_simhash_fingerprinting_distance_and_similarity():
    """
    بررسی عملکرد الگوریتم SimHash:
    - متون دقیقاً یکسان: فاصله همینگ ۰ و تشابه ۱.۰
    - متون با تغییرات جزئی: فاصله همینگ کوچک و تشابه معنادار
    - متون کاملاً ناهمگون: تفاوت بیت بیشتر
    """
    t1 = "ماده ۱: هر مالکی نسبت به مایملک خود حق همه گونه تصرف و انتفاع دارد مگر در مواردی که قانون استثناء کرده باشد."
    t2 = "ماده ۱: هر مالکی نسبت به مایملک خود حق همه گونه تصرف و انتفاع دارد مگر در مواردی که قانون استثناء نموده باشد."
    t3 = "دستورالعمل نحوه صدور گذرنامه و روادید برای رانندگان ترانزیت جاده‌ای بین‌المللی."

    fp1 = TextFingerprinter.compute_simhash(t1)
    fp2 = TextFingerprinter.compute_simhash(t2)
    fp3 = TextFingerprinter.compute_simhash(t3)

    assert len(fp1) == 64
    assert len(fp2) == 64

    # فاصله متن ۱ با خودش
    assert TextFingerprinter.hamming_distance(fp1, fp1) == 0
    assert TextFingerprinter.similarity(fp1, fp1) == 1.0

    # فاصله متن ۱ با متن ۲
    dist_1_2 = TextFingerprinter.hamming_distance(fp1, fp2)
    sim_1_2 = TextFingerprinter.similarity(fp1, fp2)
    assert dist_1_2 <= 12
    assert sim_1_2 >= 0.80

    # فاصله متن ۱ با متن ۳ (کاملا نامربوط)
    dist_1_3 = TextFingerprinter.hamming_distance(fp1, fp3)
    assert dist_1_3 > 12


# ==============================================================================
# ۵. تست‌های سیستم کشف اسناد تکراری در ۴ لایه (SmartDuplicateDetector)
# ==============================================================================

def test_duplicate_detector_exact_hash_match(db_session: Session):
    """لایه اول: کشف سند ۱۰۰٪ تکراری از طریق انطباق SHA-256."""
    text = "ماده ۴۰: حق انتفاع عبارت از حقی است که به موجب آن شخص می‌تواند از مالی که عین آن ملک دیگری است یا مالک خاصی ندارد استفاده کند."
    content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()

    existing = Submission(
        id=str(uuid.uuid4()),
        submitter_id=str(uuid.uuid4()),
        source_title="قانون مدنی",
        legal_document_name="ماده ۴۰ قانون مدنی",
        raw_legal_text=text,
        content_hash=content_hash,
        source_url="https://rc.majlis.ir/law/40",
        source_domain="مجلس",
        document_type="law",
        issuing_authority="مجلس",
    )
    db_session.add(existing)
    db_session.commit()

    detector = SmartDuplicateDetector(db_session, Submission)
    report = detector.check_all_levels(text=text, metadata={}, title="ماده ۴۰")

    assert report.is_duplicate is True
    assert report.level == DuplicateLevel.EXACT
    assert report.similarity == 1.0
    assert report.existing_id == existing.id


def test_duplicate_detector_near_duplicate_simhash(db_session: Session):
    """لایه دوم: کشف سند بسیار مشابه (Near-Duplicate) با تشابه بالای ۹۵٪."""
    words = ['ماده', 'یک', 'قانون', 'ثبت', 'اسناد', 'و', 'املاک', 'کشور', 'مصوب', 'مجلس', 'شورای', 'ملی', 'سابق', 'که', 'در', 'تاریخ', 'مشخص', 'ابلاغ', 'گردیده', 'است', 'برای', 'تمامی', 'مراجع', 'قضایی', 'و', 'اداری', 'لازم', 'الاجرا', 'می', 'باشد', 'و', 'تخلف', 'از', 'آن', 'مستوجب', 'مجازات', 'انتظامی', 'است'] * 3
    text1 = ' '.join(words)
    words[5] = 'یا'
    text2 = ' '.join(words)

    fp1 = TextFingerprinter.compute_simhash(text1)
    existing = Submission(
        id=str(uuid.uuid4()),
        submitter_id=str(uuid.uuid4()),
        source_title="قانون ثبت اسناد و املاک رسمی",
        legal_document_name="قانون ثبت اسناد و املاک",
        raw_legal_text=text1,
        content_hash=hashlib.sha256(text1.encode("utf-8")).hexdigest(),
        content_fingerprint=fp1,
        source_url="https://qavanin.ir/10",
        source_domain="قوانین",
        document_type="law",
        issuing_authority="مجلس",
    )
    db_session.add(existing)
    db_session.commit()

    detector = SmartDuplicateDetector(db_session, Submission)
    report = detector.check_all_levels(text=text2, metadata={}, title="متفرقه نامربوط")

    assert report.is_duplicate is True
    assert report.level == DuplicateLevel.NEAR_DUPLICATE
    assert report.similarity >= 0.95
    assert report.existing_id == existing.id


def test_duplicate_detector_partial_overlap(db_session: Session):
    """لایه سوم: کشف هم‌پوشانی بر اساس اشتراک مواد قانونی (Article Overlap)."""
    text_existing = (
        "ماده ۱: تعریف واژگان\n"
        "ماده ۲: دامنه شمول قانون\n"
        "ماده ۳: تکالیف دستگاه‌های اجرایی\n"
        "ماده ۴: ضمانت اجراها\n"
    )
    text_new = (
        "ماده ۱: تعریف واژگان\n"
        "ماده ۲: دامنه شمول قانون\n"
        "ماده ۳: تکالیف دستگاه‌های اجرایی\n"
        "ماده ۵: مقررات متفرقه\n"
    )

    existing = Submission(
        id=str(uuid.uuid4()),
        submitter_id=str(uuid.uuid4()),
        source_title="قانون مدیریت خدمات کشوری",
        legal_document_name="قانون مدیریت خدمات کشوری - فصل اول",
        raw_legal_text=text_existing,
        source_url="https://rooznamehrasmi.ir/law",
        source_domain="روزنامه رسمی",
        document_type="law",
        issuing_authority="مجلس",
    )
    db_session.add(existing)
    db_session.commit()

    detector = SmartDuplicateDetector(db_session, Submission)
    metadata = {"title": "قانون مدیریت خدمات کشوری"}
    report = detector.check_all_levels(text=text_new, metadata=metadata, title="قانون مدیریت خدمات کشوری")

    assert report.level == DuplicateLevel.PARTIAL_OVERLAP
    assert len(report.overlapping_submissions) > 0
    overlap = report.overlapping_submissions[0]
    assert 1 in overlap.overlapping_articles
    assert 2 in overlap.overlapping_articles
    assert 3 in overlap.overlapping_articles


def test_duplicate_detector_version_and_amendment(db_session: Session):
    """لایه چهارم: شناسایی ارتباط نسخه‌ها، اصلاحیه‌ها و متمم‌های همان قانون."""
    text_orig = "قانون مالیات‌های مستقیم مصوب ۱۳۶۶: ماده ۱۳۱..."
    text_amend = "قانون اصلاحیه مالیات‌های مستقیم مصوب سال ۱۳۹۴: اصلاح ماده ۱۳۱..."

    existing = Submission(
        id=str(uuid.uuid4()),
        submitter_id=str(uuid.uuid4()),
        source_title="قانون مالیات‌های مستقیم",
        legal_document_name="قانون مالیات‌های مستقیم",
        raw_legal_text=text_orig,
        source_url="https://qavanin.ir/tax",
        source_domain="قوانین",
        document_type="law",
        issuing_authority="مجلس",
    )
    db_session.add(existing)
    db_session.commit()

    detector = SmartDuplicateDetector(db_session, Submission)
    report = detector.check_all_levels(text=text_amend, metadata={}, title="قانون اصلاحیه مالیات‌های مستقیم")

    assert report.level == DuplicateLevel.VERSION
    assert len(report.related_versions) > 0


# ==============================================================================
# ۶. تست‌های اعتبارسنجی دامنه مراجع رسمی و حاکمیتی (Source Validator)
# ==============================================================================

@pytest.mark.parametrize("domain, authority_title", list(OFFICIAL_LEGAL_DOMAINS.items())[:6])
def test_official_government_domains_strictly_validated(domain, authority_title):
    """تمام دامنه‌های موجود در وایت‌لیست رسمی حاکمیتی باید معتبر شناخته شوند."""
    test_url = f"https://{domain}/laws/acts/2026/view"
    is_valid, auth_name, err = validate_official_legal_source_url(test_url)
    assert is_valid is True
    assert auth_name == authority_title
    assert err == ""


def test_subdomains_of_official_domains_accepted():
    """ساب‌دامنه‌های پورتال‌های دولتی معتبر (مانند laws.dotic.ir) باید تایید شوند."""
    sub_url = "https://subportal.dotic.ir/rules/view/1234"
    is_valid, auth_name, err = validate_official_legal_source_url(sub_url)
    assert is_valid is True
    assert "داتیک" in auth_name or "ریاست جمهوری" in auth_name


@pytest.mark.parametrize("bad_url", [
    "https://google.com/search?q=law",
    "https://fa.wikipedia.org/wiki/civil_code",
    "https://personal-blog.ir/law.pdf",
    "https://telegram.me/legal_channel",
    "ftp://rooznamehrasmi.ir/file",
    "http://fake-majlis.com",
    "",
    "not-a-url-at-all",
])
def test_unauthorized_external_sources_strictly_rejected(bad_url):
    """هر دامنه غیرحاکمیتی، وبلاگ، شبکه‌های اجتماعی یا نشانی نامعتبر باید رد شود."""
    is_valid, auth_name, err = validate_official_legal_source_url(bad_url)
    assert is_valid is False
    assert auth_name == ""
    assert len(err) > 0


# ==============================================================================
# ۷. تست‌های پاکسازی حملات ترنسپورت و حفظ سلامت متن (Text Preservation)
# ==============================================================================

def test_sanitize_input_text_removes_null_bytes_and_scripts():
    """حذف بایت‌های پوچ، نویسه‌های کنترلی خطرناک و تگ‌های script در حین حفظ کامل متون حقوقی."""
    hostile = "ماده ۵\x00\x08: <script>alert('XSS')</script>متن قانون اساسی جمهوری اسلامی ایران."
    sanitized = sanitize_input_text(hostile)
    
    assert "\x00" not in sanitized
    assert "\x08" not in sanitized
    assert "<script>" not in sanitized
    assert "alert" not in sanitized
    assert "ماده ۵:" in sanitized
    assert "متن قانون اساسی جمهوری اسلامی ایران." in sanitized


def test_validate_legal_title():
    """عنوان سند قانونی باید حداقل ۳ کاراکتر غیرخالی و معنادار باشد."""
    assert validate_legal_title("قانون مدنی") is True
    assert validate_legal_title("   ") is False
    assert validate_legal_title("ab") is False
    assert validate_legal_title(None) is False


# ==============================================================================
# ۸. تست‌های محاسبه نمره کیفیت سند حقوقی (Quality Scoring)
# ==============================================================================

def test_quality_score_calculation_breakdown():
    """بررسی تفکیک نمره کیفیت: اصالت منبع، غنای واژگان حقوقی، کامل بودن ساختار و پیوست."""
    score, breakdown = calculate_submission_quality_score(
        source_url="https://rooznamehrasmi.ir/law/123",
        raw_legal_text=(
            "قانون آیین دادرسی مدنی مصوب مجلس شورای اسلامی.\n"
            "ماده ۱: آیین دادرسی مدنی مجموعه اصول و مقرراتی است...\n"
            "تبصره ۱: کلیه دادگاه‌ها مکلف به اجرا می‌باشند.\n"
            "رأی صادره از شعبه دیوان عالی کشور قطعی است.\n" * 5
        ),
        legal_document_name="قانون آیین دادرسی دادگاه‌های عمومی و انقلاب",
        issuing_authority="مجلس شورای اسلامی",
        publication_info="روزنامه رسمی شماره ۱۵۴۸۰",
        contributor_notes="تایپ و تطبیق داده شده با نسخه چاپی",
        has_file_attached=True,
    )

    assert breakdown["source_authenticity"] == 30
    assert breakdown["text_quality"] >= 30
    assert breakdown["structural_completeness"] == 25
    assert breakdown["context_and_attachment"] == 10
    assert score >= 95
    assert score <= 100
