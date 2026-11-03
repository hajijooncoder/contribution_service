import hashlib
import hmac
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from app.db.models import AuditLog
from app.config import settings

GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"
TupleIntegrity = Tuple[bool, str, Optional[str]]

def format_timestamp_normalized(ts: Any) -> str:
    """Normalizes datetime to string consistently across all database dialects."""
    if isinstance(ts, datetime):
        return ts.strftime("%Y-%m-%d %H:%M:%S")
    return str(ts)[:19]

def compute_record_hash(
    previous_hash: str,
    actor_id: str,
    action: str,
    target_id: str,
    timestamp_str: str,
    details: str,
    secret_key: Optional[str] = None
) -> str:
    """
    Computes keyed HMAC-SHA256 for a single audit ledger block.
    Key custody is maintained outside the database layer in application secrets,
    strictly preventing full-chain recomputation attacks by an adversary with database access.
    """
    norm_ts = format_timestamp_normalized(timestamp_str)
    payload = f"{previous_hash}|{actor_id}|{action}|{target_id}|{norm_ts}|{details or ''}".encode("utf-8")
    key = (secret_key or settings.AUDIT_LEDGER_SECRET).encode("utf-8")
    return hmac.new(key, payload, hashlib.sha256).hexdigest()

class CryptographicAuditLedger:
    """
    Append-only cryptographic hash-chained audit ledger for staging operations.
    Enforces HMAC integrity: modifying any past record or attempting full-chain
    recomputation without key custody breaks the chain.
    """

    @staticmethod
    def append_entry(
        db: Session,
        actor_id: str,
        action: str,
        target_id: str,
        details: str = "",
        secret_key: Optional[str] = None
    ) -> AuditLog:
        """Appends a new cryptographically chained audit log entry."""
        latest_entry = db.query(AuditLog).order_by(AuditLog.timestamp.desc(), AuditLog.id.desc()).first()
        prev_hash = latest_entry.record_hash if (latest_entry and hasattr(latest_entry, "record_hash") and latest_entry.record_hash) else GENESIS_HASH

        now = datetime.now(timezone.utc)
        record_hash = compute_record_hash(
            previous_hash=prev_hash,
            actor_id=actor_id,
            action=action,
            target_id=target_id,
            timestamp_str=now,
            details=details,
            secret_key=secret_key
        )

        entry = AuditLog(
            action=action,
            actor_id=actor_id,
            target_id=target_id,
            details=details,
            previous_hash=prev_hash,
            record_hash=record_hash,
            timestamp=now
        )
        db.add(entry)
        db.flush()
        return entry

    @staticmethod
    def verify_ledger_integrity(db: Session, secret_key: Optional[str] = None) -> TupleIntegrity:
        """
        Scans all audit log entries in chronological order and verifies the cryptographic chain
        using the HMAC secret.
        Returns: (is_valid, error_message, broken_at_id)
        """
        entries = db.query(AuditLog).order_by(AuditLog.timestamp.asc(), AuditLog.id.asc()).all()
        if not entries:
            return True, "Ledger is empty", None

        expected_prev_hash = GENESIS_HASH
        for entry in entries:
            # Check previous hash linkage
            if entry.previous_hash != expected_prev_hash:
                return False, f"Broken chain link at log ID {entry.id}: previous_hash mismatch", entry.id

            # Recalculate HMAC-SHA256
            recalculated = compute_record_hash(
                previous_hash=entry.previous_hash,
                actor_id=entry.actor_id,
                action=entry.action,
                target_id=entry.target_id,
                timestamp_str=entry.timestamp,
                details=entry.details,
                secret_key=secret_key
            )
            if recalculated != entry.record_hash:
                return False, f"Tampered entry detected at log ID {entry.id}: payload does not match hash", entry.id

            expected_prev_hash = entry.record_hash

        return True, f"Ledger verified successfully ({len(entries)} chained blocks)", None

    @staticmethod
    def get_ledger_checkpoint(db: Session, secret_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Generates an immutable cryptographic checkpoint of the current ledger state
        suitable for external witness anchoring or pull-cycle synchronization.
        """
        latest_entry = db.query(AuditLog).order_by(AuditLog.timestamp.desc(), AuditLog.id.desc()).first()
        total_records = db.query(AuditLog).count()
        tip_hash = latest_entry.record_hash if latest_entry else GENESIS_HASH
        tip_id = latest_entry.id if latest_entry else None
        
        now_iso = datetime.now(timezone.utc).isoformat()
        checkpoint_payload = f"{tip_hash}|{tip_id}|{total_records}|{now_iso}".encode("utf-8")
        key = (secret_key or settings.AUDIT_LEDGER_SECRET).encode("utf-8")
        checkpoint_sig = hmac.new(key, checkpoint_payload, hashlib.sha256).hexdigest()

        return {
            "tip_record_hash": tip_hash,
            "tip_log_id": tip_id,
            "total_records": total_records,
            "checkpoint_timestamp": now_iso,
            "checkpoint_signature": checkpoint_sig
        }
