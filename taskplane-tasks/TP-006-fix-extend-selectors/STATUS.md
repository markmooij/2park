# TP-006: Fix `extend_booking()` Selectors — Status

**Current Step:** Step 1: Rewrite `extend_booking()` with Correct Selectors
**Status:** 🟡 In Progress
**Last Updated:** 2026-05-12
**Review Level:** 2
**Review Counter:** 0
**Iteration:** 1
**Size:** M

> **Hydration:** Checkboxes represent meaningful outcomes, not individual code
> changes. Workers expand steps when runtime discoveries warrant it.

---

### Step 0: Preflight
**Status:** ✅ Complete

- [x] Read `scraper.py` `extend_booking()` to understand current flow
- [x] Read TP-003 `DOM_REFERENCE.md` for actual selectors
- [x] Verify DOM reference includes extend button selectors

---

### Step 1: Rewrite `extend_booking()` with Correct Selectors
**Status:** 🟨 In Progress

- [x] Navigate to dashboard (not `/parkings`)
- [x] Click "Lopend" tab with correct selectors
- [x] Find booking card with real card selector
- [x] Click extend button with real selectors
- [x] Fill in additional minutes and submit
- [x] Read back actual new end time from website
- [x] > Code review checkpoint

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
| 2026-05-12 22:02 | Task started | Runtime V2 lane-runner execution |
| 2026-05-12 22:02 | Step 0 started | Preflight |

---

## Blockers

*None*

---

## Notes

*Reserved for execution notes*
