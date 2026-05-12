# Task: TP-007 — Shared `_find_booking_card()` Helper

**Created:** 2026-05-08
**Size:** S

## Review Level: 1 (Plan Only)

**Assessment:** Extracts shared logic from `extend_booking()` and `cancel_booking()` into a reusable `_find_booking_card()` helper. Reduces duplication and makes future selector updates easier.
**Score:** 2/8 — Blast radius: 0, Pattern novelty: 1, Security: 0, Reversibility: 1

## Canonical Task Folder

```
taskplane-tasks/TP-007-find-booking-card-helper/
├── PROMPT.md   ← This file (immutable above --- divider)
├── STATUS.md   ← Execution state (worker updates this)
├── .reviews/   ← Reviewer output (created by the orchestrator runtime)
└── .DONE       ← Created when complete
```

## Mission

`extend_booking()` and `cancel_booking()` in `scraper.py` both contain logic to find a booking card by license plate. This duplication makes it hard to maintain selectors. Extract this into a shared `_find_booking_card(page, license_plate)` method that returns the booking card element and its extracted data (license plate, start/end times).

## Dependencies

- **Task:** TP-003 (DOM audit needed for selectors)
- **Task:** TP-006 (extend_booking selectors must be fixed first, so the helper can learn from the working code)

## Context to Read First

> Only list docs the worker actually needs. Less is better.

**Tier 2 (area context):**
- `taskplane-tasks/CONTEXT.md`

**Tier 3 (load only if needed):**
- `scraper.py` — current `extend_booking()`, `cancel_booking()`, and `get_active_reservations()` methods
- `taskplane-tasks/TP-003-dom-audit/DOM_REFERENCE.md` — actual selectors

## Environment

- **Workspace:** `/home/mark/Projects/2park`
- **Services required:** None (code changes only, no live testing)

## File Scope

> The orchestrator uses this to avoid merge conflicts.

- `scraper.py` (modified — add helper, refactor callers)
- `taskplane-tasks/TP-007-find-booking-card-helper/STATUS.md` (modified)

## Steps

> **Hydration:** STATUS.md tracks outcomes, not individual code changes.

### Step 0: Preflight

- [ ] Read `scraper.py` to understand current `extend_booking()` and `cancel_booking()` implementations
- [ ] Identify duplicated card-finding logic between the two methods
- [ ] Verify TP-003 and TP-006 are complete

### Step 1: Create `_find_booking_card()` Helper

- [ ] Add `_find_booking_card(self, page, license_plate) -> Optional[dict]` method that:
  - Navigates to the dashboard and clicks the "Lopend" tab
  - Finds the booking card matching the license plate (using real selectors from DOM audit)
  - Returns a dict with: `card_element`, `license_plate`, `start_time`, `end_time`
  - Returns `None` if no matching card found
- [ ] Handle license plate normalization (compare normalized forms)
- [ ] Log available buttons on the card for debugging

**Artifacts:**
- `scraper.py` (modified)

### Step 2: Refactor Callers to Use the Helper

- [ ] Update `extend_booking()` to call `_find_booking_card()` instead of duplicating card-finding logic
- [ ] Update `cancel_booking()` to call `_find_booking_card()` instead of duplicating card-finding logic
- [ ] Verify both methods still work correctly with the shared helper

**Artifacts:**
- `scraper.py` (modified)

### Step 3: Testing & Verification

- [ ] Run FULL test suite: `pytest`
- [ ] Fix all failures
- [ ] Verify no test regressions

### Step 4: Documentation & Delivery

- [ ] Discoveries logged in STATUS.md

## Documentation Requirements

**Must Update:** None
**Check If Affected:** None

## Completion Criteria

- [ ] `_find_booking_card()` helper exists and is tested
- [ ] Both `extend_booking()` and `cancel_booking()` use the shared helper
- [ ] Full test suite passes

## Git Commit Convention

Commits happen at **step boundaries** (not after every checkbox). All commits
for this task MUST include the task ID for traceability:

- **Step completion:** `feat(TP-007): complete Step N — description`
- **Bug fixes:** `fix(TP-007): description`
- **Tests:** `test(TP-007): description`
- **Hydration:** `hydrate: TP-007 expand Step N checkboxes`

## Do NOT

- Expand task scope — add tech debt to CONTEXT.md instead
- Modify `get_active_reservations()` in this task (it has different responsibilities)
- Commit without the task ID prefix in the commit message

---

## Amendments (Added During Execution)

<!-- Workers add amendments here if issues discovered during execution.
     Format:
     ### Amendment N — YYYY-MM-DD HH:MM
     **Issue:** [what was wrong]
     **Resolution:** [what was changed] -->
