import hashlib
import io
import os
import re
import uuid
import zipfile
from pathlib import Path
from typing import Dict, Any, Tuple
from app.config import settings

FORBIDDEN_SIGNATURES = [
    b"MZ",            # DOS/Windows PE Executable
    b"\x7fELF",       # Linux ELF Binary
    b"#!",            # Shell script
    b"<script",       # Disguised HTML/JS
    b"<?php",         # Disguised PHP
]

FORBIDDEN_ZIP_EXTENSIONS = re.compile(
    r"\.(exe|bat|cmd|sh|bin|elf|py|js|vbs|ps1|msi|jar|com|dll|so|dylib)$",
    re.IGNORECASE
)

DANGEROUS_PDF_TOKENS = re.compile(
    rb"/(?:Launch|JavaScript|JS|OpenAction|EmbeddedFiles|SubmitForm|ImportData|RichMedia)\b"
)

def sanitize_filename(filename: str) -> str:
    """Safely sanitize filename preserving basic legal document naming."""
    clean = re.sub(r"[^\w\.\-\_\u0600-\u06FF]", "_", filename)
    clean = re.sub(r"\.{2,}", ".", clean)
    return clean[:200]

def inspect_docx_archive(file_bytes: bytes) -> Tuple[bool, str, str]:
    """
    Performs deep inspection of OpenXML DOCX packages to prevent zip spoofing,
    macro injection, and embedded script execution.
    """
    try:
        with zipfile.ZipFile(io.BytesIO(file_bytes), "r") as zf:
            namelist = zf.namelist()
            
            # Check for embedded executable/script binaries or macros
            for name in namelist:
                if FORBIDDEN_ZIP_EXTENSIONS.search(name) or "vbaProject" in name.lower():
                    return False, "dangerous/zip-executable", f"DOCX archive contains prohibited executable or macro component: {name}"
            
            # Must possess standard OpenXML structure
            has_content_types = "[Content_Types].xml" in namelist
            has_word_doc = any(name.startswith("word/document") and name.endswith(".xml") for name in namelist)
            
            if not (has_content_types and has_word_doc):
                return False, "application/zip", "File is a generic ZIP archive and lacks valid OpenXML DOCX structure ([Content_Types].xml, word/document.xml)."

            return True, "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "Valid OpenXML DOCX document"
    except zipfile.BadZipFile:
        return False, "application/octet-stream", "Malformed or corrupted ZIP/DOCX archive."
    except Exception as e:
        return False, "application/octet-stream", f"DOCX inspection failure: {str(e)}"

def inspect_pdf_content(file_bytes: bytes) -> Tuple[bool, str, str]:
    """
    Scans PDF byte stream for active executable actions, scripts, or embedded objects.
    """
    # Check for active execution tokens
    if DANGEROUS_PDF_TOKENS.search(file_bytes):
        return False, "dangerous/pdf-active-content", "PDF rejected: contains active executable scripts, /OpenAction, /JavaScript, or /Launch objects."
    
    return True, "application/pdf", "Valid sanitized PDF legal document"

def inspect_magic_bytes(file_bytes: bytes) -> Tuple[bool, str, str]:
    """
    Inspects magic bytes and payload content to detect authentic file format.
    Returns: (is_safe, detected_mime, reason)
    """
    if not file_bytes:
        return False, "application/octet-stream", "File is empty"

    header = file_bytes[:1024]

    # Check for explicitly forbidden binary/script signatures
    for forbidden in FORBIDDEN_SIGNATURES:
        if header.lower().startswith(forbidden.lower()):
            return False, "dangerous/executable", f"File contains prohibited executable signature {forbidden!r}"

    # 1. PDF Deep Verification
    if header.startswith(b"%PDF-"):
        return inspect_pdf_content(file_bytes)

    # 2. OpenXML DOCX Deep Verification
    if header.startswith(b"PK\x03\x04"):
        return inspect_docx_archive(file_bytes)

    # 3. RTF Document
    if header.startswith(b"{\\rtf"):
        return True, "application/rtf", "Valid RTF legal document"
    
    # 4. Clean UTF-8 Plain Text
    try:
        decoded = header[:1024].decode("utf-8")
        if "<script" in decoded.lower():
            return False, "text/dangerous-html", "HTML script tags found in plain text document"
        return True, "text/plain", "Valid UTF-8 plain text legal document"
    except UnicodeDecodeError:
        pass

    return False, "application/octet-stream", "Unknown or unsupported file format signature"

class QuarantineManager:
    """
    Manages quarantine isolation for uploaded legal documents.
    Preserves exact byte-for-byte authenticity while calculating SHA-256
    and isolating files away from execution paths.
    """

    def __init__(self, quarantine_dir: str = settings.QUARANTINE_STORAGE_PATH):
        self.quarantine_dir = Path(quarantine_dir)
        self.quarantine_dir.mkdir(parents=True, exist_ok=True)

    def process_and_quarantine(self, file_bytes: bytes, original_filename: str) -> Dict[str, Any]:
        """
        Processes uploaded raw bytes, verifies magic bytes, calculates SHA-256,
        and saves raw bytes to quarantine storage.
        """
        byte_size = len(file_bytes)
        if byte_size > settings.MAX_UPLOAD_SIZE_BYTES:
            raise ValueError(f"File size {byte_size} bytes exceeds maximum allowed {settings.MAX_UPLOAD_SIZE_BYTES}")

        if byte_size == 0:
            raise ValueError("Uploaded file is empty")

        # 1. Magic bytes & deep security inspection
        is_safe, detected_mime, reason = inspect_magic_bytes(file_bytes)
        if not is_safe:
            raise ValueError(f"File rejected by security quarantine: {reason}")

        # 2. SHA-256 cryptographic hashing (unaltered bytes)
        sha256_hash = hashlib.sha256(file_bytes).hexdigest()

        # 3. Secure storage path
        file_id = str(uuid.uuid4())
        safe_name = sanitize_filename(original_filename)
        dest_filename = f"{file_id}_{sha256_hash[:16]}_{safe_name}"
        dest_path = self.quarantine_dir / dest_filename

        # 4. Write exact unaltered bytes to quarantine
        with open(dest_path, "wb") as f:
            f.write(file_bytes)

        # Set restrictive permissions (read-only for owner/group, no execution)
        try:
            os.chmod(dest_path, 0o644)
        except OSError:
            pass

        return {
            "file_id": file_id,
            "original_filename": original_filename,
            "stored_filename": dest_filename,
            "storage_path": str(dest_path),
            "file_size": byte_size,
            "sha256_hash": sha256_hash,
            "detected_mime": detected_mime,
            "quarantine_status": "quarantined_verified",
        }
