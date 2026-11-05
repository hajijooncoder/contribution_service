import hashlib
import hmac
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Tuple, List
from sqlalchemy.orm import Session
from app.db.models import AuditLog
from app.config import settings

logger = logging.getLogger(__name__)

GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"
TupleIntegrity = Tuple[bool, str, Optional[str]]

# Key version management for rotation
AUDIT_KEY_VERSIONS: Dict[int, str] = {
    1: settings.AUDIT_LEDGER_SECRET,
}

CURRENT_KEY_VERSION = settings.AUDIT_LEDGER_KEY_VERSION

def format_timestamp_normalized(ts: Any) -> str:
    if isinstance(ts, datetime):
        return ts.strftime("%Y-%m-%d %H:%M:%S")
    return str(ts)[:19]

def get_audit_key(version: int = None) -> Tuple[bytes, int]:
    """Get the HMAC key for a specific version. Returns (key_bytes, version)."""
    version = version or CURRENT_KEY_VERSION
    key = AUDIT_KEY_VERSIONS.get(version)
    if not key:
        raise ValueError(f"Audit ledger key version {version} not found")
    return key.encode("utf-8"), version

def compute_record_hash(
    previous_hash: str,
    actor_id: str,
    action: str,
    target_id: str,
    timestamp_str: str,
    details: str,
    key_version: int = None,
    secret_key: str = None  # Deprecated: use key_version instead
) -> str:
    norm_ts = format_timestamp_normalized(timestamp_str)
    payload = f"{previous_hash}|{actor_id}|{action}|{target_id}|{norm_ts}|{details or ''}".encode("utf-8")
    
    if secret_key is not None:
        # Backward compatibility: use provided secret_key directly
        key_bytes = secret_key.encode("utf-8")
    else:
        key_bytes, _ = get_audit_key(key_version)
    
    return hmac.new(key_bytes, payload, hashlib.sha256).hexdigest()

class CryptographicAuditLedger:
    @staticmethod
    def append_entry(
        db: Session,
        actor_id: str,
        action: str,
        target_id: str,
        details: str = "",
        key_version: int = None
    ) -> AuditLog:
        key_version = key_version or CURRENT_KEY_VERSION
        
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
            key_version=key_version
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
    def verify_ledger_integrity(db: Session, key_version: int = None) -> TupleIntegrity:
        entries = db.query(AuditLog).order_by(AuditLog.timestamp.asc(), AuditLog.id.asc()).all()
        if not entries:
            return True, "Ledger is empty", None

        expected_prev_hash = GENESIS_HASH
        for entry in entries:
            if entry.previous_hash != expected_prev_hash:
                return False, f"Broken chain link at log ID {entry.id}: previous_hash mismatch", entry.id

            # Use the key version from the entry if available, otherwise default
            entry_key_version = getattr(entry, 'key_version', None) or key_version or CURRENT_KEY_VERSION
            recalculated = compute_record_hash(
                previous_hash=entry.previous_hash,
                actor_id=entry.actor_id,
                action=entry.action,
                target_id=entry.target_id,
                timestamp_str=entry.timestamp,
                details=entry.details,
                key_version=entry_key_version
            )
            if recalculated != entry.record_hash:
                return False, f"Tampered entry detected at log ID {entry.id}: payload does not match hash", entry.id

            expected_prev_hash = entry.record_hash

        return True, f"Ledger verified successfully ({len(entries)} chained blocks)", None

    @staticmethod
    def get_ledger_checkpoint(db: Session, key_version: int = None) -> Dict[str, Any]:
        key_version = key_version or CURRENT_KEY_VERSION
        latest_entry = db.query(AuditLog).order_by(AuditLog.timestamp.desc(), AuditLog.id.desc()).first()
        total_records = db.query(AuditLog).count()
        tip_hash = latest_entry.record_hash if latest_entry else GENESIS_HASH
        tip_id = latest_entry.id if latest_entry else None
        
        now_iso = datetime.now(timezone.utc).isoformat()
        checkpoint_payload = f"{tip_hash}|{tip_id}|{total_records}|{now_iso}".encode("utf-8")
        key_bytes, _ = get_audit_key(key_version)
        checkpoint_sig = hmac.new(key_bytes, checkpoint_payload, hashlib.sha256).hexdigest()

        return {
            "tip_record_hash": tip_hash,
            "tip_log_id": tip_id,
            "total_records": total_records,
            "checkpoint_timestamp": now_iso,
            "checkpoint_signature": checkpoint_sig,
            "key_version": key_version
        }

    @staticmethod
    def rotate_key(new_key: str, new_version: int = None) -> int:
        """Rotate the audit ledger HMAC key. Returns new version number."""
        global CURRENT_KEY_VERSION, AUDIT_KEY_VERSIONS
        new_version = new_version or (max(AUDIT_KEY_VERSIONS.keys()) + 1)
        AUDIT_KEY_VERSIONS[new_version] = new_key
        CURRENT_KEY_VERSION = new_version
        logger.info(f"Audit ledger key rotated to version {new_version}")
        return new_version

    @staticmethod
    def get_key_versions() -> List[int]:
        return sorted(AUDIT_KEY_VERSIONS.keys())

    @staticmethod
    def verify_with_all_keys(db: Session) -> TupleIntegrity:
        """Verify ledger trying all known key versions (for key rotation validation)."""
        for version in CryptographicAuditLedger.get_key_versions():
            is_valid, msg, broken_id = CryptographicAuditLedger.verify_ledger_integrity(db, key_version=version)
            if is_valid:
                return True, f"Ledger verified with key version {version}", None
        return False, "Ledger verification failed with all known key versions", None