import hashlib
import io
from app.core.quarantine import QuarantineManager

def test_quarantine_pdf_file():
    pdf_content = b"%PDF-1.4 Mock Legal Document Content \n \xd8\xa7\xdb\x8c\xd9\x86 \xdb\x8c\xda\xa9 \xd9\x85\xd8\xaa\xd9\x86 \xd8\xad\xd9\x82\xd9\x88\xd9\x82\xdb\x8c \xd8\xa7\xd8\xb3\xd8\xaa."
    expected_sha256 = hashlib.sha256(pdf_content).hexdigest()
    
    mgr = QuarantineManager()
    res = mgr.process_and_quarantine(pdf_content, "qanoon_madani.pdf")
    
    assert res["sha256_hash"] == expected_sha256
    assert res["detected_mime"] == "application/pdf"
    assert res["file_size"] == len(pdf_content)
    
    # Verify bit-for-bit byte preservation
    with open(res["storage_path"], "rb") as f:
        stored_bytes = f.read()
    assert stored_bytes == pdf_content

def test_quarantine_rejects_executable():
    exe_content = b"MZ\x90\x00\x03\x00\x00\x00FakeWindowsExe"
    mgr = QuarantineManager()
    try:
        mgr.process_and_quarantine(exe_content, "malicious.pdf")
        assert False, "Should have rejected executable payload"
    except ValueError as e:
        assert "executable" in str(e).lower()

def test_quarantine_rejects_shell_script():
    script_content = b"#!/bin/bash\nrm -rf /"
    mgr = QuarantineManager()
    try:
        mgr.process_and_quarantine(script_content, "script.txt")
        assert False, "Should have rejected script"
    except ValueError as e:
        assert "prohibited" in str(e).lower()

def test_quarantine_rejects_html_script():
    html_content = b"<script>fetch('http://evil.com')</script>"
    mgr = QuarantineManager()
    try:
        mgr.process_and_quarantine(html_content, "attack.txt")
        assert False, "Should have rejected script"
    except ValueError as e:
        assert "script" in str(e).lower()

def test_upload_api_endpoint(client, contributor_headers):
    dummy_pdf = b"%PDF-1.5 \n Article 10 Civil Code: Freedom of contract."
    response = client.post(
        "/api/v1/contribution/upload",
        files={"file": ("madani_art10.pdf", io.BytesIO(dummy_pdf), "application/pdf")},
        headers=contributor_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "file_id" in data

def test_quarantine_rejects_malicious_pdf_with_active_objects():
    """
    HIGH SEVERITY ADVERSARIAL TEST: An attacker uploads a PDF containing active
    embedded scripts or /OpenAction execution tags. Quarantine must strictly reject it.
    """
    malicious_pdf = (
        b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R /OpenAction 3 0 R >>\nendobj\n"
        b"3 0 obj\n<< /Type /Action /S /JavaScript /JS (app.alert(1)) >>\nendobj\n"
        b"trailer\n<< /Root 1 0 R >>\n%%EOF"
    )
    mgr = QuarantineManager()
    try:
        mgr.process_and_quarantine(malicious_pdf, "exploit.pdf")
        assert False, "Should have rejected active script PDF payload"
    except ValueError as e:
        assert "active executable" in str(e).lower() or "rejected" in str(e).lower()

def test_quarantine_rejects_fake_docx_zip_archive():
    """
    HIGH SEVERITY ADVERSARIAL TEST: An attacker uploads an arbitrary zip archive
    containing a shell script named 'document.docx'. Quarantine must inspect
    the archive members and reject it.
    """
    import zipfile
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("malicious.sh", "#!/bin/bash\necho pwned\n")
    fake_docx_bytes = buf.getvalue()

    mgr = QuarantineManager()
    try:
        mgr.process_and_quarantine(fake_docx_bytes, "malicious.docx")
        assert False, "Should have rejected generic ZIP masquerading as DOCX"
    except ValueError as e:
        assert "prohibited executable" in str(e).lower() or "zip archive" in str(e).lower()

def test_quarantine_accepts_valid_openxml_docx():
    """
    Verifies authentic OpenXML DOCX archive structure is correctly accepted.
    """
    import zipfile
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("[Content_Types].xml", '<?xml version="1.0"?><Types></Types>')
        zf.writestr("word/document.xml", '<?xml version="1.0"?><w:document></w:document>')
    valid_docx_bytes = buf.getvalue()

    mgr = QuarantineManager()
    res = mgr.process_and_quarantine(valid_docx_bytes, "authentic_law.docx")
    assert res["detected_mime"] == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    assert res["file_size"] == len(valid_docx_bytes)
