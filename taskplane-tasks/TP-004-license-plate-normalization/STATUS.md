# TP-004: License Plate Normalization at API Boundary — Status

**Current Step:** Step 0: Preflight
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

- [x] Read `models.py` to understand current validation
- [x] Read `api.py` to identify all endpoints
- [x] Verify TP-003 DOM reference available

---

### Step 1: Add `normalize_license_plate()` to `models.py`
**Status:** 🟨 In Progress

- [x] Create `normalize_license_plate()` utility
- [x] Add unit tests for normalization
- [x] Update `validate_license_plate()` to normalize before validation

---

### Step 2: Apply Normalization at API Boundary
**Status:** 🟨 In Progress

- [x] Normalize plate in `create_booking()` (already handled via Pydantic validator)
- [x] Normalize plate in `extend_booking()`
- [x] Normalize plate in `cancel_booking()`
- [x] Update `README.md`

---

### Step 3: Testing & Verification
**Status:** ⬜ Not Started

- [ ] FULL test suite passing (`pytest`)
- [ ] All failures fixed

---

### Step 4: Documentation & Delivery
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
| 2026-05-12 21:56 | Task started | Runtime V2 lane-runner execution |
| 2026-05-12 21:56 | Step 0 started | Preflight |

---

## Blockers

*None*

---

## Notes

*Reserved for execution notes*
