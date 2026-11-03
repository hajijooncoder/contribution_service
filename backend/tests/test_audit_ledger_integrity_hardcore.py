"""
Audit Ledger Cryptographic Integrity Hardcore Test Suite.
تست‌های بشدت سخت‌گیرانه برای اعتبارسنجی زنجیره بلوکی ثبت وقایع حسابرسی (Audit Ledger).
شامل بررسی یکپارچگی ریاضی هش‌ها، کلید HMAC خارج از دیتابیس، کشف هرگونه دستکاری جزئی و رفتارهای همزمان.
"""

import hashlib
import hmac
import threading
from datetime import datetime, timezone
import pytest
from sqlalchemy.orm import Session

from app.core.audit_ledger import (
    CryptographicAuditLedger,
    compute_record_hash,
    format_timestamp_normalized,
    GENESIS_HASH,
)
from app.db.models import AuditLog
from app.config import settings


def test_genesis_block_links_to_genesis_hash(db_session: Session):
    """بررسی اینکه اولین ورودی در زنجیره حتماً به GENESIS_HASH ارجاع می‌دهد."""
    # پاکسازی اولیه رکوردهای تست قبلی در صورت وجود
    db_session.query(AuditLog).delete()
    db_session.commit()

    entry = CryptographicAuditLedger.append_entry(
        db=db_session,
        actor_id="actor-genesis-001",
        action="SYSTEM_INIT",
        target_id="target-001",
        details="Initial genesis event",
    )
    db_session.commit()

    assert entry.previous_hash == GENESIS_HASH
    assert entry.record_hash is not None
    assert len(entry.record_hash) == 64
    assert int(entry.record_hash, 16) > 0


def test_sequential_hash_chaining_integrity(db_session: Session):
    """بررسی پیوستگی زنجیره در درج متوالی ۱۰ رکورد حسابرسی."""
    db_session.query(AuditLog).delete()
    db_session.commit()

    created_entries = []
    for i in range(10):
        entry = CryptographicAuditLedger.append_entry(
            db=db_session,
            actor_id=f"actor-{i}",
            action=f"ACTION_STEP_{i}",
            target_id=f"target-seq-{i}",
            details=f"Sequential step {i} details with Persian text شماره {i}",
        )
        db_session.commit()
        created_entries.append(entry)

    # بررسی صحت اتصال هر بلوک به بلوک ماقبل
    assert created_entries[0].previous_hash == GENESIS_HASH
    for i in range(1, 10):
        assert created_entries[i].previous_hash == created_entries[i - 1].record_hash

    # راستی‌آزمایی کل زنجیره توسط متد رسمی
    is_valid, msg, broken_id = CryptographicAuditLedger.verify_ledger_integrity(db_session)
    assert is_valid is True
    assert broken_id is None
    assert "10 chained blocks" in msg


def test_detect_tampered_details_in_historical_record(db_session: Session):
    """دستکاری یک کاراکتر در جزییات یک رکورد قدیمی باید بلافاصله زنجیره را باطل کند."""
    db_session.query(AuditLog).delete()
    db_session.commit()

    for i in range(5):
        CryptographicAuditLedger.append_entry(
            db=db_session,
            actor_id=f"actor-{i}",
            action=f"ACTION_{i}",
            target_id=f"target-{i}",
            details=f"Safe original payload {i}",
        )
        db_session.commit()

    # مهاجم وارد دیتابیس شده و محتوای رکورد سوم را تغییر می‌دهد
    victim = db_session.query(AuditLog).order_by(AuditLog.id.asc()).offset(2).first()
    assert victim is not None
    victim_id = victim.id
    victim.details = "Safe original payload 2 [TAMPERED_BY_ATTACKER]"
    db_session.commit()

    is_valid, msg, broken_id = CryptographicAuditLedger.verify_ledger_integrity(db_session)
    assert is_valid is False
    assert broken_id == victim_id
    assert "Tampered entry detected" in msg


def test_detect_tampered_action_field(db_session: Session):
    """دستکاری در فیلد action باید باعث عدم تطابق هش HMAC شود."""
    db_session.query(AuditLog).delete()
    db_session.commit()

    entry = CryptographicAuditLedger.append_entry(
        db=db_session,
        actor_id="reviewer-99",
        action="REVIEW_REJECTED",
        target_id="sub-100",
        details="Proper rejection reason",
    )
    db_session.commit()

    # مهاجم اکشن را به تایید تبدیل می‌کند بدون کلید HMAC
    entry.action = "QUORUM_REACHED_ACCEPTED"
    db_session.commit()

    is_valid, msg, broken_id = CryptographicAuditLedger.verify_ledger_integrity(db_session)
    assert is_valid is False
    assert broken_id == entry.id
    assert "payload does not match hash" in msg


def test_detect_tampered_actor_id(db_session: Session):
    """جعل هویت کنش‌گر (actor_id) در دفترکل گذشته باید بلافاصله کشف شود."""
    db_session.query(AuditLog).delete()
    db_session.commit()

    entry = CryptographicAuditLedger.append_entry(
        db=db_session,
        actor_id="legitimate-contributor",
        action="CONTRIBUTION_SUBMITTED",
        target_id="sub-200",
        details="Standard submission",
    )
    db_session.commit()

    entry.actor_id = "malicious-impersonator"
    db_session.commit()

    is_valid, msg, broken_id = CryptographicAuditLedger.verify_ledger_integrity(db_session)
    assert is_valid is False
    assert broken_id == entry.id


def test_detect_tampered_target_id(db_session: Session):
    """تغییر سند هدف (target_id) باید بلافاصله اعتبارسنجی را بشکند."""
    db_session.query(AuditLog).delete()
    db_session.commit()

    entry = CryptographicAuditLedger.append_entry(
        db=db_session,
        actor_id="admin-01",
        action="ROLE_PROMOTED",
        target_id="user-good-citizen",
        details="Promoted to reviewer",
    )
    db_session.commit()

    entry.target_id = "user-malicious-agent"
    db_session.commit()

    is_valid, msg, broken_id = CryptographicAuditLedger.verify_ledger_integrity(db_session)
    assert is_valid is False
    assert broken_id == entry.id


def test_detect_deleted_middle_entry(db_session: Session):
    """حذف یک رکورد از وسط زنجیره باید اتصال previous_hash رکورد بعدی را قطع کند."""
    db_session.query(AuditLog).delete()
    db_session.commit()

    entries = []
    for i in range(5):
        e = CryptographicAuditLedger.append_entry(
            db=db_session,
            actor_id=f"actor-{i}",
            action=f"ACT_{i}",
            target_id=f"tgt-{i}",
            details=f"Block {i}",
        )
        db_session.commit()
        entries.append(e)

    # حذف رکورد وسطی (ایندکس ۲)
    middle_entry = entries[2]
    next_entry_id = entries[3].id
    db_session.delete(middle_entry)
    db_session.commit()

    is_valid, msg, broken_id = CryptographicAuditLedger.verify_ledger_integrity(db_session)
    assert is_valid is False
    assert broken_id == next_entry_id
    assert "Broken chain link" in msg
    assert "previous_hash mismatch" in msg


def test_hmac_key_isolation_against_recomputation_attack(db_session: Session):
    """
    آزمون سناریوی تهدید پیشرفته:
    مهاجم دسترسی خواندن و نوشتن کامل به دیتابیس دارد، اما کلید HMAC را ندارد.
    مهاجم رکوردی را تغییر می‌دهد و سعی می‌کند کل زنجیره بعد از آن را با یک کلید حدسی یا SHA256 ساده بازتولید کند.
    سیستم با کلید اصلی باید حمله را Fail-Closed کند.
    """
    db_session.query(AuditLog).delete()
    db_session.commit()

    for i in range(4):
        CryptographicAuditLedger.append_entry(
            db=db_session,
            actor_id=f"author-{i}",
            action=f"EVENT_{i}",
            target_id=f"doc-{i}",
            details=f"Payload {i}",
        )
        db_session.commit()

    # مهاجم رکورد ۱ را دستکاری می‌کند و زنجیره را با کلید جعلی recompute می‌کند
    attacker_fake_secret = "attacker-stolen-or-guessed-key"
    all_entries = db_session.query(AuditLog).order_by(AuditLog.timestamp.asc(), AuditLog.id.asc()).all()

    all_entries[1].details = "Tampered fraudulent event"
    prev_h = all_entries[0].record_hash

    for entry in all_entries[1:]:
        entry.previous_hash = prev_h
        fake_hash = compute_record_hash(
            previous_hash=prev_h,
            actor_id=entry.actor_id,
            action=entry.action,
            target_id=entry.target_id,
            timestamp_str=entry.timestamp,
            details=entry.details,
            secret_key=attacker_fake_secret,
        )
        entry.record_hash = fake_hash
        prev_h = fake_hash

    db_session.commit()

    is_valid, msg, broken_id = CryptographicAuditLedger.verify_ledger_integrity(db_session)
    assert is_valid is False
    assert broken_id == all_entries[1].id
    assert "Tampered entry detected" in msg


def test_single_bit_flip_detection(db_session: Session):
    """تغییر حتی یک کاراکتر/بیت در هش ذخیره شده باید با شکست اعتبارسنجی مواجه شود."""
    db_session.query(AuditLog).delete()
    db_session.commit()

    entry = CryptographicAuditLedger.append_entry(
        db=db_session,
        actor_id="verifier-1",
        action="BIT_TEST",
        target_id="target-bit",
        details="Testing bit-level integrity",
    )
    db_session.commit()

    orig_hash = entry.record_hash
    # تلنگر زدن به آخرین کاراکتر هگز
    flipped_char = "0" if orig_hash[-1] != "0" else "1"
    entry.record_hash = orig_hash[:-1] + flipped_char
    db_session.commit()

    is_valid, msg, broken_id = CryptographicAuditLedger.verify_ledger_integrity(db_session)
    assert is_valid is False
    assert broken_id == entry.id


def test_empty_ledger_integrity(db_session: Session):
    """دفترکل خالی باید معتبر با پیام خالی بودن اعلام شود."""
    db_session.query(AuditLog).delete()
    db_session.commit()

    is_valid, msg, broken_id = CryptographicAuditLedger.verify_ledger_integrity(db_session)
    assert is_valid is True
    assert broken_id is None
    assert "empty" in msg.lower()


def test_checkpoint_generation_and_tamper_proofing(db_session: Session):
    """تست امضای رمزی Checkpoint دفترکل برای ارسال به شاهدان خارجی (External Witness)."""
    db_session.query(AuditLog).delete()
    db_session.commit()

    # ۱. چک‌پوینت دفترکل خالی
    empty_cp = CryptographicAuditLedger.get_ledger_checkpoint(db_session)
    assert empty_cp["tip_record_hash"] == GENESIS_HASH
    assert empty_cp["tip_log_id"] is None
    assert empty_cp["total_records"] == 0
    assert len(empty_cp["checkpoint_signature"]) == 64

    # ۲. ایجاد رکوردها و بررسی تطابق tip_record_hash
    last_entry = None
    for i in range(3):
        last_entry = CryptographicAuditLedger.append_entry(
            db=db_session,
            actor_id=f"actor-cp-{i}",
            action="CP_ACTION",
            target_id=f"doc-cp-{i}",
            details=f"Data {i}",
        )
        db_session.commit()

    cp = CryptographicAuditLedger.get_ledger_checkpoint(db_session)
    assert cp["tip_record_hash"] == last_entry.record_hash
    assert cp["tip_log_id"] == last_entry.id
    assert cp["total_records"] == 3

    # راستی‌آزمایی مستقل امضای چک‌پوینت با کلید اصلی
    expected_payload = f"{cp['tip_record_hash']}|{cp['tip_log_id']}|{cp['total_records']}|{cp['checkpoint_timestamp']}".encode("utf-8")
    expected_sig = hmac.new(settings.AUDIT_LEDGER_SECRET.encode("utf-8"), expected_payload, hashlib.sha256).hexdigest()
    assert cp["checkpoint_signature"] == expected_sig


def test_unicode_persian_and_special_characters_preservation(db_session: Session):
    """بررسی رفتار هش در متون فارسی پیچیده، اعراب، نیم‌فاصله و کاراکترهای ویژه."""
    db_session.query(AuditLog).delete()
    db_session.commit()

    complex_persian = "قانون آیین‌نامه اجرایی مصوّب هیأت وزیران؛ ماده ۱۲ (تبصرهٔ ۲) با علامت‌های «» و % و & و <xml>"
    entry = CryptographicAuditLedger.append_entry(
        db=db_session,
        actor_id="کاربر-حقوقی-۱۲۳",
        action="ثبت_سند_رسمی",
        target_id="سند-قوه-قضائیه-۴۵۶",
        details=complex_persian,
    )
    db_session.commit()

    is_valid, msg, broken_id = CryptographicAuditLedger.verify_ledger_integrity(db_session)
    assert is_valid is True
    assert broken_id is None

    # بررسی مجدد هش به روش دستی
    manual_hash = compute_record_hash(
        previous_hash=GENESIS_HASH,
        actor_id="کاربر-حقوقی-۱۲۳",
        action="ثبت_سند_رسمی",
        target_id="سند-قوه-قضائیه-۴۵۶",
        timestamp_str=entry.timestamp,
        details=complex_persian,
    )
    assert entry.record_hash == manual_hash


def test_extremely_large_details_payload(db_session: Session):
    """تست ورودی عظیم جزئیات (مثلا متون چند صد کیلوبایتی قوانین) بدون سرریز یا شکست زنجیره."""
    db_session.query(AuditLog).delete()
    db_session.commit()

    large_text = ("ماده ۱: کلیه قوانین و مقررات مدنی کشور لازم‌الاجرا می‌باشند.\n" * 2000)
    assert len(large_text) > 100000  # بیش از ۱۰۰ کیلوبایت

    entry = CryptographicAuditLedger.append_entry(
        db=db_session,
        actor_id="admin-bulk",
        action="BULK_LEGAL_IMPORT",
        target_id="bulk-doc-001",
        details=large_text,
    )
    db_session.commit()

    is_valid, _, broken_id = CryptographicAuditLedger.verify_ledger_integrity(db_session)
    assert is_valid is True
    assert broken_id is None


def test_timestamp_normalization_deterministic(db_session: Session):
    """بررسی اینکه یکسان‌سازی فرمت زمان در تولید پیلود هش کاملا قطعی (Deterministic) است."""
    now = datetime(2026, 11, 3, 14, 30, 45, 123456, tzinfo=timezone.utc)
    norm1 = format_timestamp_normalized(now)
    norm2 = format_timestamp_normalized("2026-11-03 14:30:45.123456+00:00")
    assert norm1 == "2026-11-03 14:30:45"
    assert norm2 == "2026-11-03 14:30:45"


def test_concurrent_append_thread_safety(db_session: Session):
    """
    تست فشار همزمانی روی دفترکل:
    چندین ریسه همزمان در حال اضافه کردن رکورد حسابرسی هستند.
    نباید هیچ دو رکوردی previous_hash متناقض یا نامعتبر ایجاد کنند و ساختار نهایی باید کاملا سالم بماند.
    """
    from app.db.session import SessionLocal
    
    db_session.query(AuditLog).delete()
    db_session.commit()

    # رکورد پیدایش را ابتدا ثبت می‌کنیم
    CryptographicAuditLedger.append_entry(
        db=db_session,
        actor_id="setup-actor",
        action="INIT",
        target_id="init",
        details="Genesis lock init",
    )
    db_session.commit()

    errors = []

    lock = threading.Lock()
    def worker_append(thread_id: int):
        thread_db = SessionLocal()
        try:
            for j in range(5):
                with lock:
                    CryptographicAuditLedger.append_entry(
                        db=thread_db,
                        actor_id=f"thread-{thread_id}",
                        action=f"THREAD_ACTION_{j}",
                        target_id=f"target-t{thread_id}-j{j}",
                        details=f"Thread {thread_id} step {j}",
                    )
                    thread_db.commit()
        except Exception as e:
            errors.append(str(e))
        finally:
            thread_db.close()

    threads = [threading.Thread(target=worker_append, args=(t,)) for t in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0, f"Thread errors encountered: {errors}"

    total_count = db_session.query(AuditLog).count()
    assert total_count == 1 + (4 * 5)

    # بررسی صحت زنجیره بعد از رقابت ریسه‌ها
    is_valid, msg, broken_id = CryptographicAuditLedger.verify_ledger_integrity(db_session)
    assert is_valid is True, f"Ledger integrity broken under concurrency: {msg} (at ID {broken_id})"
