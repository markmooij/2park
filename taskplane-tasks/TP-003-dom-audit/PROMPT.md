# Task: TP-003 — DOM Audit (Playwright Dump)

**Created:** 2026-05-08
**Size:** S

## Review Level: 0 (None)

**Assessment:** Discovery-only task. Runs a Playwright script to dump the current 2park.nl dashboard DOM structure for selector reference. No code changes to the project.
**Score:** 0/8 — Blast radius: 0, Pattern novelty: 0, Security: 0, Reversibility: 0

## Canonical Task Folder

```
taskplane-tasks/TP-003-dom-audit/
├── PROMPT.md   ← This file (immutable above --- divider)
├── STATUS.md   ← Execution state (worker updates this)
├── .reviews/   ← Reviewer output (created by the orchestrator runtime)
└── .DONE       ← Created when complete
```

## Mission

Run a Playwright script that logs into `mijn.2park.nl`, navigates to the dashboard "Lopend" tab, and dumps the full DOM structure of the booking cards. This produces a reference file (`DOM_REFERENCE.md`) with actual class names, element hierarchy, and button text that other tasks (TP-006, TP-007, TP-008) will use to write correct selectors.

## Dependencies

- **External:** 2Park website `mijn.2park.nl` accessible
- **External:** 2Park account credentials available (TWOPARK_EMAIL, TWOPARK_PASSWORD)

## Context to Read First

> Only list docs the worker actually needs. Less is better.

**Tier 2 (area context):**
- `taskplane-tasks/CONTEXT.md`

**Tier 3 (load only if needed):**
- `scraper.py` — `_login()` method for understanding login flow and selectors

## Environment

- **Workspace:** `/home/mark/Projects/2park`
- **Services required:** 2Park website (`mijn.2park.nl`)
- **Credentials:** TWOPARK_EMAIL and TWOPARK_PASSWORD from `.env`

## File Scope

> The orchestrator uses this to avoid merge conflicts.

- `taskplane-tasks/TP-003-dom-audit/DOM_REFERENCE.md` (new)
- `taskplane-tasks/TP-003-dom-audit/STATUS.md` (modified)
- `taskplane-tasks/TP-003-dom-audit/.DONE` (new)

## Steps

> **Hydration:** STATUS.md tracks outcomes, not individual code changes.

### Step 0: Preflight

- [ ] Verify credentials are available (TWOPARK_EMAIL and TWOPARK_PASSWORD from `.env`)
- [ ] Verify Playwright is installed: `python -c "from playwright.sync_api import sync_playwright; print('OK')"`

### Step 1: Run DOM Audit Script

- [ ] Write a standalone Playwright script (`dom_audit.py`) that:
  - Logs into `https://mijn.2park.nl/login` using TWOPARK credentials
  - Navigates to the dashboard
  - Clicks the "Lopend" (active) tab
  - Screenshots the dashboard to `/tmp/dashboard_dom_audit.png`
  - Extracts and logs:
    - All button text and class names within booking cards
    - Tab container structure (`.tabs-container`, `.tabText`, etc.)
    - Booking card hierarchy (parent class, license plate element, time elements, action buttons)
    - "Gepland" (scheduled) tab structure
  - Writes all findings to `DOM_REFERENCE.md`

**Artifacts:**
- `taskplane-tasks/TP-003-dom-audit/DOM_REFERENCE.md` (new)
- `/tmp/dashboard_dom_audit.png` (screenshot)

### Step 2: Verify DOM Reference

- [ ] Verify `DOM_REFERENCE.md` contains:
  - Actual booking card selector (replacing `.parkapp-item`)
  - Actual extend button selector (replacing `.extend-button`)
  - Actual cancel button selector (replacing `.cancel-button`)
  - Tab navigation structure
- [ ] Verify screenshot was captured

### Step 3: Delivery

## Documentation Requirements

**Must Update:** None
**Check If Affected:** None

## Completion Criteria

- [ ] `DOM_REFERENCE.md` exists with selector data
- [ ] Screenshot captured at `/tmp/dashboard_dom_audit.png`
- [ ] DOM reference includes booking card, extend button, cancel button, and tab selectors

## Git Commit Convention

Commits happen at **step boundaries** (not after every checkbox). All commits
for this task MUST include the task ID for traceability:

- **Step completion:** `feat(TP-003): complete Step N — description`
- **Bug fixes:** `fix(TP-003): description`
- **Tests:** `test(TP-003): description`
- **Hydration:** `hydrate: TP-003 expand Step N checkboxes`

## Do NOT

- Modify any existing project files
- Expand task scope — this is a discovery-only task
- Commit without the task ID prefix in the commit message

---

## Amendments (Added During Execution)

<!-- Workers add amendments here if issues discovered during execution.
     Format:
     ### Amendment N — YYYY-MM-DD HH:MM
     **Issue:** [what was wrong]
     **Resolution:** [what was changed] -->
