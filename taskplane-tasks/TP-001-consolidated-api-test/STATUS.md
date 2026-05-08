# TP-001: Consolidated End-to-End API Test Run — Status

**Current Step:** Not Started
**Status:** 🔵 Ready for Execution
**Last Updated:** 2026-05-08
**Review Level:** 1
**Review Counter:** 0
**Iteration:** 0
**Size:** M

> **Hydration:** Checkboxes represent meaningful outcomes, not individual code
> changes. Workers expand steps when runtime discoveries warrant it.

---

### Step 0: Preflight
**Status:** ⬜ Not Started

- [ ] Verify API is reachable: `curl http://rasp-pi-4-service.local:8090/health`
- [ ] Verify credentials are available (TWOPARK_EMAIL and TWOPARK_PASSWORD env vars or stored securely)
- [ ] Verify Playwright is installed: `python -c "from playwright.sync_api import sync_playwright; print('OK')"`

---

### Step 1: API Test Sequence — Create Booking
**Status:** ⬜ Not Started

- [ ] Create a booking for license plate `51-PX-PN` with duration 120 minutes using `start_time: "now"`
- [ ] Verify the API returns HTTP 201 with correct booking details
- [ ] Log the response body and timestamp to RESULTS.md

---

### Step 2: API Test Sequence — Extend Booking
**Status:** ⬜ Not Started

- [ ] Extend the booking for `51-PX-PN` by 60 additional minutes
- [ ] Verify the API returns HTTP 200 with the new_end_time
- [ ] Verify the new_end_time is exactly 60 minutes past the original end_time
- [ ] Log the response body to RESULTS.md

---

### Step 3: API Test Sequence — List Active Bookings
**Status:** ⬜ Not Started

- [ ] GET `/api/bookings` to confirm the booking is still active
- [ ] Verify the booking appears in the list with correct license_plate and status
- [ ] GET `/api/account/balance` to confirm account is accessible
- [ ] Log responses to RESULTS.md

---

### Step 4: API Test Sequence — Cancel Booking
**Status:** ⬜ Not Started

- [ ] POST to `/api/bookings/51-PX-PN/cancel`
- [ ] Verify the API returns HTTP 200 with status: "cancelled"
- [ ] Log the response body to RESULTS.md

---

### Step 5: Independent Playwright Verification — Booking Created
**Status:** ⬜ Not Started

- [ ] Launch a separate Playwright browser session
- [ ] Log in to `https://mijn.2park.nl/login` with credentials
- [ ] Wait for dashboard to load (60s+ timeout)
- [ ] Verify the booking for `51-PX-PN` appears on the dashboard
- [ ] Record and log findings to RESULTS.md

---

### Step 6: Independent Playwright Verification — Booking Extended
**Status:** ⬜ Not Started

- [ ] Refresh the dashboard
- [ ] Verify the booking end time reflects the extension (+60 minutes)
- [ ] Log findings to RESULTS.md

---

### Step 7: Independent Playwright Verification — Booking Cancelled
**Status:** ⬜ Not Started

- [ ] Refresh the dashboard
- [ ] Verify the cancelled booking no longer appears in active bookings
- [ ] Log findings to RESULTS.md

---

### Step 8: Cleanup & Documentation
**Status:** ⬜ Not Started

- [ ] Ensure all test bookings are cancelled (verify via API)
- [ ] Compile final RESULTS.md with full report
- [ ] Include timestamps, HTTP status codes, response bodies, and screenshots

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
