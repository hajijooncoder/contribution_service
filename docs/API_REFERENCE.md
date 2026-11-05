# MAHOUN Legal Contribution Platform — API Reference
## OpenAPI v3.1 / REST & WebSocket Specifications

All API endpoints are prefixed with `/api/v1` unless noted otherwise.

---

### Table of Contents
1. [Authentication (`/auth`)](#1-authentication-auth)
2. [Contribution & Staging (`/contribution`)](#2-contribution--staging-contribution)
3. [Peer Review Workspace (`/contribution/review`)](#3-peer-review-workspace-contributionreview)
4. [Administration Panel (`/admin`)](#4-administration-panel-admin)
5. [Owner Export Gateway (`/internal/export`)](#5-owner-export-gateway-internalexport)
6. [Real-time WebSocket Push (`/ws`)](#6-real-time-websocket-push-ws)

---

### 1. Authentication (`/auth`)

#### `POST /api/v1/auth/login`
Authenticates a user and issues an HMAC-signed JWT bearer token.
- **Headers:** `Content-Type: application/x-www-form-urlencoded`
- **Request Body:**
  - `username` (string, required): User email address.
  - `password` (string, required): User password.
- **Responses:**
  - `200 OK`:
    ```json
    {
      "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "token_type": "bearer",
      "user": {
        "id": "uuid-v4",
        "email": "contributor@example.com",
        "full_name": "نام کاربر",
        "role": "contributor",
        "total_credits": 150
      }
    }
    ```
  - `401 Unauthorized`: Invalid credentials.

#### `GET /api/v1/auth/me`
Retrieves current authenticated profile.
- **Headers:** `Authorization: Bearer <token>`
- **Responses:**
  - `200 OK`: `UserProfile` object.
  - `401 Unauthorized`: Missing or invalid token.

---

### 2. Contribution & Staging (`/contribution`)

#### `POST /api/v1/contribution/validate-url`
Performs real-time validation of official Iranian legal source URLs.
- **Request Body:**
  ```json
  { "url": "https://rc.majlis.ir/fa/law/show/132456" }
  ```
- **Responses:**
  - `200 OK`:
    ```json
    {
      "valid": true,
      "authority": "مرکز پژوهش‌های مجلس شورای اسلامی",
      "error": null
    }
    ```
  - `200 OK` (when invalid domain):
    ```json
    {
      "valid": false,
      "authority": null,
      "error": "دامنه منبع در لیست پایگاه‌های رسمی حقوقی کشور قرار ندارد."
    }
    ```

#### `POST /api/v1/contribution/upload`
Uploads a physical document directly into quarantine isolation.
- **Headers:** `Content-Type: multipart/form-data`
- **Form Data:** `file` (binary PDF/DOCX/TXT)
- **Responses:**
  - `200 OK`:
    ```json
    { "file_id": "quarantine-uuid-v4" }
    ```
  - `400 Bad Request`: Prohibited MIME type or corrupt payload.
  - `429 Too Many Requests`: Rate limiter triggered.

#### `POST /api/v1/contribution/submit/enhanced`
Main submission pipeline with auto-enhancement and duplicate preview.
- **Request Body:**
  ```json
  {
    "source_title": "قانون تجارت الکترونیکی",
    "legal_document_name": "قانون تجارت الکترونیکی مصوب ۱۳۸۲",
    "raw_legal_text": "ماده ۱: این قانون دربرگیرنده...",
    "source_url": "https://rc.majlis.ir/fa/law/show/1",
    "document_type": "law",
    "issuing_authority": "مجلس شورای اسلامی",
    "publication_info": "روزنامه رسمی شماره ۱۷۱۵۳",
    "contributor_notes": "ثبت اولیه با رعایت نیم‌فاصله‌ها",
    "skip_enhancement": false,
    "force_submit": false
  }
  ```
- **Responses:**
  - `200 OK` (Preview / Duplicate detected):
    ```json
    {
      "status": "preview",
      "submission_id": null,
      "enhanced_preview": {
        "original_length": 1500,
        "enhanced_length": 1495,
        "changes_count": 8,
        "metadata": {
          "article_count": 5,
          "note_count": 2,
          "risk_level": "LOW"
        },
        "quality_score": 92.5,
        "fingerprint": "1a2b3c4d5e6f7a8b",
        "content_hash": "e3b0c442..."
      },
      "message": "پیش‌نمایش ارتقای متن با موفقیت آماده شد."
    }
    ```

#### `POST /api/v1/contribution/submit`
Direct submission endpoint entering the staging FSM.
- **Responses:** `201 Created` with full `ContributionSubmissionOut`.

#### `GET /api/v1/contribution/stats`
Aggregated platform metrics and user credits.
- **Responses:**
  - `200 OK`:
    ```json
    {
      "total_submissions": 142,
      "pending_submissions": 12,
      "accepted_submissions": 118,
      "rejected_submissions": 12,
      "contribution_credits": 3450
    }
    ```

#### `GET /api/v1/contribution/recent-activity?limit=5`
Returns authenticated user's recent contribution activities for real-time dashboard progress.

#### `GET /api/v1/contribution/history`
Returns strictly authenticated user's submitted documents.

#### `GET /api/v1/contribution/search`
Advanced search and filtering across the platform.
- **Query Parameters:**
  - `q` (string, optional): Full-text query.
  - `document_type` (string, optional): `law`, `regulation`, `judicial_ruling`, etc.
  - `issuing_authority` (string, optional): Authority name substring.
  - `status_filter` (string, optional): `submitted`, `under_legal_review`, `accepted`, `rejected`.
  - `skip` (integer, default `0`): Pagination offset.
  - `limit` (integer, default `20`, max `100`): Page size.
- **Responses:**
  - `200 OK`:
    ```json
    {
      "items": [
        {
          "id": "uuid-v4",
          "date": "2026-11-05",
          "legal_document_name": "قانون تجارت الکترونیکی",
          "source_title": "مرکز پژوهش‌ها",
          "document_type": "law",
          "issuing_authority": "مجلس شورای اسلامی",
          "status": "accepted",
          "quality_score": 95,
          "awarded_credits": 25,
          "submitter_id": "user-uuid"
        }
      ],
      "total": 1,
      "skip": 0,
      "limit": 20
    }
    ```

#### `GET /api/v1/contribution/status/{submission_id}`
Returns details for a specific submission with IDOR protection.

---

### 3. Peer Review Workspace (`/contribution/review`)

#### `GET /api/v1/contribution/review/pending`
Lists submissions awaiting peer consensus (restricted to `reviewer` and `admin`).

#### `POST /api/v1/contribution/review/decision`
Submits a review decision.
- **Request Body:**
  ```json
  {
    "submission_id": "uuid-v4",
    "decision": "approve",
    "reviewer_notes": "انطباق با متن روزنامه رسمی احراز گردید."
  }
  ```
- **Responses:**
  - `200 OK`: Updated quorum state, current approvals, and audit block hash.

---

### 4. Administration Panel (`/admin`)

Requires `role: admin`.

- `GET /api/v1/admin/users`: List users with role & active filters.
- `PUT /api/v1/admin/users/{id}/activate`: Toggle account activation.
- `PUT /api/v1/admin/users/{id}/role`: Update role (`contributor`, `reviewer`, `admin`).
- `GET /api/v1/admin/stats/overview`: Global system counters and credit statistics.
- `GET /api/v1/admin/export/overview`: Export readiness status and isolation metrics.

---

### 5. Owner Export Gateway (`/internal/export`)

#### `GET /api/v1/internal/export/dataset.jsonl`
Protected endpoint for Haji Mamad's personal data extraction.
- **Headers:** `X-Gateway-Token: <EXPORT_GATEWAY_TOKEN>`
- **Response:** `200 OK` with `Content-Type: application/x-ndjson; charset=utf-8` and `Content-Disposition: attachment; filename=dataset.jsonl`.
- **401 Unauthorized**: Invalid or missing gateway token.

---

### 6. Real-time WebSocket Push (`/ws`)

#### `WS /api/v1/ws/{user_id}?token={jwt_token}`
Maintains live, bidirectional push channel for instantaneous status updates.
- **Server Events:**
  - `NOTIFICATION`:
    ```json
    {
      "type": "NOTIFICATION",
      "title": "وضعیت مشارکت به‌روزرسانی شد",
      "message": "مشارکت شما توسط داور همتا تأیید گردید.",
      "timestamp": "2026-11-05T02:00:00Z"
    }
    ```
