# Task: TP-009 — Validation Re-Run: Consolidated API Test

**Created:** 2026-05-13
**Size:** M

## Review Level: 2 (Plan + Code)

**Assessment:** Re-runs the full TP-001 test suite against the improved code (TP-003 through TP-008). Validates all 3 original discrepancies are fixed. Requires code review since the test script may need updates to match new API behavior.
**Score:** 4/8 — Blast radius: 1, Pattern novelty: 0, Security: 0, Reversibility: 2

## Canonical Task Folder

```
taskplane-tasks/TP-009-validation-rerun/
├── PROMPT.md   ← This file (immutable above --- divider)
├── STATUS.md   ← Execution state (worker updates this)
├── .reviews/   ← Reviewer output (created by the orchestrator runtime)
└── .DONE       ← Created when complete
```

## Mission

Re-run the consolidated end-to-end API test (`test_run.py`) against the live Raspberry Pi instance now that TP-003 through TP-008 have improved the code. Validate that all 3 original discrepancies are resolved:
1. License plate normalization works correctly
2. Booking end time matches actual website value
3. Extend booking works with correct selectors

## Dependencies

- **Task:** TP-003 (DOM audit complete)
- **Task:** TP-004 (license plate normalization applied)
- **Task:** TP-005 (actual end time from website)
- **Task:** TP-006 (extend_booking selectors fixed)
- **Task:** TP-007 (shared `_find_booking_card()` helper)
- **Task:** TP-008 (`/health/scraper` endpoint)
- **External:** 2Park API running at `http://rasp-pi-4-service.local:8090`
- **External:** 2Park website `mijn.2park.nl` accessible

## Context to Read First

> Only list docs the worker actually needs. Less is better.

**Tier 2 (area context):**
- `taskplane-tasks/CONTEXT.md`

**Tier 3 (load only if needed):**
- `taskplane-tasks/TP-001-consolidated-api-test/RESULTS.md` — original test results showing the 3 discrepancies
- `taskplane-tasks/TP-001-consolidated-api-test/test_run.py` — existing test script to adapt
- `taskplane-tasks/TP-003-dom-audit/DOM_REFERENCE.md` — current selectors

## Environment

- **Workspace:** `/home/mark/Projects/2park`
- **API URL:** `http://rasp-pi-4-service.local:8090`
- **Bearer Token:** `b6a32d1cde51a1dce7e21343f8233a501afe49cbf3bc0983263591fbf3e3ce43`
- **License Plate:** `51-PX-PN`
- **2Park Website:** `https://mijn.2park.nl` (slow — use generous timeouts)

## File Scope

> The orchestrator uses this to avoid merge conflicts.

- `taskplane-tasks/TP-009-validation-rerun/test_run.py` (new)
- `taskplane-tasks/TP-009-validation-rerun/RESULTS.md` (new — test report)
- `taskplane-tasks/TP-009-validation-rerun/STATUS.md` (modified)

## Steps

> **Hydration:** STATUS.md tracks outcomes, not individual code changes.

### Step 0: Preflight

- [ ] Verify API is reachable: `curl http://rasp-pi-4-service.local:8090/health`
- [ ] Verify `/health/scraper` endpoint works: `curl http://rasp-pi-4-service.local:8090/health/scraper`
- [ ] Verify credentials are available (TWOPARK_EMAIL and TWOPARK_PASSWORD)
- [ ] Verify Playwright is installed: `python -c "from playwright.sync_api import sync_playwright; print('OK')"`
- [ ] Verify no active bookings exist: `curl http://rasp-pi-4-service.local:8090/api/bookings`

### Step 1: Run Full API Test Sequence

- [ ] Create booking for `51-PX-PN` (120 min) — verify HTTP 201, normalized plate in response
- [ ] Extend booking by 60 min — verify HTTP 200 (was failing in TP-001!)
- [ ] List active bookings — verify booking present with correct times
- [ ] Cancel booking — verify HTTP 200 with status "cancelled"
- [ ] Log all responses and timestamps to `RESULTS.md`

**Artifacts:**
- `taskplane-tasks/TP-009-validation-rerun/RESULTS.md` (new)

### Step 2: Independent Playwright Verification

- [ ] Log in to `https://mijn.2park.nl/login` with credentials
- [ ] Verify booking appears on dashboard (after create)
- [ ] Verify booking end time reflects extension (+60 min)
- [ ] Verify cancelled booking no longer appears in active bookings
- [ ] Capture screenshots at each verification step
- [ ] Log findings to `RESULTS.md`

### Step 3: Validate Original Discrepancies Are Fixed

- [ ] Verify license plate is normalized in all API responses (`51PXPN` not `51-PX-PN`)
- [ ] Verify end time matches actual website value (not locally calculated)
- [ ] Verify extend booking succeeded (HTTP 200, not 404)
- [ ] Compare results against TP-001 original results and note improvements

### Step 4: Cleanup & Final Report

- [ ] Ensure all test bookings are cancelled
- [ ] Compile final `RESULTS.md` with:
  - Full test report with timestamps, HTTP status codes, response bodies
  - Comparison against TP-001 results showing which discrepancies are now fixed
  - Playwright screenshots of each verification step
  - Any remaining issues or new discrepancies discovered

### Step 5: Testing & Verification

- [ ] Verify test script is executable and produces expected output
- [ ] Verify no active test bookings remain

### Step 6: Documentation & Delivery

- [ ] `RESULTS.md` complete with full report
- [ ] Discoveries logged in STATUS.md

## Documentation Requirements

**Must Update:** None
**Check If Affected:** None

## Completion Criteria

- [ ] All 6 steps complete
- [ ] All API operations returned expected HTTP status codes
- [ ] Extend booking succeeded (was the failing step in TP-001)
- [ ] Playwright verification confirmed 2park.nl state matches API state
- [ ] `RESULTS.md` contains full report with screenshots and comparison to TP-001
- [ ] No active test bookings remain

## Git Commit Convention

Commits happen at **step boundaries** (not after every checkbox). All commits
for this task MUST include the task ID for traceability:

- **Step completion:** `test(TP-009): complete Step N — description`
- **Bug fixes:** `fix(TP-009): description`
- **Tests:** `test(TP-009): description`
- **Hydration:** `hydrate: TP-009 expand Step N checkboxes`

## Do NOT

- Expand task scope — add tech debt to CONTEXT.md instead
- Create bookings with durations longer than 240 minutes
- Leave any test bookings active after the test completes
- Load docs not listed in "Context to Read First"
- Commit without the task ID prefix in the commit message
- Use aggressive timeouts — the 2park.nl website is slow; use 60s+ for navigation

---

## Amendments (Added During Execution)

<!-- Workers add amendments here if issues discovered during execution.
     Format:
     ### Amendment N — YYYY-MM-DD HH:MM
     **Issue:** [what was wrong]
     **Resolution:** [what was changed] -->
