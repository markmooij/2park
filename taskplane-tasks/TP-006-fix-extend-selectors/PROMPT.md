# Task: TP-006 — Fix `extend_booking()` Selectors

**Created:** 2026-05-08
**Size:** M

## Review Level: 2 (Plan + Code)

**Assessment:** Rewrites `extend_booking()` in `scraper.py` with correct selectors from the DOM audit. This is the highest-value fix — it resolves the only failing step in the TP-001 test. Requires code review since it touches production scraper logic.
**Score:** 4/8 — Blast radius: 1, Pattern novelty: 1, Security: 0, Reversibility: 2

## Canonical Task Folder

```
taskplane-tasks/TP-006-fix-extend-selectors/
├── PROMPT.md   ← This file (immutable above --- divider)
├── STATUS.md   ← Execution state (worker updates this)
├── .reviews/   ← Reviewer output (created by the orchestrator runtime)
└── .DONE       ← Created when complete
```

## Mission

`extend_booking()` in `scraper.py` uses placeholder selectors (`.parkapp-item`, `.extend-button`, `.btn-extend`) that don't exist in the current 2park.nl DOM. Using the DOM reference from TP-003, rewrite `extend_booking()` with correct selectors so the API can successfully extend bookings via the website UI.

## Dependencies

- **Task:** TP-003 (DOM audit must provide actual selectors)
- **External:** None

## Context to Read First

> Only list docs the worker actually needs. Less is better.

**Tier 2 (area context):**
- `taskplane-tasks/CONTEXT.md`

**Tier 3 (load only if needed):**
- `scraper.py` — current `extend_booking()` implementation
- `taskplane-tasks/TP-003-dom-audit/DOM_REFERENCE.md` — actual selectors to use
- `models.py` — `Reservation` model

## Environment

- **Workspace:** `/home/mark/Projects/2park`
- **Services required:** None (code changes only, no live testing)

## File Scope

> The orchestrator uses this to avoid merge conflicts.

- `scraper.py` (modified — `extend_booking()` method)
- `taskplane-tasks/TP-006-fix-extend-selectors/STATUS.md` (modified)

## Steps

> **Hydration:** STATUS.md tracks outcomes, not individual code changes.

### Step 0: Preflight

- [ ] Read `scraper.py` `extend_booking()` to understand current flow
- [ ] Read TP-003 `DOM_REFERENCE.md` for actual selectors
- [ ] Verify DOM reference includes extend button and booking card selectors

### Step 1: Rewrite `extend_booking()` with Correct Selectors

- [ ] Navigate to the dashboard (not `/parkings`) since that's where bookings are visible
- [ ] Click the "Lopend" tab using the confirmed tab navigation selectors from DOM audit
- [ ] Find the booking card using the real card selector (from DOM audit)
- [ ] Locate and click the extend button using real selectors (from DOM audit)
- [ ] Fill in additional minutes in the extend form
- [ ] Submit the extension
- [ ] Read back the new end time from the refreshed page (not calculated locally)
- [ ] Add a `> Code review checkpoint` marker — this step touches production scraper logic

**Artifacts:**
- `scraper.py` (modified)

### Step 2: Handle Edge Cases

- [ ] If no active booking found for the plate, return proper `BookingNotFoundException`
- [ ] If extend button not found, log available buttons for debugging and return `ScrapeErrorException`
- [ ] Take screenshot on failure for debugging

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
**Check If Affected:**
- `README.md` — Update if extend endpoint behavior changes

## Completion Criteria

- [ ] `extend_booking()` uses correct selectors from DOM audit
- [ ] Extension reads back actual new end time from website
- [ ] Full test suite passes

## Git Commit Convention

Commits happen at **step boundaries** (not after every checkbox). All commits
for this task MUST include the task ID for traceability:

- **Step completion:** `feat(TP-006): complete Step N — description`
- **Bug fixes:** `fix(TP-006): description`
- **Tests:** `test(TP-006): description`
- **Hydration:** `hydrate: TP-006 expand Step N checkboxes`

## Do NOT

- Expand task scope — add tech debt to CONTEXT.md instead
- Modify `cancel_booking()` in this task (that's part of TP-007 shared helper)
- Commit without the task ID prefix in the commit message

---

## Amendments (Added During Execution)

<!-- Workers add amendments here if issues discovered during execution.
     Format:
     ### Amendment N — YYYY-MM-DD HH:MM
     **Issue:** [what was wrong]
     **Resolution:** [what was changed] -->
