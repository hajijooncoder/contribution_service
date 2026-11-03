# Security Boundaries & Air-Gap Principles

## 1. Zero Direct Network Route
The Contribution Platform is intentionally engineered with **zero network routes** into the protected MAHOUN Core runtime or Knowledge Foundry:
- No database connections to Neo4j.
- No direct RPC or HTTP calls into MAHOUN Core engines.
- No shared memory or process spaces.

## 2. Strictly Forbidden Components
The following proprietary assets are permanently prohibited from this repository:
- `mahoun/` core Python packages.
- Neo4j graph schemas, drivers, and graph query services.
- Five-layer Iranian legal ontology definitions and compilation tools.
- Evidence-linked verdict engines and Ultra NLI verifiers.
- Machine learning weights, transformers, and training checkpoints.

## 3. Threat Model & Mitigations
| Threat Vector | Mitigation Strategy |
| :--- | :--- |
| **Malicious File Uploads** | Multi-layer quarantine manager: MIME sniffing, extension whitelist, path traversal defense, and isolated storage outside public web roots. |
| **Sybil Attack / Self-Review** | Strict conflict-of-interest check: contributors are cryptographically prevented from reviewing their own submissions (`reviewer_id != author_id`). |
| **Ledger Tampering** | Cryptographic HMAC-SHA256 hash-chaining where modifying any historical record invalidates the entire audit chain. |
| **DDoS / Flooding** | Dual sliding-window in-memory rate limiter per IP address and per user ID. |
| **Privilege Escalation** | Registration endpoints strictly forbid setting roles; only authenticated administrators can promote roles. |
