# Task: TP-001 — Consolidated End-to-End API Test Run

**Created:** 2026-05-08
**Size:** M

## Review Level: 1 (Plan Only)

**Assessment:** This task exercises the live API and the 2park.nl website via browser automation. The test script adapts existing Playwright patterns from scraper.py. Credentials are used as-is without modification. All bookings are ephemeral and reversible.
**Score:** 3/8 — Blast radius: 1, Pattern novelty: 1, Security: 1, Reversibility: 0

## Canonical Task Folder

```
/home/mark/Projects/2park/taskplane-tasks/TP-001-consolidated-api-test/
├── PROMPT.md   ← This file (immutable above --- divider)
├── STATUS.md   ← Execution state (worker updates this)
├── .reviews/   ← Reviewer output (created by the orchestrator runtime)
├── .DONE       ← Created when complete
└── test_run.py  ← The consolidated test script
```

## Mission

Run a full end-to-end test of the 2Park API against the live Raspberry Pi instance at `http://rasp-pi-4-service.local:8090`. The test creates a booking, extends it, cancels it, and verifies each step both via the API response and independently by logging into `mijn.2park.nl` with Playwright. The goal is to confirm the API works correctly in a real-world scenario and that the 2park.nl website reflects the expected state at each stage.

## Dependencies

- **External:** 2Park API running at `http://rasp-pi-4-service.local:8090`
- **External:** 2Park website `mijn.2park.nl` accessible (may be slow)
- **External:** 2Park account credentials available (TWOPARK_EMAIL, TWOPARK_PASSWORD)

## Context to Read First

> Only list docs the worker actually needs. Less is better.

**Tier 2 (area context):**
- `taskplane-tasks/CONTEXT.md`

**Tier 3 (load only if needed):**
- `scraper.py` — to understand Playwright selectors and login flow for the independent verification step
- `README.md` — API endpoints, curl examples, and configuration details

## Environment

- **Workspace:** `/home/mark/Projects/2park`
- **API URL:** `http://rasp-pi-4-service.local:8090`
- **Bearer Token:** `yourtoken`
- **License Plate:** `51-PX-PN`
- **2Park Website:** `https://mijn.2park.nl` (slow — use generous timeouts)

## File Scope

> The orchestrator uses this to avoid merge conflicts.

- `taskplane-tasks/TP-001-consolidated-api-test/test_run.py` (new)
- `taskplane-tasks/TP-001-consolidated-api-test/STATUS.md` (modified)
- `taskplane-tasks/TP-001-consolidated-api-test/RESULTS.md` (new — test report)

## Steps

> **Hydration:** STATUS.md tracks outcomes, not individual code changes.

### Step 0: Preflight

- [ ] Verify API is reachable: `curl http://rasp-pi-4-service.local:8090/health`
- [ ] Verify credentials are available (TWOPARK_EMAIL and TWOPARK_PASSWORD env vars or stored securely)
- [ ] Verify Playwright is installed: `python -c "from playwright.sync_api import sync_playwright; print('OK')"`

### Step 1: API Test Sequence — Create Booking

- [ ] Create a booking for license plate `51-PX-PN` with duration 120 minutes using `start_time: "now"`
- [ ] Verify the API returns HTTP 201 with correct booking details (license_plate, start_time, end_time, status: "active")
- [ ] Log the response body and timestamp to RESULTS.md

**Artifacts:**
- `taskplane-tasks/TP-001-consolidated-api-test/RESULTS.md` (new — test results log)

### Step 2: API Test Sequence — Extend Booking

- [ ] Extend the booking for `51-PX-PN` by 60 additional minutes
- [ ] Verify the API returns HTTP 200 with the new_end_time
- [ ] Verify the new_end_time is exactly 60 minutes past the original end_time
- [ ] Log the response body to RESULTS.md

### Step 3: API Test Sequence — List Active Bookings

- [ ] GET `/api/bookings` to confirm the booking is still active
- [ ] Verify the booking appears in the list with correct license_plate and status
- [ ] GET `/api/account/balance` to confirm account is accessible
- [ ] Log responses to RESULTS.md

### Step 4: API Test Sequence — Cancel Booking

- [ ] POST to `/api/bookings/51-PX-PN/cancel`
- [ ] Verify the API returns HTTP 200 with status: "cancelled"
- [ ] Log the response body to RESULTS.md

### Step 5: Independent Playwright Verification — Booking Created

- [ ] Launch a separate Playwright browser session (not the API's scraper)
- [ ] Log in to `https://mijn.2park.nl/login` using the same TWOPARK_EMAIL and TWOPARK_PASSWORD
- [ ] Wait for the dashboard to load (use generous timeout — 60+ seconds for page load)
- [ ] Verify the booking for `51-PX-PN` appears on the dashboard
- [ ] Record the booking details shown (license plate, start time, end time, status)
- [ ] Log findings to RESULTS.md

### Step 6: Independent Playwright Verification — Booking Extended

- [ ] Refresh the dashboard (or wait for the extended booking to appear)
- [ ] Verify the booking end time reflects the extension (+60 minutes)
- [ ] Log findings to RESULTS.md

### Step 7: Independent Playwright Verification — Booking Cancelled

- [ ] Refresh the dashboard
- [ ] Verify the cancelled booking for `51-PX-PN` no longer appears in active bookings
- [ ] Optionally check a past/cancelled bookings section if the UI has one
- [ ] Log findings to RESULTS.md

### Step 8: Cleanup & Documentation

- [ ] Ensure all test bookings are cancelled (verify via API: GET /api/bookings should return empty or no active `51-PX-PN`)
- [ ] Compile final RESULTS.md with: what was attempted, what was executed, what happened, any discrepancies between API and website
- [ ] Include timestamps, HTTP status codes, response bodies, and Playwright screenshots of each verification step

## Documentation Requirements

**Must Update:**
- `taskplane-tasks/TP-001-consolidated-api-test/RESULTS.md` — Full test report with timestamps, curl outputs, API responses, Playwright verification results, and screenshots

**Check If Affected:**
- `README.md` — Update if any API endpoint behavior differs from documented behavior

## Completion Criteria

- [ ] All 8 steps complete
- [ ] All API operations returned expected HTTP status codes
- [ ] Playwright verification confirmed 2park.nl state matches API state at each step
- [ ] RESULTS.md contains full report with screenshots and discrepancy notes
- [ ] No active test bookings remain (cleanup verified)

## Git Commit Convention

Commits happen at **step boundaries** (not after every checkbox). All commits
for this task MUST include the task ID for traceability:

- **Step completion:** `test(TP-001): complete Step N — description`
- **Bug fixes:** `fix(TP-001): description`
- **Tests:** `test(TP-001): description`
- **Hydration:** `hydrate: TP-001 expand Step N checkboxes`

## Do NOT

- Expand task scope — add tech debt to CONTEXT.md instead
- Create bookings with durations longer than 240 minutes (keep test impact minimal)
- Leave any test bookings active after the test completes
- Load docs not listed in "Context to Read First"
- Commit without the task ID prefix in the commit message
- Use aggressive timeouts — the 2park.nl website is slow; use 60s+ for navigation and 30s+ for selectors

---

## Amendments (Added During Execution)

<!-- Workers add amendments here if issues discovered during execution.
     Format:
     ### Amendment N — YYYY-MM-DD HH:MM
     **Issue:** [what was wrong]
     **Resolution:** [what was changed] -->
