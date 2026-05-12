# Task: TP-005 — Return Actual End Time from Website

**Created:** 2026-05-08
**Size:** S

## Review Level: 1 (Plan Only)

**Assessment:** Modifies `create_booking()` in `scraper.py` to read back the actual end time from the website instead of returning the locally calculated value. Single file change.
**Score:** 2/8 — Blast radius: 0, Pattern novelty: 1, Security: 0, Reversibility: 1

## Canonical Task Folder

```
taskplane-tasks/TP-005-actual-end-time/
├── PROMPT.md   ← This file (immutable above --- divider)
├── STATUS.md   ← Execution state (worker updates this)
├── .reviews/   ← Reviewer output (created by the orchestrator runtime)
└── .DONE       ← Created when complete
```

## Mission

The API currently calculates `end_time = start_time + timedelta(minutes=duration_minutes)` locally and returns it to the caller, but the actual booking on the 2park.nl website uses its own logic (often ending at end-of-day). The API lies to the caller about the true end time. Fix `scraper.py` `create_booking()` to read back the actual end time from the website after creating the booking.

## Dependencies

- **Task:** TP-003 (DOM audit needed to understand the time element selectors on booking cards)
- **External:** None

## Context to Read First

> Only list docs the worker actually needs. Less is better.

**Tier 2 (area context):**
- `taskplane-tasks/CONTEXT.md`

**Tier 3 (load only if needed):**
- `scraper.py` — `create_booking()` and `get_active_reservations()` methods
- `models.py` — `Reservation` internal model
- `taskplane-tasks/TP-003-dom-audit/DOM_REFERENCE.md` — time element selectors

## Environment

- **Workspace:** `/home/mark/Projects/2park`
- **Services required:** None (code changes only, no live testing)

## File Scope

> The orchestrator uses this to avoid merge conflicts.

- `scraper.py` (modified — `create_booking()` and related)
- `taskplane-tasks/TP-005-actual-end-time/STATUS.md` (modified)

## Steps

> **Hydration:** STATUS.md tracks outcomes, not individual code changes.

### Step 0: Preflight

- [ ] Read `scraper.py` to understand current `create_booking()` flow
- [ ] Read `get_active_reservations()` to understand how times are extracted
- [ ] Verify TP-003 DOM reference is available

### Step 1: Update `create_booking()` to Return Actual End Time

- [ ] After the form is submitted and verified, the existing code already calls `get_active_reservations()` to verify the booking was created
- [ ] Modify `create_booking()` to read the `end_time` from the returned `Reservation` object (which is scraped from the website) instead of using the caller-supplied `end_time`
- [ ] If the scraped end time differs from the calculated end time by more than 5 minutes, log a warning with both values
- [ ] Ensure the returned dict includes the actual scraped `end_time`

**Artifacts:**
- `scraper.py` (modified)

### Step 2: Update `api.py` to Propagate Actual End Time

- [ ] Verify that `create_booking()` endpoint in `api.py` returns the end time from the scraper result (should already work if scraper returns correct value)
- [ ] Add logging to surface the discrepancy when it occurs

**Artifacts:**
- `api.py` (modified, if needed)

### Step 3: Testing & Verification

- [ ] Run FULL test suite: `pytest`
- [ ] Fix all failures
- [ ] Verify no test regressions

### Step 4: Documentation & Delivery

- [ ] Discoveries logged in STATUS.md

## Documentation Requirements

**Must Update:** None
**Check If Affected:**
- `README.md` — Update if the API behavior description needs clarification about end time accuracy

## Completion Criteria

- [ ] `create_booking()` returns actual scraped end time from website
- [ ] Discrepancy logging in place (>5 min difference)
- [ ] Full test suite passes

## Git Commit Convention

Commits happen at **step boundaries** (not after every checkbox). All commits
for this task MUST include the task ID for traceability:

- **Step completion:** `feat(TP-005): complete Step N — description`
- **Bug fixes:** `fix(TP-005): description`
- **Tests:** `test(TP-005): description`
- **Hydration:** `hydrate: TP-005 expand Step N checkboxes`

## Do NOT

- Expand task scope — add tech debt to CONTEXT.md instead
- Modify selectors in this task (that's TP-006)
- Commit without the task ID prefix in the commit message

---

## Amendments (Added During Execution)

<!-- Workers add amendments here if issues discovered during execution.
     Format:
     ### Amendment N — YYYY-MM-DD HH:MM
     **Issue:** [what was wrong]
     **Resolution:** [what was changed] -->
