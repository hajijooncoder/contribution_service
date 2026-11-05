# MAHOUN Legal Contribution Platform — Testing & Verification Guide
## Continuous Quality Assurance: Backend Pytest, Frontend Vitest, and Playwright E2E

---

### 1. Quality Standards & Invariants

Every code contribution must comply with the three strict invariants:
1. **100% Green Test Suite:** Zero test failures across backend and frontend.
2. **Zero Warnings Policy:** Zero runtime, deprecation, or framework warnings.
3. **Air-Gap Verification:** Zero outbound network calls to `KingMahouN`.

---

### 2. Backend Test Suite (Pytest)

The backend features over **305 comprehensive tests** covering the quarantine isolator, scoring engine, FSM quorum consensus, cryptographic audit ledger, search filters, and WebSocket push channels.

#### Running Backend Tests
From the project root:
```bash
# Run all backend tests cleanly
pytest backend/ -q

# Run with full verbose output
pytest backend/ -v

# Run a specific test suite
pytest backend/tests/test_search.py -v
pytest backend/tests/test_admin.py -v
pytest backend/tests/test_websocket.py -v
pytest backend/tests/test_validate_url.py -v
```

#### Test Configuration (`backend/pytest.ini`)
- Configured with `testpaths = tests`.
- Filtered for third-party deprecations (e.g., `passlib` crypt/bcrypt and Starlette `TestClient` transport warnings).

---

### 3. Frontend Test Suite (Vitest)

The frontend test suite features **91 tests across 8 test suites**, rigorously validating React components, UI state management, API contracts, real-time URL validation, and WebSocket hooks.

#### Running Frontend Tests
From the project root:
```bash
# Run all frontend tests in single-run mode
npm --prefix frontend test -- --run

# Run specific component test file
npm --prefix frontend test -- src/components/ContributionHistory.test.tsx
npm --prefix frontend test -- src/components/ContributionForm.test.tsx
npm --prefix frontend test -- src/components/AdminPanel.test.tsx
```

#### Test Suites Summary:
1. `src/components/ContributionForm.test.tsx` (URL validation debounce, verified badges).
2. `src/components/ContributionHistory.test.tsx` (Search bar, multi-select filters, clear filters).
3. `src/components/DashboardPage.test.tsx` (Stats cards, 5-step pipeline, 6-step proof panel).
4. `src/components/AdminPanel.test.tsx` (User management, system stats, Owner Export Gateway).
5. `src/components/components.brutal.test.tsx` (Full component interaction and boundary checks).
6. `src/hooks/useWebSocket.test.ts` (Auto-reconnect, token authentication, message dispatch).
7. `src/api/client.contract.test.ts` (Type contracts and HTTP response parity).
8. `src/types/types.contract.test.ts` (TypeScript type integrity).

---

### 4. End-to-End Suite (Playwright)

Located in `frontend/e2e/user-journey.spec.ts` and configured via `frontend/playwright.config.ts`.

#### Running E2E Tests:
```bash
# Run Playwright tests
npm --prefix frontend exec playwright test

# Run with interactive UI
npm --prefix frontend exec playwright test -- --ui
```

#### Verified User Journeys:
1. **Landing & Pipeline Navigation:** Verifies the 5-step pipeline, 6-step Proof of Contribution engine, and 8 quality metric cards.
2. **Real-time URL Validation:** Verifies debounced domain checks on official Iranian legal sources.
3. **Audit Trail Modal:** Inspects cryptographic hash representations and verification timestamps.
4. **Contributor Dashboard:** Ensures credits, statistics, and recent activity reflect active state.

---

### 5. Production Build Verification

To verify that the frontend compiles cleanly into a production-ready static bundle:
```bash
npm --prefix frontend run build
```
- **Type Check:** `tsc -b` passes with **0 errors**.
- **Vite Bundler:** Produces optimized minified output:
  - HTML: `~1.17 kB`
  - CSS: `~43.9 kB` (`gzip: 7.4 kB`)
  - JS: `~328.9 kB` (`gzip: 92.0 kB`) — well below the 1.5 MB threshold.
