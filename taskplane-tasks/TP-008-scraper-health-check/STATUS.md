# TP-008: `/health/scraper` Selector Check — Status

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

- [ ] Read `api.py` existing `/health` endpoint
- [ ] Read `scraper.py` to understand `_login()` and `_find_booking_card()`
- [ ] Read `errors.py` to understand error handling
- [ ] Verify TP-003, TP-006, TP-007 complete

---

### Step 1: Add `scraper_health_check()` to `TwoParkScraper`
**Status:** ⬜ Not Started

- [ ] Add `scraper_health_check()` method
- [ ] Verify tab navigation selectors
- [ ] Verify booking card selector exists
- [ ] Return status dict with results

---

### Step 2: Add `/health/scraper` Endpoint to `api.py`
**Status:** ⬜ Not Started

- [ ] Create `GET /health/scraper` endpoint
- [ ] Return HTTP 200 with status
- [ ] Include response time
- [ ] Add to API root documentation
- [ ] Add error handling and timeouts

---

### Step 3: Add `SELECTOR_MISMATCH` Error Code
**Status:** ⬜ Not Started

- [ ] Add error code to `ErrorCode` enum (if needed)
- [ ] Create exception class (if needed)

---

### Step 4: Testing & Verification
**Status:** ⬜ Not Started

- [ ] FULL test suite passing (`pytest`)
- [ ] All failures fixed

---

### Step 5: Documentation & Delivery
**Status:** ⬜ Not Started

- [ ] `README.md` updated
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
