# TP-008: `/health/scraper` Selector Check — Status

**Current Step:** Step 1: Add `scraper_health_check()` to `TwoParkScraper`
**Status:** 🟡 In Progress
**Last Updated:** 2026-05-12
**Review Level:** 2
**Review Counter:** 1
**Iteration:** 1
**Size:** M

> **Hydration:** Checkboxes represent meaningful outcomes, not individual code
> changes. Workers expand steps when runtime discoveries warrant it.

---

### Step 0: Preflight
**Status:** ✅ Complete

- [x] Read `api.py` existing `/health` endpoint
- [x] Read `scraper.py` to understand `_login()` and `_find_booking_card()`
- [x] Read `errors.py` to understand error handling
- [x] Verify TP-003, TP-006, TP-007 complete

---

### Step 1: Add `scraper_health_check()` to `TwoParkScraper`
**Status:** 🟨 In Progress

- [x] Add `scraper_health_check()` method
- [x] Verify tab navigation selectors
- [x] Verify booking card selector exists
- [x] Return status dict with results

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
| 2026-05-12 22:14 | Task started | Runtime V2 lane-runner execution |
| 2026-05-12 22:14 | Step 0 started | Preflight |

---

## Blockers

*None*

---

## Notes

*Reserved for execution notes*
| 2026-05-12 22:16 | Review R001 | plan Step 1: APPROVE |
