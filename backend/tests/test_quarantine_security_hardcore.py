"""
Quarantine Security and File Isolation Hardcore Test Suite.
تست‌های بشدت سخت‌گیرانه برای اعتبارسنجی امنیت قرنطینه فایل، کشف بدافزارها و حفاظت از یکپارچگی بایت‌ها.
"""

import io
import os
import zipfile
import pytest
from pathlib import Path

from app.core.quarantine import (
    QuarantineManager,
    inspect_magic_bytes,
    inspect_pdf_content,
    inspect_docx_archive,
    sanitize_filename,
    FORBIDDEN_SIGNATURES,
    FORBIDDEN_ZIP_EXTENSIONS,
    DANGEROUS_PDF_TOKENS,
)
from app.config import settings


# ==============================================================================
# ۱. تست‌های تفصیلی شناسایی امضای فایل و باینری‌های مخرب (Magic Bytes)
# ==============================================================================

@pytest.mark.parametrize("sig", FORBIDDEN_SIGNATURES)
def test_all_forbidden_signatures_strictly_rejected(sig):
    """بررسی تک تک امضاهای ممنوعه: اجرایی، باینری لینوکس، شل‌اسکریپت، اسکریپت وب، پی‌اچ‌پی."""
    malicious_payload = sig + b"\x00\x01\x02PayloadBytes"
    is_safe, mime, reason = inspect_magic_bytes(malicious_payload)
    assert is_safe is False
    assert "dangerous" in mime or "prohibited" in reason.lower() or "rejected" in reason.lower()


def test_dos_pe_executable_blocked():
    """فایل اجرایی ویندوز (PE/EXE) با هدر MZ باید بلافاصله رد شود."""
    raw_exe = b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff\x00\x00"
    is_safe, mime, reason = inspect_magic_bytes(raw_exe)
    assert is_safe is False
    assert mime == "dangerous/executable"


def test_linux_elf_binary_blocked():
    """باینری اجرایی لینوکس با هدر ELF باید بلافاصله رد شود."""
    raw_elf = b"\x7fELF\x02\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    is_safe, mime, reason = inspect_magic_bytes(raw_elf)
    assert is_safe is False
    assert mime == "dangerous/executable"


def test_shell_script_blocked():
    """اسکریپت با هدر شل‌بنگ (#!) باید مسدود شود."""
    raw_sh = b"#!/bin/bash\nrm -rf / --no-preserve-root\n"
    is_safe, mime, reason = inspect_magic_bytes(raw_sh)
    assert is_safe is False
    assert mime == "dangerous/executable"


def test_php_script_blocked():
    """فایل وب شل PHP باید مسدود شود."""
    raw_php = b"<?php system($_GET['cmd']); ?>"
    is_safe, mime, reason = inspect_magic_bytes(raw_php)
    assert is_safe is False
    assert mime == "dangerous/executable"


def test_case_insensitive_forbidden_signatures():
    """حساس نبودن به حروف بزرگ و کوچک در امضاهای ممنوعه مانند mz یا <SCRIPT."""
    payload1 = b"mz\x90\x00"
    assert inspect_magic_bytes(payload1)[0] is False

    payload2 = b"<SCRIPT language='javascript'>alert(1)</SCRIPT>"
    assert inspect_magic_bytes(payload2)[0] is False


def test_empty_payload_rejected():
    """فایل صفر بایتی باید بلافاصله رد شود."""
    is_safe, mime, reason = inspect_magic_bytes(b"")
    assert is_safe is False
    assert "empty" in reason.lower()


def test_unsupported_binary_garbage_rejected():
    """بایت‌های تصادفی یا فرمت‌های غیرمجاز (مانند MP4/AVI/ISO) باید مسدود شوند."""
    garbage = b"\x00\xff\xfe\x01\x02\x03\x04\x05\xaa\xbb\xcc\xdd" * 20
    is_safe, mime, reason = inspect_magic_bytes(garbage)
    assert is_safe is False
    assert mime == "application/octet-stream"
    assert "unknown or unsupported" in reason.lower()


# ==============================================================================
# ۲. تست‌های پیشرفته امنیت اسناد PDF (Active Execution Tokens)
# ==============================================================================

@pytest.mark.parametrize("token", [
    b"/Launch",
    b"/JavaScript",
    b"/JS",
    b"/OpenAction",
    b"/EmbeddedFiles",
    b"/SubmitForm",
    b"/ImportData",
    b"/RichMedia",
])
def test_pdf_with_dangerous_active_tokens_blocked(token):
    """هر سند PDF حاوی کدهای اجرایی، جاوا اسکریپت یا اکشن‌های بازشدن خودکار باید شناسایی و مسدود شود."""
    malicious_pdf = (
        b"%PDF-1.7\n"
        b"1 0 obj\n"
        b"<< /Type /Catalog " + token + b" 2 0 R >>\n"
        b"endobj\n"
        b"%%EOF\n"
    )
    is_safe, mime, reason = inspect_magic_bytes(malicious_pdf)
    assert is_safe is False
    assert mime == "dangerous/pdf-active-content"
    assert "contains active executable scripts" in reason


def test_clean_sanitized_pdf_accepted():
    """سند PDF حقوقی تمیز و بدون آبجکت‌های خطرناک باید تایید شود."""
    clean_pdf = (
        b"%PDF-1.4\n"
        b"1 0 obj\n"
        b"<< /Type /Catalog /Pages 2 0 R >>\n"
        b"endobj\n"
        b"2 0 obj\n"
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>\n"
        b"endobj\n"
        b"3 0 obj\n"
        b"<< /Type /Page /Parent 2 0 R >>\n"
        b"endobj\n"
        b"xref\n0 4\n0000000000 65535 f \n"
        b"trailer\n<< /Size 4 /Root 1 0 R >>\n"
        b"startxref\n150\n%%EOF\n"
    )
    is_safe, mime, reason = inspect_magic_bytes(clean_pdf)
    assert is_safe is True
    assert mime == "application/pdf"
    assert "Valid sanitized PDF" in reason


# ==============================================================================
# ۳. تست‌های بازرسی عمیق اسناد DOCX و آرشیوهای ZIP
# ==============================================================================

def create_in_memory_zip(file_dict: dict) -> bytes:
    """ابزار کمکی برای ساخت آرشیو زیپ در حافظه."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for filename, content in file_dict.items():
            zf.writestr(filename, content)
    return buf.getvalue()


def test_valid_openxml_docx_accepted():
    """فایل DOCX رسمی که دارای ساختار OpenXML استاندارد است باید تایید شود."""
    docx_bytes = create_in_memory_zip({
        "[Content_Types].xml": '<?xml version="1.0"?><Types></Types>',
        "word/document.xml": '<?xml version="1.0"?><w:document><w:body>متن قانون</w:body></w:document>',
        "_rels/.rels": '<?xml version="1.0"?>',
    })
    is_safe, mime, reason = inspect_magic_bytes(docx_bytes)
    assert is_safe is True
    assert mime == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    assert "Valid OpenXML DOCX" in reason


def test_docx_with_macro_vba_project_blocked():
    """سند ورد آلوده به ماکرو (vbaProject.bin) باید بلافاصله کشف و مسدود شود."""
    infected_docx = create_in_memory_zip({
        "[Content_Types].xml": '<Types></Types>',
        "word/document.xml": '<w:document></w:document>',
        "word/vbaProject.bin": b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1MaliciousMacroPayload",
    })
    is_safe, mime, reason = inspect_magic_bytes(infected_docx)
    assert is_safe is False
    assert mime == "dangerous/zip-executable"
    assert "macro component" in reason


@pytest.mark.parametrize("bad_ext", [
    "payload.exe", "script.bat", "run.sh", "agent.py", "exploit.dll", "module.so", "setup.msi", "keylogger.js"
])
def test_docx_with_embedded_executables_blocked(bad_ext):
    """جاسازی فایل اجرایی یا اسکریپتی داخل ساختار زیپ سند ورد باید شناسایی شود."""
    infected = create_in_memory_zip({
        "[Content_Types].xml": '<Types></Types>',
        "word/document.xml": '<w:document></w:document>',
        f"word/media/{bad_ext}": b"EvilExecutableContent",
    })
    is_safe, mime, reason = inspect_magic_bytes(infected)
    assert is_safe is False
    assert mime == "dangerous/zip-executable"
    assert bad_ext in reason


def test_generic_zip_without_openxml_structure_rejected():
    """یک فایل زیپ معمولی تغییر نام یافته به docx بدون ساختار ورد باید رد شود."""
    generic_zip = create_in_memory_zip({
        "notes.txt": "just some text",
        "data.csv": "col1,col2\n1,2",
    })
    is_safe, mime, reason = inspect_magic_bytes(generic_zip)
    assert is_safe is False
    assert mime == "application/zip"
    assert "lacks valid OpenXML DOCX structure" in reason


def test_corrupted_zip_archive_handled_gracefully():
    """فایل زیپ خراب و ناقص نباید سیستم را کرش کند."""
    corrupted = b"PK\x03\x04\x14\x00\x00\x00\x08\x00corrupted_bytes_without_central_directory"
    is_safe, mime, reason = inspect_magic_bytes(corrupted)
    assert is_safe is False
    assert "Malformed or corrupted" in reason or "failure" in reason


# ==============================================================================
# ۴. تست‌های پاکسازی نام فایل و جلوگیری از پیمایش مسیر (Path Traversal)
# ==============================================================================

def test_sanitize_filename_directory_traversal():
    """حمله پیمایش دایرکتوری (../..) باید خنثی شده و کاراکترهای خطرناک حذف شوند."""
    dirty1 = "../../etc/passwd"
    clean1 = sanitize_filename(dirty1)
    assert ".." not in clean1
    assert "/" not in clean1
    assert clean1 == "._._etc_passwd" or "etc_passwd" in clean1

    dirty2 = "..\\..\\windows\\system32\\cmd.exe"
    clean2 = sanitize_filename(dirty2)
    assert ".." not in clean2
    assert "\\" not in clean2


def test_sanitize_filename_preserves_persian_letters():
    """حفظ حروف فارسی، اعداد و خط فاصله در نام فایل مصوبات و قوانین."""
    persian_name = "قانون_مدنی_مصوب_۱۳۰۷-نسخه_اصلی.pdf"
    clean = sanitize_filename(persian_name)
    assert clean == persian_name


def test_sanitize_filename_length_limit():
    """محدود کردن طول نام فایل به ۲۰۰ کاراکتر برای جلوگیری از سرریز بافر فایل‌سیستم."""
    super_long = "a" * 300 + ".pdf"
    clean = sanitize_filename(super_long)
    assert len(clean) <= 200


def test_sanitize_filename_special_characters_removed():
    """حذف کاراکترهای لوله‌کشی و پایپ و پرانتزهای غیرمجاز شل."""
    dirty = "law;rm -rf;$(calc)|`whoami`.pdf"
    clean = sanitize_filename(dirty)
    assert ";" not in clean
    assert "$" not in clean
    assert "|" not in clean
    assert "`" not in clean


# ==============================================================================
# ۵. تست‌های یکپارچگی QuarantineManager (ذخیره‌سازی ایزوله و هش قطعی)
# ==============================================================================

def test_quarantine_manager_exact_sha256_and_byte_preservation(tmp_path):
    """
    بررسی اصل بنیادین قرنطینه:
    بایت‌های فایل حقوقی دست‌نخورده ذخیره می‌شوند و هش SHA-256 ذخیره شده دقیقاً با هش بایت‌های اصلی تطابق دارد.
    """
    qm = QuarantineManager(quarantine_dir=str(tmp_path / "quarantine_test"))
    
    clean_legal_text = (
        "قانون اساسی جمهوری اسلامی ایران\n"
        "اصل اول: حکومت ایران جمهوری اسلامی است...\n"
    ).encode("utf-8")

    res = qm.process_and_quarantine(clean_legal_text, "constitutional_law.txt")

    assert res["file_size"] == len(clean_legal_text)
    assert res["quarantine_status"] == "quarantined_verified"
    assert res["detected_mime"] == "text/plain"

    # راستی‌آزمایی هش
    import hashlib
    expected_hash = hashlib.sha256(clean_legal_text).hexdigest()
    assert res["sha256_hash"] == expected_hash

    # راستی‌آزمایی خواندن مستقیم از دیسک
    stored_path = Path(res["storage_path"])
    assert stored_path.exists()
    assert stored_path.read_bytes() == clean_legal_text

    # راستی‌آزمایی پرمیشن‌های امنیتی فایل (0o644)
    file_stat = os.stat(stored_path)
    # مطمئن می‌شویم فایل اجازه اجرا (Executable) ندارد
    assert (file_stat.st_mode & 0o111) == 0


def test_quarantine_manager_rejects_zero_bytes(tmp_path):
    """تلاش برای قرنطینه کردن فایل خالی باید خطا بدهد."""
    qm = QuarantineManager(quarantine_dir=str(tmp_path))
    with pytest.raises(ValueError, match="empty"):
        qm.process_and_quarantine(b"", "empty.txt")


def test_quarantine_manager_rejects_oversized_file(tmp_path):
    """تلاش برای قرنطینه کردن فایل بزرگتر از حد مجاز (25MB) باید با خطا متوقف شود."""
    qm = QuarantineManager(quarantine_dir=str(tmp_path))
    oversized = b"A" * (settings.MAX_UPLOAD_SIZE_BYTES + 1024)
    with pytest.raises(ValueError, match="exceeds maximum allowed"):
        qm.process_and_quarantine(oversized, "huge.txt")


def test_quarantine_manager_unique_filenames_for_identical_content(tmp_path):
    """دو بار آپلود یک فایل مشابه باید شناسه‌های فیزیکی و UUID جداگانه دریافت کند."""
    qm = QuarantineManager(quarantine_dir=str(tmp_path))
    content = b"Some legal content text here."
    
    res1 = qm.process_and_quarantine(content, "doc.txt")
    res2 = qm.process_and_quarantine(content, "doc.txt")

    assert res1["sha256_hash"] == res2["sha256_hash"]
    assert res1["file_id"] != res2["file_id"]
    assert res1["stored_filename"] != res2["stored_filename"]
    assert res1["storage_path"] != res2["storage_path"]
