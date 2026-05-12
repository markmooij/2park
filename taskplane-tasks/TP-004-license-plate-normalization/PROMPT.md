# Task: TP-004 — License Plate Normalization at API Boundary

**Created:** 2026-05-08
**Size:** S

## Review Level: 1 (Plan Only)

**Assessment:** Adds a normalization utility and applies it at the API boundary. Single file modification with a new utility file. Low risk, easy revert.
**Score:** 2/8 — Blast radius: 0, Pattern novelty: 1, Security: 0, Reversibility: 1

## Canonical Task Folder

```
taskplane-tasks/TP-004-license-plate-normalization/
├── PROMPT.md   ← This file (immutable above --- divider)
├── STATUS.md   ← Execution state (worker updates this)
├── .reviews/   ← Reviewer output (created by the orchestrator runtime)
└── .DONE       ← Created when complete
```

## Mission

The API currently echoes back license plates in whatever format the caller sends (e.g., `51-PX-PN`), but the 2park.nl website normalizes plates to `51PXPN` (no hyphens, uppercase). This causes the extend/cancel endpoints to fail when callers use the returned plate value with hyphens. Add a `normalize_license_plate()` utility and apply it at every API endpoint that accepts or returns a license plate.

## Dependencies

- **Task:** TP-003 (DOM audit needed to confirm how the website actually stores plates)
- **External:** None

## Context to Read First

> Only list docs the worker actually needs. Less is better.

**Tier 2 (area context):**
- `taskplane-tasks/CONTEXT.md`

**Tier 3 (load only if needed):**
- `models.py` — `validate_license_plate()` and `CreateBookingRequest` to understand current validation
- `api.py` — endpoints that accept/return license plates
- `taskplane-tasks/TP-003-dom-audit/DOM_REFERENCE.md` — confirm website plate format

## Environment

- **Workspace:** `/home/mark/Projects/2park`
- **Services required:** None (code changes only, no live testing)

## File Scope

> The orchestrator uses this to avoid merge conflicts.

- `models.py` (modified — add normalization)
- `api.py` (modified — apply normalization at boundary)
- `taskplane-tasks/TP-004-license-plate-normalization/STATUS.md` (modified)

## Steps

> **Hydration:** STATUS.md tracks outcomes, not individual code changes.

### Step 0: Preflight

- [ ] Read `models.py` to understand current `validate_license_plate()` logic
- [ ] Read `api.py` to identify all endpoints accepting/returning license plates
- [ ] Verify TP-003 DOM reference confirms website plate format

### Step 1: Add `normalize_license_plate()` to `models.py`

- [ ] Create `normalize_license_plate(plate: str) -> str` that:
  - Strips hyphens, spaces, and converts to uppercase
  - Returns the normalized string
  - Is idempotent (calling twice produces same result)
- [ ] Add unit test for normalization (edge cases: with hyphens, without hyphens, mixed case, spaces)
- [ ] Update `validate_license_plate()` to normalize **before** validation

**Artifacts:**
- `models.py` (modified)

### Step 2: Apply Normalization at API Boundary

- [ ] In `api.py`, normalize the `license_plate` parameter in:
  - `create_booking()` — normalize before passing to scraper
  - `extend_booking()` — normalize the URL path parameter
  - `cancel_booking()` — normalize the URL path parameter
- [ ] Ensure all response objects return the normalized plate (already handled if `create_booking` returns normalized plate from scraper)
- [ ] Update `README.md` to document that plates are normalized (hyphens stripped, uppercased)

**Artifacts:**
- `api.py` (modified)
- `README.md` (modified)

### Step 3: Testing & Verification

- [ ] Run FULL test suite: `pytest`
- [ ] Fix all failures
- [ ] Verify no test regressions

### Step 4: Documentation & Delivery

- [ ] `README.md` updated with normalization note
- [ ] Discoveries logged in STATUS.md

## Documentation Requirements

**Must Update:**
- `README.md` — Add note that license plates are normalized (hyphens stripped, uppercased) at the API boundary

**Check If Affected:**
- `API.md` — Update if API contract for license plate format changes

## Completion Criteria

- [ ] `normalize_license_plate()` exists in `models.py` and is tested
- [ ] All API endpoints normalize plates before processing
- [ ] `README.md` documents the normalization behavior
- [ ] Full test suite passes

## Git Commit Convention

Commits happen at **step boundaries** (not after every checkbox). All commits
for this task MUST include the task ID for traceability:

- **Step completion:** `feat(TP-004): complete Step N — description`
- **Bug fixes:** `fix(TP-004): description`
- **Tests:** `test(TP-004): description`
- **Hydration:** `hydrate: TP-004 expand Step N checkboxes`

## Do NOT

- Expand task scope — add tech debt to CONTEXT.md instead
- Modify `scraper.py` in this task (that's TP-005/TP-006)
- Commit without the task ID prefix in the commit message

---

## Amendments (Added During Execution)

<!-- Workers add amendments here if issues discovered during execution.
     Format:
     ### Amendment N — YYYY-MM-DD HH:MM
     **Issue:** [what was wrong]
     **Resolution:** [what was changed] -->
