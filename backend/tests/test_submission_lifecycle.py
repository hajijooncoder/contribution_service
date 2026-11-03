import io

def test_full_submission_and_review_lifecycle(client, contributor_headers, reviewer_headers, reviewer_headers_2):
    # 1. Upload a file to quarantine
    pdf_bytes = b"%PDF-1.4 \n \xd9\x85\xd8\xa7\xd8\xaf\xd9\x87 \xdb\xb1\xdb\xb0 \xd9\x82\xd8\xa7\xd9\x86\xd9\x88\xd9\x86 \xd9\x85\xd8\xaf\xd9\x86\xdb\x8c"
    upload_resp = client.post(
        "/api/v1/contribution/upload",
        files={"file": ("madani.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        headers=contributor_headers
    )
    assert upload_resp.status_code == 200
    file_id = upload_resp.json()["file_id"]

    # 2. Submit legal contribution with official source URL and raw legal text
    legal_text = (
        "ماده ۱۰ قانون مدنی: قراردادهای خصوصی نسبت به کسانی که آن را منعقد نموده‌اند، "
        "در صورتی که مخالف صریح قانون نباشد، نافذ است. این ماده اصل حاکمیت اراده و آزادی قراردادها را بیان می‌کند."
    )
    sub_payload = {
        "source_title": "قانون مدنی مصوب ۱۳۰۷",
        "legal_document_name": "ماده ۱۰ قانون مدنی - قراردادهای خصوصی",
        "raw_legal_text": legal_text,
        "source_url": "https://rc.majlis.ir/fa/law/show/90000",
        "document_type": "law",
        "issuing_authority": "مجلس شورای اسلامی",
        "publication_info": "روزنامه رسمی کشور شماره ۱۲۳۴",
        "contributor_notes": "این ماده حاکم بر اصل آزادی اراده و قراردادهای نامعین است.",
        "file_upload_id": file_id
    }
    submit_resp = client.post(
        "/api/v1/contribution/submit",
        json=sub_payload,
        headers=contributor_headers
    )
    assert submit_resp.status_code == 201
    sub_data = submit_resp.json()
    submission_id = sub_data["id"]
    assert sub_data["status"] == "submitted"
    assert sub_data["legal_document_name"] == "ماده ۱۰ قانون مدنی - قراردادهای خصوصی"
    assert sub_data["source_domain"] == "مرکز پژوهش‌های مجلس شورای اسلامی"
    assert sub_data["quality_score"] >= 80  # Official source + long text + keywords + file
    assert sub_data["required_reviewers"] == 2  # High-risk law requires 2 independent reviews!

    # 3. Check stats (pending, credits 0 before approval)
    stats_resp = client.get("/api/v1/contribution/stats", headers=contributor_headers)
    assert stats_resp.status_code == 200
    stats = stats_resp.json()
    assert stats["total_submissions"] >= 1
    assert stats["pending_submissions"] >= 1

    # 4. Check history
    hist_resp = client.get("/api/v1/contribution/history", headers=contributor_headers)
    assert hist_resp.status_code == 200
    history = hist_resp.json()
    assert len(history) >= 1
    assert history[0]["id"] == submission_id

    # 5. Reviewer queue inspection
    # Contributor must be forbidden from reviewer queue
    forbidden_resp = client.get("/api/v1/contribution/review/pending", headers=contributor_headers)
    assert forbidden_resp.status_code == 403

    # Reviewer can view pending
    pending_resp = client.get("/api/v1/contribution/review/pending", headers=reviewer_headers)
    assert pending_resp.status_code == 200
    pending_items = pending_resp.json()
    assert any(item["id"] == submission_id for item in pending_items)

    # 6. First Reviewer votes Approve -> Quorum is 1/2, status moves to under_legal_review
    decision_1 = {
        "submission_id": submission_id,
        "decision": "approve",
        "reviewer_notes": "متن و مرجع ماده ۱۰ قانون مدنی دقیقاً مطابقت دارد و توسط داور ۱ تایید می‌شود.",
        "validation_result": "تایید انطباق حقوقی - داور ۱"
    }
    resp_vote1 = client.post(
        "/api/v1/contribution/review/decision",
        json=decision_1,
        headers=reviewer_headers
    )
    assert resp_vote1.status_code == 200
    assert resp_vote1.json()["new_status"] == "under_legal_review"

    # 7. Second Reviewer votes Approve -> Quorum achieved (2/2) -> moves to accepted!
    decision_2 = {
        "submission_id": submission_id,
        "decision": "approve",
        "reviewer_notes": "بررسی ثانویه انجام شد و بدون اشکال تایید نهایی می‌گردد.",
        "validation_result": "تایید انطباق حقوقی - داور ۲"
    }
    resp_vote2 = client.post(
        "/api/v1/contribution/review/decision",
        json=decision_2,
        headers=reviewer_headers_2
    )
    assert resp_vote2.status_code == 200
    assert resp_vote2.json()["new_status"] == "accepted"

    # 8. Check updated status and awarded credits
    status_resp = client.get(f"/api/v1/contribution/status/{submission_id}", headers=contributor_headers)
    assert status_resp.status_code == 200
    updated_sub = status_resp.json()
    assert updated_sub["status"] == "accepted"
    assert updated_sub["awarded_credits"] == updated_sub["quality_score"]
    assert updated_sub["current_approvals"] == 2
    assert updated_sub["provenance_stamp"] is not None

    # 9. Check that user's total credits were updated
    stats_after = client.get("/api/v1/contribution/stats", headers=contributor_headers).json()
    assert stats_after["contribution_credits"] >= updated_sub["awarded_credits"]

def test_unofficial_source_url_is_strictly_rejected(client, contributor_headers):
    """Verifies Fail-Closed rejection of unofficial/blog URLs."""
    invalid_payload = {
        "source_title": "قانون تجارت",
        "legal_document_name": "ماده ۳۰۰ قانون تجارت",
        "raw_legal_text": "ماده ۳۰۰ قانون تجارت در خصوص شرکتهای سهامی عام و خاص می باشد.",
        "source_url": "https://unauthorized-legal-blog.ir/article-300",
        "document_type": "law",
        "issuing_authority": "مجلس شورای اسلامی"
    }
    resp = client.post(
        "/api/v1/contribution/submit",
        json=invalid_payload,
        headers=contributor_headers
    )
    assert resp.status_code == 400
    error_detail = resp.json()["detail"]
    assert "مرجع نامعتبر است" in error_detail

def test_catalog_endpoints(client):
    auth_resp = client.get("/api/v1/contribution/catalog/authorities")
    assert auth_resp.status_code == 200
    authorities = auth_resp.json()
    assert len(authorities) > 0
    assert any("مجلس" in a["name"] for a in authorities)

    codes_resp = client.get("/api/v1/contribution/catalog/codes")
    assert codes_resp.status_code == 200
    codes = codes_resp.json()
    assert len(codes) > 0
    assert any(c["code_id"] == "CIVIL_CODE" for c in codes)
