# API Contracts & Endpoint Specifications

All endpoints are versioned under `/api/v1`.

## Authentication (`/api/v1/auth`)
- `POST /register`: Register a new contributor. Forbids assigning custom roles or MCC credits.
- `POST /token`: OAuth2 password request returning JWT access token.
- `GET /me`: Get authenticated user profile and MCC balance.
- `POST /admin/promote`: Admin promotion of users to reviewer/expert roles.

## Contributions (`/api/v1/contributions`)
- `POST /submit`: Basic legal submission.
- `POST /submit/enhanced`: Submission with automated text enhancement preview and duplicate detection.
- `POST /upload`: Secure multi-part document upload into isolated quarantine.
- `GET /history`: Contributor submission history.
- `GET /catalog/authorities`: Official catalog of issuing authorities.
- `GET /catalog/codes`: Canonical reference list of legal codes.

## Peer Review (`/api/v1/reviews`)
- `GET /queue`: Get pending submissions awaiting peer review.
- `POST /{submission_id}`: Submit review decision (`approved` / `rejected`).
- `GET /stats`: Reviewer throughput and platform statistics.

## Owner Export Gateway (`/api/v1/internal/export`)
- `GET /pull`: Fetch validated submissions in JSONL format (Requires `X-Export-Token` header).
- `POST /mark-ingested`: Mark extracted batch as consumed.
- `GET /ledger-audit`: Export audit ledger for tamper verification.
- `GET /quarantine/{file_id}`: Download quarantined raw evidence file.
