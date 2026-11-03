# Legal Contribution Data Flow

## 1. Contributor Ingestion Flow
1. **Submission:** User enters official legal source URL and Persian legal text via the React frontend.
2. **Whitelisting:** Backend verifies domain against the official legislative/executive whitelist.
3. **Enhancement & SimHash:** Text is normalized, metadata extracted, SimHash computed, and compared against existing corpus for duplicate detection.
4. **Staging Persistence:** Validated submission is stored in the staging database with status `submitted`.
5. **Ledger Block:** Cryptographic audit entry appended to `audit_ledger.jsonl`.

## 2. Peer-Review Consensus Flow
1. **Reviewer Queue:** Independent reviewers fetch unassigned submissions.
2. **Review Execution:** Reviewers inspect source accuracy and vote (`approved` / `rejected`).
3. **Quorum Evaluation:**
   - Standard laws: Requires 1 approval.
   - High-risk documents (repeals, amendments, criminal codes): Requires 2 independent approvals.
4. **Final State:** On quorum reach, status advances to `approved`.

## 3. Owner-Controlled Pull Flow (Air-Gap)
- The owner initiates an authenticated HTTP GET request to `/api/v1/internal/export/pull` using the secret `EXPORT_GATEWAY_TOKEN`.
- The satellite returns an export bundle containing clean JSONL data and cryptographic ledger hashes.
- Once downloaded, the owner marks the batch as ingested via `/api/v1/internal/export/mark-ingested`.
- Data is moved via secure physical storage or VPN into the offline Knowledge Foundry.
