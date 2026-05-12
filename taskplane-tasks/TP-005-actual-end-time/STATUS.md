# TP-005: Return Actual End Time from Website — Status

**Current Step:** Step 2: Update api.py to Propagate Actual End Time
**Status:** 🟡 In Progress
**Last Updated:** 2026-05-12
**Review Level:** 1
**Review Counter:** 0
**Iteration:** 1
**Size:** S

> **Hydration:** Checkboxes represent meaningful outcomes, not individual code
> changes. Workers expand steps when runtime discoveries warrant it.

---

### Step 0: Preflight
**Status:** ✅ Complete

- [x] Read `scraper.py` to understand current `create_booking()` flow
- [x] Read `get_active_reservations()` to understand time extraction
- [x] Verify TP-003 DOM reference available

---

### Step 1: Update `create_booking()` to Return Actual End Time
**Status:** ✅ Complete

- [x] Modify `create_booking()` to use scraped end time from `Reservation`
- [x] Add discrepancy warning log (>5 min difference)
- [x] Ensure returned dict includes actual scraped end time

---

### Step 2: Update `api.py` to Propagate Actual End Time
**Status:** ✅ Complete

- [x] Verify `create_booking` endpoint returns actual end time
- [x] Add discrepancy logging if needed

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
| 2026-05-12 21:59 | Task started | Runtime V2 lane-runner execution |
| 2026-05-12 21:59 | Step 0 started | Preflight |

---

## Blockers

*None*

---

## Notes

*Reserved for execution notes*
