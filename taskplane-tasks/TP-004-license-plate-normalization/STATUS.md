# TP-004: License Plate Normalization at API Boundary — Status

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

- [ ] Read `models.py` to understand current validation
- [ ] Read `api.py` to identify all endpoints
- [ ] Verify TP-003 DOM reference available

---

### Step 1: Add `normalize_license_plate()` to `models.py`
**Status:** ⬜ Not Started

- [ ] Create `normalize_license_plate()` utility
- [ ] Add unit tests for normalization
- [ ] Update `validate_license_plate()` to normalize before validation

---

### Step 2: Apply Normalization at API Boundary
**Status:** ⬜ Not Started

- [ ] Normalize plate in `create_booking()`
- [ ] Normalize plate in `extend_booking()`
- [ ] Normalize plate in `cancel_booking()`
- [ ] Update `README.md`

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

---

## Blockers

*None*

---

## Notes

*Reserved for execution notes*
