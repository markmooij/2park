# TP-006: Fix `extend_booking()` Selectors — Status

**Current Step:** Step 4: Documentation & Delivery
**Status:** ✅ Complete
**Last Updated:** 2026-05-12
**Review Level:** 2
**Review Counter:** 2
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
**Status:** ✅ Complete

- [x] Navigate to dashboard (not `/parkings`)
- [x] Click "Lopend" tab with correct selectors
- [x] Find booking card with real card selector
- [x] Click extend button with real selectors
- [x] Fill in additional minutes and submit
- [x] Read back actual new end time from website
- [x] > Code review checkpoint

---

### Step 2: Handle Edge Cases
**Status:** ✅ Complete

- [x] Return proper `BookingNotFoundException` when no booking found
- [x] Log available buttons and return `ScrapeErrorException` when extend button missing
- [x] Take screenshot on failure

---

### Step 3: Testing & Verification
**Status:** ✅ Complete

- [x] FULL test suite passing (`pytest`) — 24 passed, 0 failures
- [x] All failures fixed (none)

---

### Step 4: Documentation & Delivery
**Status:** ✅ Complete

- [x] Discoveries logged

---

## Reviews

| # | Type | Step | Verdict | File |
|---|------|------|---------|------|
| R001 | code | 1 | APPROVE | — |
| R002 | code | 2 | APPROVE | — |

---

## Discoveries

| Discovery | Disposition | Location |
|-----------|-------------|----------|
| `.parkapp-item` selector confirmed working for booking cards | Used in implementation | `scraper.py` |
| `.extend-context-menu-button` is the correct extend button class | Used in implementation | `scraper.py` |
| `.license-plate.active` is the correct license plate selector (not `.license-plate-text`) | Used with fallback | `scraper.py` |
| Dashboard URL is `https://mijn.2park.nl/` (not `/parkings`) | Fixed navigation | `scraper.py` |
| Extend form fields not visible in DOM audit — used generic input selectors | Fallback approach | `scraper.py` |
| Tab navigation uses `.tabs-container button` elements with text content | Used for "Lopend" tab | `scraper.py` |

---

## Execution Log

| Timestamp | Action | Outcome |
|-----------|--------|---------|
| 2026-05-08 | Task staged | PROMPT.md and STATUS.md created |
| 2026-05-12 22:02 | Task started | Runtime V2 lane-runner execution |
| 2026-05-12 22:02 | Step 0 started | Preflight |
| 2026-05-12 22:10 | Worker iter 1 | done in 482s, tools: 63 |
| 2026-05-12 22:10 | Task complete | .DONE created |

---

## Blockers

*None*

---

## Notes

*Reserved for execution notes*
| 2026-05-12 22:06 | Review R001 | code Step 1: APPROVE |
| 2026-05-12 22:09 | Review R002 | code Step 2: APPROVE |
