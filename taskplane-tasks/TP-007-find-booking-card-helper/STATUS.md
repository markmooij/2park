# TP-007: Shared `_find_booking_card()` Helper — Status

**Current Step:** Not Started
**Status:** 🔵 Ready for Execution
**Last Updated:** 2026-05-08
**Review Level:** 1
**Review Counter:** 0
**Iteration:** 0
**Size:** S

> **Hydration:** Checkboxes represent meaningful outcomes, not individual code
> changes. Workers expand steps when runtime discoveries warrant it.

---

### Step 0: Preflight
**Status:** ⬜ Not Started

- [ ] Read `scraper.py` to understand duplicated card-finding logic
- [ ] Identify shared logic between `extend_booking()` and `cancel_booking()`
- [ ] Verify TP-003 and TP-006 complete

---

### Step 1: Create `_find_booking_card()` Helper
**Status:** ⬜ Not Started

- [ ] Add `_find_booking_card()` method with correct selectors
- [ ] Return dict with card element, license plate, start/end times
- [ ] Handle license plate normalization
- [ ] Log debugging info

---

### Step 2: Refactor Callers to Use the Helper
**Status:** ⬜ Not Started

- [ ] Update `extend_booking()` to use `_find_booking_card()`
- [ ] Update `cancel_booking()` to use `_find_booking_card()`
- [ ] Verify both methods still work correctly

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
