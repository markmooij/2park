# TP-005: Return Actual End Time from Website — Status

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

- [ ] Read `scraper.py` to understand current `create_booking()` flow
- [ ] Read `get_active_reservations()` to understand time extraction
- [ ] Verify TP-003 DOM reference available

---

### Step 1: Update `create_booking()` to Return Actual End Time
**Status:** ⬜ Not Started

- [ ] Modify `create_booking()` to use scraped end time from `Reservation`
- [ ] Add discrepancy warning log (>5 min difference)
- [ ] Ensure returned dict includes actual scraped end time

---

### Step 2: Update `api.py` to Propagate Actual End Time
**Status:** ⬜ Not Started

- [ ] Verify `create_booking` endpoint returns actual end time
- [ ] Add discrepancy logging if needed

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
