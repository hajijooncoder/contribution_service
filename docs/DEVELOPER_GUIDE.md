# MAHOUN Legal Contribution Platform — Developer & Architecture Guide
## High-Security Staging Isolation, Quorum FSM, Cryptographic Audit & Owner Export Gateway

---

### 1. Architectural Philosophy & Strict Air-Gap Invariant

The `contribution_service` operates as a zero-trust staging environment for legal intelligence ingestion. 

```
                                      AIR-GAP BOUNDARY
   [ Public Internet ]                        |                [ Core Kernel ]
   Contributors & Reviewers                   |
           │                                  |
           ▼                                  |
   ┌───────────────────────────────────┐      |
   │      contribution_service         │      |
   │  ┌─────────────────────────────┐  │      |
   │  │   Quarantine Isolator       │  │      |
   │  │   SHA-256 Byte Verification │  │      |
   │  └──────────────┬──────────────┘  │      |
   │                 ▼                 │      |
   │  ┌─────────────────────────────┐  │      |
   │  │    Quorum FSM Consensus     │  │      |
   │  │   (1-3 Reviewer Quorum)     │  │      |
   │  └──────────────┬──────────────┘  │      |
   │                 ▼                 │      |
   │  ┌─────────────────────────────┐  │      |
   │  │ Cryptographic Audit Ledger  │  │      |
   │  └──────────────┬──────────────┘  │      |
   │                 ▼                 │      |
   │  ┌─────────────────────────────┐  │      |
   │  │   Owner Export Gateway      │  │  MANUAL DOWNLOAD   ┌─────────────────────┐
   │  │  HMAC dataset.jsonl Export  │──┼───────────────────►│     KingMahouN      │
   │  └─────────────────────────────┘  │  (Haji Mamad only) │ Core Knowledge Graph│
   └───────────────────────────────────┘      |             └─────────────────────┘
                                              |
```

> [!CAUTION]
> **Zero Automated Pipeline Invariant:**
> Under no circumstances may `contribution_service` open network connections, webhooks, or automated synchronization pipelines with `KingMahouN`. The only sanctioned route of data transition into the core knowledge base is through the **Owner Export Gateway**, which produces an authenticated, tamper-evident `dataset.jsonl` file strictly on-demand for manual review and ingestion by Haji Mamad.

---

### 2. Core Subsystems

#### 2.1 Quarantine Isolation Engine (`app/core/quarantine.py`)
- Isolates incoming uploads on disk with restricted read-only permissions (`0o644`).
- Computes SHA-256 byte-level digests directly from the incoming binary streams.
- Validates MIME signatures (`application/pdf`, `text/plain`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document`).
- Rejects executable formats, binary scripts, or files exceeding max size limits (15 MB).

#### 2.2 Quorum Finite State Machine (`app/core/fsm_quorum.py`)
State transitions are deterministic and strictly enforced:
- **`submitted`**: Document received, sanitized, and placed into staging quarantine.
- **`under_validation`**: Automated checks completed (SimHash duplicate detection, authority validation).
- **`under_legal_review`**: Placed into reviewer pool. Required approvals calculated:
  $$\text{Required Approvals} = \begin{cases} 1 & \text{if Risk is LOW} \\ 2 & \text{if Risk is MEDIUM} \\ 3 & \text{if Risk is HIGH or Overlap } > 70\% \end{cases}$$
- **`accepted`**: Current approvals reach required threshold ($\ge \text{required\_reviewers}$). Credits awarded to contributor.
- **`rejected`**: Quorum rejected with documented auditor explanation.

#### 2.3 Cryptographic Audit Ledger (`app/core/audit_ledger.py`)
- Modeled after a hash-chained ledger:
  $$\text{Block Hash} = \text{HMAC-SHA256}(\text{SecretKey}, \text{prev\_hash} \parallel \text{actor\_id} \parallel \text{action} \parallel \text{timestamp} \parallel \text{target\_id})$$
- Prevents post-hoc record manipulation or repudiation.
- Persisted in table `staging_audit_ledger`.

#### 2.4 Duplicate Detection & Fingerprinting (`app/core/duplicate_detector.py`)
1. **Exact Duplicate Detection:** Direct comparison of `content_hash = SHA256(normalized_text)`.
2. **Near-Duplicate Detection:** 64-bit SimHash algorithm. Computes Hamming distance between SimHash fingerprints:
   $$\text{HammingDistance}(H_1, H_2) \le 3 \implies \text{Near Duplicate ($>85\%$ semantic equivalence)}$$

#### 2.5 Real-Time WebSocket Infrastructure (`app/websocket/manager.py`)
- Thread-safe `ConnectionManager` maintains active client WebSockets keyed by authenticated `user_id`.
- Auto-pings heartbeat every 30 seconds to maintain connection through proxies.
- Reviewer actions trigger instant asynchronous notifications:
  ```json
  {
    "type": "REVIEW_DECISION",
    "submission_id": "...",
    "status": "accepted",
    "awarded_credits": 25,
    "message": "مشارکت شما توسط داوران همتا تأیید شد."
  }
  ```

#### 2.6 Owner Export Gateway (`app/api/v1/internal_export.py`)
- Protected by `X-Gateway-Token` HTTP header matching `settings.EXPORT_GATEWAY_TOKEN`.
- Queries all approved (`status == 'accepted'`) submissions.
- Emits newline-delimited JSON (`dataset.jsonl`) adhering to KingMahouN's `CanonicalIngestionBatch` specification:
  ```json
  {
    "document_id": "MHN-2026-0042",
    "title": "قانون تجارت الکترونیکی",
    "authority": "مجلس شورای اسلامی",
    "document_type": "law",
    "source_url": "https://rc.majlis.ir/fa/law/show/1",
    "source_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "raw_text": "...",
    "spans": [
      {
        "start": 0,
        "end": 128,
        "text_hash": "a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e"
      }
    ],
    "export_timestamp": "2026-11-05T02:00:00Z",
    "hmac_signature": "..."
  }
  ```

---

### 3. Database Schema Overview

The database resides in SQLite (or PostgreSQL in production):
- **`staging_users`**: User identities, roles (`contributor`, `reviewer`, `admin`), active status, credit balances.
- **`staging_submissions`**: The primary entity holding title, raw legal text, URLs, quality score, quorum state, and hash fingerprints.
- **`staging_uploaded_files`**: Physical file records quarantined with SHA-256 hashes.
- **`staging_reviews`**: Reviewer decisions, scores, and rationales.
- **`staging_audit_ledger`**: Append-only cryptographic trail.

---

### 4. Code Quality & Invariant Rules

1. **Zero Warning Mandate:**
   All builds and test runs must produce `0` warnings. Deprecated calls (such as naive `datetime.utcnow()`) are forbidden in favor of `datetime.now(timezone.utc)`.
2. **Persian Typography Compliance:**
   Legal text normalization must enforce `\u200c` (ZWNJ / نیم‌فاصله) preservation and prevent character mutilation.
3. **No Direct Production Database Access:**
   Under no circumstance should staging code communicate with production database credentials.
