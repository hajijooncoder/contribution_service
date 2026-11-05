import hashlib
import io
import os
import re
import uuid
import zipfile
import logging
from pathlib import Path
from typing import Dict, Any, Tuple
from app.config import settings

logger = logging.getLogger(__name__)

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
    clean = re.sub(r"[^\w\.\-\_\u0600-\u06FF]", "_", filename)
    clean = re.sub(r"\.{2,}", ".", clean)
    return clean[:200]

def inspect_docx_archive(file_bytes: bytes) -> Tuple[bool, str, str]:
    try:
        with zipfile.ZipFile(io.BytesIO(file_bytes), "r") as zf:
            namelist = zf.namelist()
            
            for name in namelist:
                if FORBIDDEN_ZIP_EXTENSIONS.search(name) or "vbaProject" in name.lower():
                    logger.warning(f"DOCX rejected: contains prohibited component {name}")
                    return False, "dangerous/zip-executable", f"DOCX archive contains prohibited executable or macro component: {name}"
            
            has_content_types = "[Content_Types].xml" in namelist
            has_word_doc = any(name.startswith("word/document") and name.endswith(".xml") for name in namelist)
            
            if not (has_content_types and has_word_doc):
                return False, "application/zip", "File is a generic ZIP archive and lacks valid OpenXML DOCX structure."

            return True, "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "Valid OpenXML DOCX document"
    except zipfile.BadZipFile:
        return False, "application/octet-stream", "Malformed or corrupted ZIP/DOCX archive."
    except Exception as e:
        logger.exception(f"DOCX inspection failed: {e}")
        return False, "application/octet-stream", f"DOCX inspection failure: {str(e)}"

def inspect_pdf_content(file_bytes: bytes) -> Tuple[bool, str, str]:
    if DANGEROUS_PDF_TOKENS.search(file_bytes):
        logger.warning("PDF rejected: contains active executable tokens")
        return False, "dangerous/pdf-active-content", "PDF rejected: contains active executable scripts, /OpenAction, /JavaScript, or /Launch objects."
    
    return True, "application/pdf", "Valid sanitized PDF legal document"

def inspect_magic_bytes(file_bytes: bytes) -> Tuple[bool, str, str]:
    if not file_bytes:
        return False, "application/octet-stream", "File is empty"

    header = file_bytes[:1024]

    for forbidden in FORBIDDEN_SIGNATURES:
        if header.lower().startswith(forbidden.lower()):
            logger.warning(f"File rejected: forbidden signature {forbidden!r}")
            return False, "dangerous/executable", f"File contains prohibited executable signature {forbidden!r}"

    if header.startswith(b"%PDF-"):
        return inspect_pdf_content(file_bytes)

    if header.startswith(b"PK\x03\x04"):
        return inspect_docx_archive(file_bytes)

    if header.startswith(b"{\\rtf"):
        return True, "application/rtf", "Valid RTF legal document"
    
    try:
        decoded = header[:1024].decode("utf-8")
        if "<script" in decoded.lower():
            logger.warning("Plain text file rejected: contains script tags")
            return False, "text/dangerous-html", "HTML script tags found in plain text document"
        return True, "text/plain", "Valid UTF-8 plain text legal document"
    except UnicodeDecodeError:
        pass

    return False, "application/octet-stream", "Unknown or unsupported file format signature"

class QuarantineManager:
    def __init__(self, quarantine_dir: str = settings.QUARANTINE_STORAGE_PATH):
        self.quarantine_dir = Path(quarantine_dir)
        self.quarantine_dir.mkdir(parents=True, exist_ok=True)

    def process_and_quarantine(self, file_bytes: bytes, original_filename: str) -> Dict[str, Any]:
        byte_size = len(file_bytes)
        if byte_size > settings.MAX_UPLOAD_SIZE_BYTES:
            raise ValueError(f"File size {byte_size} bytes exceeds maximum allowed {settings.MAX_UPLOAD_SIZE_BYTES}")

        if byte_size == 0:
            raise ValueError("Uploaded file is empty")

        is_safe, detected_mime, reason = inspect_magic_bytes(file_bytes)
        if not is_safe:
            raise ValueError(f"File rejected by security quarantine: {reason}")

        sha256_hash = hashlib.sha256(file_bytes).hexdigest()

        file_id = str(uuid.uuid4())
        safe_name = sanitize_filename(original_filename)
        dest_filename = f"{file_id}_{sha256_hash[:16]}_{safe_name}"
        dest_path = self.quarantine_dir / dest_filename

        with open(dest_path, "wb") as f:
            f.write(file_bytes)

        try:
            os.chmod(dest_path, 0o644)
        except OSError as e:
            logger.warning(f"Failed to set file permissions on {dest_path}: {e}")

        logger.info(f"File quarantined: id={file_id}, size={byte_size}, mime={detected_mime}, sha256={sha256_hash[:16]}...")

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