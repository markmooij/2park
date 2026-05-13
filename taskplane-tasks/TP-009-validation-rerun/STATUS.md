# TP-009: Validation Re-Run — Consolidated API Test — Status

**Current Step:** Not Started
**Status:** 🔵 Ready for Execution
**Last Updated:** 2026-05-13
**Review Level:** 2
**Review Counter:** 0
**Iteration:** 0
**Size:** M

> **Hydration:** Checkboxes represent meaningful outcomes, not individual code
> changes. Workers expand steps when runtime discoveries warrant it.

---

### Step 0: Preflight
**Status:** ⬜ Not Started

- [ ] Verify API is reachable
- [ ] Verify `/health/scraper` endpoint works
- [ ] Verify credentials available
- [ ] Verify Playwright installed
- [ ] Verify no active bookings

---

### Step 1: Run Full API Test Sequence
**Status:** ⬜ Not Started

- [ ] Create booking — verify HTTP 201, normalized plate
- [ ] Extend booking — verify HTTP 200 (was failing in TP-001)
- [ ] List active bookings — verify booking present
- [ ] Cancel booking — verify HTTP 200
- [ ] Log all responses to `RESULTS.md`

---

### Step 2: Independent Playwright Verification
**Status:** ⬜ Not Started

- [ ] Log in to `mijn.2park.nl`
- [ ] Verify booking on dashboard (after create)
- [ ] Verify end time reflects extension
- [ ] Verify cancelled booking not in active
- [ ] Capture screenshots
- [ ] Log findings to `RESULTS.md`

---

### Step 3: Validate Original Discrepancies Are Fixed
**Status:** ⬜ Not Started

- [ ] Verify license plate normalized in all responses
- [ ] Verify end time matches actual website value
- [ ] Verify extend booking succeeded (HTTP 200 not 404)
- [ ] Compare against TP-001 results

---

### Step 4: Cleanup & Final Report
**Status:** ⬜ Not Started

- [ ] Ensure all test bookings cancelled
- [ ] Compile final `RESULTS.md` with full report
- [ ] Include comparison to TP-001

---

### Step 5: Testing & Verification
**Status:** ⬜ Not Started

- [ ] Test script executable
- [ ] No active test bookings remain

---

### Step 6: Documentation & Delivery
**Status:** ⬜ Not Started

- [ ] `RESULTS.md` complete
- [ ] Discoveries logged

---

## Reviews

| # | Type | Step | Verdict | File |
|---|------|------|---------|------|

---

## Discoveries

| Discovery | Disposition | Location |
|-----------|-------------|----------|

---

## Execution Log

| Timestamp | Action | Outcome |
|-----------|--------|---------|
| 2026-05-13 | Task staged | PROMPT.md and STATUS.md created |

---

## Blockers

*None*

---

## Notes

*Reserved for execution notes*
