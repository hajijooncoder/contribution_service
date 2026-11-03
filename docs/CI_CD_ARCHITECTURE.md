# CI/CD Architecture & Quality Gates

## 1. Overview
The CI/CD pipeline is designed for security, maintainability, and total decoupling:
- **No Shared Pipeline with MAHOUN Core:** Workflows do not reference Core infrastructure.
- **Air-Gap Verification:** Explicit gate fails if any Core imports or Neo4j drivers are found.
- **Multi-Stage Container Builds:** Non-root runtime images for both backend and frontend.

## 2. Quality Gates
| Gate | Target | Verification Check |
| :--- | :--- | :--- |
| **Gate 1: Air-Gap Boundary** | Static Analysis | Zero `mahoun` or `neo4j` occurrences. |
| **Gate 2: Backend Reliability**| Pytest | All 161 hardcore unit and adversarial tests pass. |
| **Gate 3: Frontend Quality** | TypeScript & Vite | Strict typechecking and production build. |
| **Gate 4: Container Security** | Docker | Independent multi-stage builds with non-root user. |
| **Gate 5: Secret Audit** | Scan | No private keys, database dumps, or unencrypted tokens. |

## 3. Workflows
- `.github/workflows/ci.yml`: Runs on PRs and pushes to `main`/`develop`.
- `.github/workflows/security.yml`: Runs dependency audits and secret scanning.
- `.github/workflows/docker.yml`: Builds Docker images independently.
- `.github/workflows/release.yml`: Prepares controlled releases on git tags (`v*.*.*`).
