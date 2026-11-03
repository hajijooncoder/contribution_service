import io
import hashlib
import json

def test_export_pull_gateway_unauthorized(client):
    resp = client.get("/api/v1/internal/export/approved-packages")
    assert resp.status_code == 403

def test_export_pull_gateway_authorized_flow(client, contributor_headers, reviewer_headers, reviewer_headers_2):
    gateway_headers = {"X-Gateway-Token": "test-export-gateway-token"}

    # 1. Upload and create an approved submission with official source and raw legal text
    pdf_bytes = b"%PDF-1.4 \n \xd9\x85\xd8\xa7\xd8\xaf\xd9\x87 \xdb\xb1\xdb\xb1\xdb\xb0\xdb\xb2 \xd9\x82\xd8\xa7\xd9\x86\xd9\x88\xd9\x86 \xd9\x85\xd8\xaf\xd9\x86\xdb\x8c"
    file_sha256 = hashlib.sha256(pdf_bytes).hexdigest()
    
    upload_resp = client.post(
        "/api/v1/contribution/upload",
        files={"file": ("madani_1102.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        headers=contributor_headers
    )
    file_id = upload_resp.json()["file_id"]

    sub_payload = {
        "source_title": "قانون مدنی - حقوق خانواده",
        "legal_document_name": "ماده ۱۱۰۲ قانون مدنی - روابط زوجین",
        "raw_legal_text": "همین که نکاح به طور صحت واقع شد روابط زوجیت بین طرفین موجود و حقوق و تکالیف زوجین در مقابل همدیگر برقرار می‌شود.",
        "source_url": "https://rc.majlis.ir/fa/law/show/90001",
        "document_type": "law",
        "issuing_authority": "مجلس شورای اسلامی",
        "file_upload_id": file_id
    }
    submit_resp = client.post("/api/v1/contribution/submit", json=sub_payload, headers=contributor_headers)
    assert submit_resp.status_code == 201
    submission_id = submit_resp.json()["id"]

    # Quorum: Approve by Reviewer 1 and Reviewer 2
    client.post(
        "/api/v1/contribution/review/decision",
        json={"submission_id": submission_id, "decision": "approve"},
        headers=reviewer_headers
    )
    client.post(
        "/api/v1/contribution/review/decision",
        json={"submission_id": submission_id, "decision": "approve"},
        headers=reviewer_headers_2
    )

    # 2. Secure Core pulls approved packages
    export_resp = client.get("/api/v1/internal/export/approved-packages", headers=gateway_headers)
    assert export_resp.status_code == 200
    export_data = export_resp.json()
    assert export_data["count"] >= 1
    assert "ledger_checkpoint" in export_data
    assert export_data["ledger_checkpoint"]["tip_record_hash"] is not None
    
    # Verify dedicated ledger checkpoint endpoint
    checkpoint_resp = client.get("/api/v1/internal/export/ledger-checkpoint", headers=gateway_headers)
    assert checkpoint_resp.status_code == 200
    assert "checkpoint_signature" in checkpoint_resp.json()
    
    pulled_pkg = next(p for p in export_data["packages"] if p["manifest"]["submission_id"] == submission_id)
    assert pulled_pkg["manifest"]["legal_document_name"] == "ماده ۱۱۰۲ قانون مدنی - روابط زوجین"
    assert pulled_pkg["manifest"]["file"]["sha256_hash"] == file_sha256
    assert "همین که نکاح به طور صحت واقع شد" in pulled_pkg["manifest"]["raw_legal_text"]
    assert "staging_transit_sha256" in pulled_pkg

    # 3. Test clean text exports (JSONL & TXT datasets for manual inspection / batch ingestion)
    jsonl_resp = client.get("/api/v1/internal/export/dataset.jsonl", headers=gateway_headers)
    assert jsonl_resp.status_code == 200
    jsonl_lines = jsonl_resp.text.strip().split("\n")
    assert len(jsonl_lines) >= 1
    first_record = json.loads(jsonl_lines[0])
    assert "title" in first_record
    assert "raw_text" in first_record
    assert "source_domain" in first_record

    txt_resp = client.get("/api/v1/internal/export/dataset.txt", headers=gateway_headers)
    assert txt_resp.status_code == 200
    assert "سند شماره:" in txt_resp.text
    assert "ماده ۱۱۰۲ قانون مدنی" in txt_resp.text

    # 4. Secure Core pulls the quarantined file bytes
    file_download_resp = client.get(
        f"/api/v1/internal/export/package-file/{file_id}",
        headers=gateway_headers
    )
    assert file_download_resp.status_code == 200
    assert file_download_resp.headers["x-content-sha256"] == file_sha256
    assert file_download_resp.content == pdf_bytes

    # 5. Secure Core marks the package as ingested
    ack_resp = client.post(
        f"/api/v1/internal/export/mark-ingested/{submission_id}",
        headers=gateway_headers
    )
    assert ack_resp.status_code == 200
    assert ack_resp.json()["new_status"] == "in_processing"

    # Status check confirms state transition
    status_resp = client.get(f"/api/v1/contribution/status/{submission_id}", headers=contributor_headers)
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] == "in_processing"
