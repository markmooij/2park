# TP-006: Fix `extend_booking()` Selectors — Status

**Current Step:** Not Started
**Status:** 🔵 Ready for Execution
**Last Updated:** 2026-05-08
**Review Level:** 2
**Review Counter:** 0
**Iteration:** 0
**Size:** M

> **Hydration:** Checkboxes represent meaningful outcomes, not individual code
> changes. Workers expand steps when runtime discoveries warrant it.

---

### Step 0: Preflight
**Status:** ⬜ Not Started

- [ ] Read `scraper.py` `extend_booking()` to understand current flow
- [ ] Read TP-003 `DOM_REFERENCE.md` for actual selectors
- [ ] Verify DOM reference includes extend button selectors

---

### Step 1: Rewrite `extend_booking()` with Correct Selectors
**Status:** ⬜ Not Started

- [ ] Navigate to dashboard (not `/parkings`)
- [ ] Click "Lopend" tab with correct selectors
- [ ] Find booking card with real card selector
- [ ] Click extend button with real selectors
- [ ] Fill in additional minutes and submit
- [ ] Read back actual new end time from website

---

### Step 2: Handle Edge Cases
**Status:** ⬜ Not Started

- [ ] Return proper `BookingNotFoundException` when no booking found
- [ ] Log available buttons and return `ScrapeErrorException` when extend button missing
- [ ] Take screenshot on failure

---

### Step 3: Testing & Verification
**Status:** ⬜ Not Started

- [ ] FULL test suite passing (`pytest`)
- [ ] All failures fixed

---

### Step 4: Documentation & Delivery
**Status:** ⬜ Not Started

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
| 2026-05-08 | Task staged | PROMPT.md and STATUS.md created |

---

## Blockers

*None*

---

## Notes

*Reserved for execution notes*
