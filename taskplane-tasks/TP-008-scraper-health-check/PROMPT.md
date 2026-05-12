# Task: TP-008 — `/health/scraper` Selector Check

**Created:** 2026-05-08
**Size:** M

## Review Level: 2 (Plan + Code)

**Assessment:** Adds a new API endpoint that validates scraper selectors are present on the live website. Prevents future silent failures from 2park.nl DOM changes. Requires code review since it adds a new production endpoint.
**Score:** 4/8 — Blast radius: 1, Pattern novelty: 1, Security: 0, Reversibility: 2

## Canonical Task Folder

```
taskplane-tasks/TP-008-scraper-health-check/
├── PROMPT.md   ← This file (immutable above --- divider)
├── STATUS.md   ← Execution state (worker updates this)
├── .reviews/   ← Reviewer output (created by the orchestrator runtime)
└── .DONE       ← Created when complete
```

## Mission

Add a `/health/scraper` endpoint that logs into the 2park.nl dashboard and verifies that the expected selectors (booking cards, tab navigation, extend/cancel buttons) are present. This catches selector drift early — before a caller tries to extend a booking and gets a 404.

## Dependencies

- **Task:** TP-003 (DOM audit provides the selectors to check)
- **Task:** TP-006 (extend_booking selectors must be fixed first)
- **Task:** TP-007 (shared `_find_booking_card()` helper provides reusable logic)
- **External:** None

## Context to Read First

> Only list docs the worker actually needs. Less is better.

**Tier 2 (area context):**
- `taskplane-tasks/CONTEXT.md`

**Tier 3 (load only if needed):**
- `api.py` — existing `/health` endpoint for pattern reference
- `scraper.py` — `_login()` and `_find_booking_card()` methods
- `errors.py` — existing error types
- `taskplane-tasks/TP-003-dom-audit/DOM_REFERENCE.md` — selectors to validate

## Environment

- **Workspace:** `/home/mark/Projects/2park`
- **Services required:** None (code changes only, no live testing)

## File Scope

> The orchestrator uses this to avoid merge conflicts.

- `api.py` (modified — add `/health/scraper` endpoint)
- `scraper.py` (modified — add `scraper_health_check()` method)
- `errors.py` (modified — add `SELECTOR_MISMATCH` error code if needed)
- `taskplane-tasks/TP-008-scraper-health-check/STATUS.md` (modified)

## Steps

> **Hydration:** STATUS.md tracks outcomes, not individual code changes.

### Step 0: Preflight

- [ ] Read `api.py` existing `/health` endpoint for pattern reference
- [ ] Read `scraper.py` to understand `_login()` and `_find_booking_card()`
- [ ] Read `errors.py` to understand error handling patterns
- [ ] Verify TP-003, TP-006, TP-007 are complete

### Step 1: Add `scraper_health_check()` to `TwoParkScraper`

- [ ] Add `async def scraper_health_check(self) -> dict` method that:
  - Navigates to the dashboard
  - Verifies tab navigation selectors are present (`.tabs-container`, `.tabText`)
  - Verifies booking card selector exists (even if no cards, the container should be there)
  - Returns a dict: `{"status": "ok", "selectors_checked": [...], "timestamp": ...}` or `{"status": "degraded", "missing_selectors": [...]}`
- [ ] Log detailed results for debugging

**Artifacts:**
- `scraper.py` (modified)

### Step 2: Add `/health/scraper` Endpoint to `api.py`

- [ ] Create `GET /health/scraper` endpoint that:
  - Calls `scraper_health_check()` via `TwoParkScraper`
  - Returns HTTP 200 if all selectors present
  - Returns HTTP 200 with `"status": "degraded"` if some selectors missing (don't fail the health check entirely — the website may just be slow)
  - Includes response time in the response
- [ ] Add to the API root (`/`) endpoint documentation
- [ ] Add appropriate error handling and timeouts

**Artifacts:**
- `api.py` (modified)

### Step 3: Add `SELECTOR_MISMATCH` Error Code (if needed)

- [ ] If the health check needs a dedicated error type, add `SELECTOR_MISMATCH` to `ErrorCode` enum in `errors.py`
- [ ] Create corresponding exception class if needed

**Artifacts:**
- `errors.py` (modified, if needed)

### Step 4: Testing & Verification

- [ ] Run FULL test suite: `pytest`
- [ ] Fix all failures
- [ ] Verify no test regressions

### Step 5: Documentation & Delivery

- [ ] Update `README.md` to document the new `/health/scraper` endpoint
- [ ] Discoveries logged in STATUS.md

## Documentation Requirements

**Must Update:**
- `README.md` — Document the new `/health/scraper` endpoint

**Check If Affected:**
- `API.md` — Update if API endpoint documentation exists

## Completion Criteria

- [ ] `scraper_health_check()` method exists in `TwoParkScraper`
- [ ] `/health/scraper` endpoint works and returns selector status
- [ ] Full test suite passes
- [ ] `README.md` updated

## Git Commit Convention

Commits happen at **step boundaries** (not after every checkbox). All commits
for this task MUST include the task ID for traceability:

- **Step completion:** `feat(TP-008): complete Step N — description`
- **Bug fixes:** `fix(TP-008): description`
- **Tests:** `test(TP-008): description`
- **Hydration:** `hydrate: TP-008 expand Step N checkboxes`

## Do NOT

- Expand task scope — add tech debt to CONTEXT.md instead
- Modify existing `/health` endpoint (keep it unchanged)
- Commit without the task ID prefix in the commit message

---

## Amendments (Added During Execution)

<!-- Workers add amendments here if issues discovered during execution.
     Format:
     ### Amendment N — YYYY-MM-DD HH:MM
     **Issue:** [what was wrong]
     **Resolution:** [what was changed] -->
