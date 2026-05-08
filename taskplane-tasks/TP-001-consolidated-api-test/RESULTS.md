# TP-001: Consolidated End-to-End API Test Run — Results

**Test Date:** 2026-05-08
**API URL:** http://rasp-pi-4-service.local:8090
**Website:** https://mijn.2park.nl
**License Plate:** 51-PX-PN
**Bearer Token:** b6a32d1cde51a1dce7e21343f8233a501afe49cbf3bc0983263591fbf3e3ce43
**Test Script:** test_run.py

---

## Test Summary

| Step | Description | Result |
|------|------------|--------|
| 0 | Preflight | ✅ PASS |
| 1 | Create Booking | ✅ PASS (HTTP 201) |
| 2 | Extend Booking | ❌ FAIL (scraper selector mismatch) |
| 3 | List Active Bookings | ✅ PASS |
| 4 | Cancel Booking | ✅ PASS (HTTP 200) |
| 5 | Playwright: Dashboard Verification | ✅ PASS |
| 6 | Playwright: Scheduled Bookings Tab | ✅ PASS |
| 7 | Playwright: Cancelled Booking Not in Active | ✅ PASS |
| 8 | Cleanup Verification | ✅ PASS |

**Overall:** 8/9 PASS (Step 2 fails due to known scraper issue)

---

## Step 0: Preflight

### API Health Check
- **Endpoint:** `GET http://rasp-pi-4-service.local:8090/health`
- **HTTP Status:** 200
- **Response:** `{"status":"healthy","timestamp":"2026-05-08T14:57:10.451499+00:00","rate_limit":{"max_requests":10,"window_seconds":60}}`
- **Result:** ✅ PASS

### Credentials
- **TWOPARK_EMAIL:** markmooij@gmail.com (available in .env)
- **TWOPARK_PASSWORD:** configured
- **Result:** ✅ PASS

### Playwright
- **Python Import:** `from playwright.sync_api import sync_playwright` — OK
- **Browser Launch:** Chromium headless — OK
- **Result:** ✅ PASS

---

## Step 1: API Test Sequence — Create Booking

- **Endpoint:** `POST /api/bookings`
- **Request Body:** `{"license_plate": "51-PX-PN", "start_time": "now", "duration_minutes": 120}`
- **HTTP Status:** 201
- **Response Body:**
  ```json
  {"license_plate":"51-PX-PN","start_time":"2026-05-08T15:08:13.560048Z","end_time":"2026-05-08T17:08:13.560048Z","status":"active"}
  ```
- **Validation:**
  - License plate: 51-PX-PN ✅
  - Start time: 2026-05-08T15:08:13.560048Z ✅
  - End time: 2026-05-08T17:08:13.560048Z (120 min from start) ✅
  - Status: active ✅
- **Result:** ✅ PASS

---

## Step 2: API Test Sequence — Extend Booking

- **Endpoint:** `POST /api/bookings/51PXPN/extend` (plate normalized to 51PXPN)
- **Request Body:** `{"additional_minutes": 60}`
- **HTTP Status:** 404
- **Response Body:**
  ```json
  {"error":{"code":"BOOKING_NOT_FOUND","message":"Could not find booking UI for 51PXPN"}}
  ```
- **Analysis:** The API returned the booking (confirmed via GET /api/bookings), but the
  `extend_booking` endpoint calls the TwoParkScraper which navigates to the 2park.nl
  website to perform the extension via UI automation. The scraper uses placeholder
  selectors (`.parkapp-item`, `.extend-button`, `.btn-extend`) that do **not** match
  the current 2park.nl website structure.
  
  The actual website structure uses:
  - `tabs-container` / `tabs` for tab navigation
  - `tabText` for tab labels (Lopend, Gepland)
  - No `.parkapp-item` or `.extend-button` elements
  
  The scraper successfully found the reservation via `get_active_reservations()`
  (returned 1 reservation with license_plate "51PXPN") but failed when trying to
  find and click the extend button on the UI.

- **Result:** ❌ FAIL — Scraper selector mismatch (not an API bug, scraper needs update)

---

## Step 3: API Test Sequence — List Active Bookings

- **Endpoint:** `GET /api/bookings`
- **HTTP Status:** 200
- **Response Body:**
  ```json
  {"bookings":[{"license_plate":"51PXPN","start_time":"2026-05-08T17:08:00Z","end_time":"2026-05-08T23:59:00Z","status":"active"}],"count":1}
  ```
- **Validation:**
  - Booking present: ✅
  - License plate: 51PXPN (normalized — hyphens stripped by TwoPark website)
  - Start time: 2026-05-08T17:08:00Z
  - End time: 2026-05-08T23:59:00Z
  - Status: active ✅

- **Endpoint:** `GET /api/account/balance`
- **HTTP Status:** 200
- **Response Body:**
  ```json
  {"balance":14.37,"currency":"EUR","last_checked":"2026-05-08T15:08:55.680850Z"}
  ```
- **Result:** ✅ PASS

---

## Step 4: API Test Sequence — Cancel Booking

- **Endpoint:** `POST /api/bookings/51PXPN/cancel`
- **HTTP Status:** 200
- **Response Body:**
  ```json
  {"status":"cancelled","cancelled_at":"2026-05-08T15:09:07.618000Z"}
  ```
- **Validation:**
  - Status: cancelled ✅
  - Cancelled at: 2026-05-08T15:09:07.618000Z ✅
- **Post-cancel verification:** `GET /api/bookings` returns `{"bookings":[],"count":0}`
- **Result:** ✅ PASS

---

## Steps 5-7: Playwright Verification

### Step 5: Dashboard Verification (after cancel)
- **Screenshot:** `/tmp/dashboard_after_cancel.png`
- **Dashboard URL:** https://mijn.2park.nl/
- **Balance:** € 14,37
- **Active bookings:** "Geen lopende parkeeracties gevonden" (No active bookings)
- **Result:** ✅ PASS — Booking correctly not shown as active

### Step 6: Scheduled Bookings Tab
- **Action:** Clicked "Gepland" tab
- **Screenshot:** `/tmp/dashboard_scheduled.png`
- **Content:** "Geen geplande parkeeracties gevonden" (No scheduled bookings)
- **Result:** ✅ PASS

### Step 7: Cancelled Booking Not in Active
- **Action:** Switched back to "Lopend" tab
- **Result:** ✅ PASS — License plate "51PXPN" not found in active bookings body text

---

## Step 8: Cleanup Verification

- **Endpoint:** `GET /api/bookings`
- **Response:** `{"bookings":[],"count":0}`
- **Result:** ✅ PASS — No active test bookings remain

---

## Discrepancies Found

1. **License plate normalization:** API returns "51-PX-PN" but the TwoPark website
   stores "51PXPN" (hyphens stripped). The API endpoint uses the original format
   in the response but the scraper normalizes it internally.

2. **Booking duration discrepancy:** API calculated 120 min from start time, but
   the TwoPark website set the booking to end of day (23:59). The scraper's
   create_booking navigates to the website form and the website's own logic
   determines the actual booking times.

3. **Scraper selector mismatch:** The `extend_booking` and `cancel_booking` methods
   in scraper.py use placeholder selectors that don't match the current 2park.nl
   website DOM. The website uses `.tabs-container`, `.tabText`, etc. for navigation
   and doesn't have `.parkapp-item` or `.extend-button` elements.

---

## Screenshots

| Screenshot | Description |
|-----------|-------------|
| `/tmp/dashboard_after_cancel.png` | Dashboard showing no active bookings after cancel |
| `/tmp/dashboard_scheduled.png` | Scheduled bookings tab (empty) |

---

## Files Produced

- `test_run.py` — Consolidated test script (executable)
- `RESULTS.md` — This file (test report)
- `STATUS.md` — Execution state
