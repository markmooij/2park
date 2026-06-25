# 2Park API & Checker

REST API and CLI tool for managing parking reservations on [2park.nl](https://mijn.2park.nl).

## Quick Start (Docker)

```bash
cp .env.example .env
nano .env  # Add your 2Park credentials + generate an API token

# Generate a secure API token
openssl rand -hex 32

# Build and run
docker compose up -d

# Test
curl http://localhost:8090/health
curl http://localhost:8090/health/scraper
curl -H "Authorization: Bearer YOUR_API_TOKEN" http://localhost:8090/api/account/balance
```

## Quick Start (Local)

```bash
uv sync
uv run playwright install chromium
cp .env.example .env
nano .env
python api.py
```

## API Endpoints

All endpoints except `/health` and `/health/scraper` require a Bearer token in the `Authorization` header.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check (no auth) |
| `/health/scraper` | GET | Scraper selector health check (no auth) |
| `/api/account/balance` | GET | Get current account balance |
| `/api/bookings` | GET | List all active bookings |
| `/api/bookings` | POST | Create a new booking |
| `/api/bookings/{license_plate}/extend` | POST | Extend an existing booking |
| `/api/bookings/{license_plate}/cancel` | POST | Cancel a booking |

## License Plate Normalization

All license plates are **normalized at the API boundary**: hyphens and spaces are stripped, and letters are uppercased. This matches the format used by 2park.nl.

| Input | Normalized |
|-------|------------|
| `51-PXPN` | `51PXPN` |
| `AB-12-CD` | `AB12CD` |
| `ab-12-x` | `AB12X` |
| `51PXPN` | `51PXPN` (already normalized) |

Normalization is idempotent — sending a normalized plate back as input produces the same result.

## curl Examples

All examples use port `8090` (default for both Docker and local). Replace `YOUR_API_TOKEN` with your actual token.

### Scraper Health Check

```bash
curl http://localhost:8090/health/scraper
```

```json
{
  "status": "ok",
  "selectors_checked": [
    {"selector": ".tabs-container", "label": "Tab container", "present": true},
    {"selector": ".tabText", "label": "Tab text element", "present": true},
    {"selector": ".parkapp-item", "label": "Booking card item", "present": true},
    {"selector": ".license-plate.active", "label": "License plate display", "present": true},
    {"selector": ".extend-context-menu-button", "label": "Extend button", "present": true},
    {"selector": ".stop-context-menu-button", "label": "Stop/Cancel button", "present": true},
    {"selector": ".time-container", "label": "Time display container", "present": true},
    {"selector": ".parking-action-balance", "label": "Balance display", "present": true}
  ],
  "missing_selectors": [],
  "timestamp": "2026-03-31T13:27:13.889549Z",
  "total_response_time_ms": 12500.3
}
```

When `"status"` is `"degraded"`, some selectors are missing from the dashboard — the scraper may produce incorrect results. When `"status"` is `"error"`, the scraper could not reach the 2Park website at all.

### Get Account Balance

```bash
curl -H "Authorization: Bearer YOUR_API_TOKEN" \
  http://localhost:8090/api/account/balance
```

```json
{
  "balance": 15.97,
  "currency": "EUR",
  "last_checked": "2026-03-31T13:27:13.889549Z"
}
```

### List Active Bookings

```bash
curl -H "Authorization: Bearer YOUR_API_TOKEN" \
  http://localhost:8090/api/bookings
```

```json
{
  "bookings": [
    {
      "license_plate": "31TJHV",
      "start_time": "2026-03-31T14:46:00Z",
      "end_time": "2026-03-31T17:00:00Z",
      "status": "active"
    }
  ],
  "count": 1
}
```

### Create a Booking

```bash
curl -X POST http://localhost:8090/api/bookings \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "license_plate": "51-PXPN",
    "start_time": "now",
    "duration_minutes": 120
  }'
```

```json
{
  "license_plate": "51PXPN",
  "start_time": "2026-03-31T13:27:13Z",
  "end_time": "2026-03-31T15:27:13Z",
  "status": "active"
}
```

- `license_plate`: Dutch format (`AB-12-CD`, `51PXPN`, `51-PXPN`)
- `start_time`: `"now"` or ISO 8601 string (e.g. `"2026-04-01T09:00:00Z"`)
- `duration_minutes`: 1-1440

### Extend a Booking

```bash
curl -X POST http://localhost:8090/api/bookings/51-PXPN/extend \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"additional_minutes": 60}'
```

```json
{
  "license_plate": "51PXPN",
  "new_end_time": "2026-03-31T16:27:13Z"
}
```

### Cancel a Booking

```bash
curl -X POST http://localhost:8090/api/bookings/51-PXPN/cancel \
  -H "Authorization: Bearer YOUR_API_TOKEN"
```

```json
{
  "status": "cancelled",
  "cancelled_at": "2026-03-31T13:30:00Z"
}
```

## Error Handling

All errors use a consistent JSON format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable description"
  }
}
```

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INVALID_TOKEN` | 401 | Missing or invalid Bearer token |
| `LOGIN_FAILED` | 401 | 2Park login failed (bad credentials or site down) |
| `VALIDATION_ERROR` | 422 | Invalid request body (bad license plate, missing fields) |
| `INVALID_TIME` | 400 | Unparseable `start_time` value |
| `BOOKING_NOT_FOUND` | 404 | No active booking for the given plate |
| `BOOKING_CONFLICT` | 409 | Active booking already exists for this plate |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests (check `X-RateLimit-Reset` header) |
| `TIMEOUT_ERROR` | 504 | Browser operation timed out |
| `BROWSER_ERROR` | 500 | Browser automation failure |
| `INTERNAL_ERROR` | 500 | Unexpected server error |

### Rate Limit Headers

Every response includes rate limit headers:

```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 8
X-RateLimit-Reset: 45
```

## Configuration

### Environment Variables

**Required:**

| Variable | Description |
|----------|-------------|
| `TWOPARK_EMAIL` | Your 2Park account email |
| `TWOPARK_PASSWORD` | Your 2Park account password |
| `API_TOKEN` | Bearer token for API authentication |

**Optional:**

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `8090` | API server port |
| `RATE_LIMIT_REQUESTS` | `10` | Max requests per window |
| `RATE_LIMIT_WINDOW_SECONDS` | `60` | Rate limit window (seconds) |
| `BROWSER_TIMEOUT` | `30` | Browser launch timeout (10-300s) |
| `NAVIGATION_TIMEOUT` | `30` | Page navigation timeout (10-300s) |
| `SELECTOR_TIMEOUT` | `10` | Element selector timeout (10-300s) |
| `LOG_LEVEL` | `INFO` | Logging level |

## Docker

```bash
# Build and start
docker compose up -d

# View logs
docker logs -f 2park-api

# Stop
docker compose down

# Rebuild after code changes
docker compose up -d --build
```

The API is available at `http://localhost:8090`. The container includes a health check that runs every 30 seconds.

## Home Assistant Integration

The API is designed to work with Home Assistant's `rest` and `rest_command` integrations for automated parking based on presence detection.

### Quick Setup (Files from `home-assistant/`)

The easiest way to set up the Home Assistant integration is to copy the files from the `home-assistant/` directory into your HA `/config/` folder:

```bash
scp home-assistant/*.yaml root@homeassistant.local:/config/
```

Or copy manually via the File Editor add-on in HA.

Then add these lines to your `/config/configuration.yaml`:

```yaml
sensor: !include sensors.yaml
template: !include template.yaml
rest_command: !include rest_commands.yaml
```

Finally, restart Home Assistant: **Settings → System → Power & Startup → Restart**.

### What You Get

| Component | Entity IDs |
|-----------|------------|
| **REST Sensors** | `sensor.2park_balance`, `sensor.2park_bookings_count` |
| **Template Sensors** | `sensor.2park_summary`, `sensor.2park_bookings_dynamic`, `binary_sensor.2park_low_balance` |
| **REST Commands** | `rest_command.cancel_twopark_booking`, `rest_command.extend_twopark_booking`, `rest_command.create_twopark_booking` |

### Dashboard Card (Dynamic)

The dashboard card is **fully dynamic** — it reads active bookings from the API and displays:

- **Balance** card showing current account balance
- **Bookings** card showing number of active bookings
- **Booking rows** for each active booking, each with:
  - License plate and end time display
  - **Cancel** button (with confirmation dialog)
  - **+60m** button to extend the booking by one hour
- **No Active Bookings** placeholder when count is 0

No hardcoded license plates required — the card adapts automatically based on what the API returns.

#### Adding the Card to Your Dashboard

1. Go to your dashboard → Edit → Three dots → **Edit as YAML**
2. Paste the content from `home-assistant/native-cards-improved.yaml`
3. Save

#### How It Works

The `sensor.2park_bookings_dynamic` template sensor (defined in `template.yaml`) parses the `bookings` JSON array from the API and exposes each booking's details as individual attributes:

| Attribute | Example | Description |
|-----------|---------|-------------|
| `booking_1_plate` | `51PXPN` | License plate of booking 1 |
| `booking_1_start` | `2026-03-31T14:46:00Z` | Start time of booking 1 |
| `booking_1_end` | `2026-03-31T17:00:00Z` | End time of booking 1 |
| `booking_1_status` | `active` | Status of booking 1 |
| `booking_2_plate` ... `booking_5_*` | ... | Same for bookings 2-5 |

Supports up to **5 concurrent bookings**. The dashboard card uses `conditional` cards to show rows only when a booking exists, and `button` cards with Jinja2 templates to dynamically set the license plate for cancel/extend actions.

#### Forcing a Refresh

The REST sensors update every 5 minutes. To force an immediate refresh:

```yaml
service: homeassistant.update_entity
target:
  entity_id:
    - sensor.2park_balance
    - sensor.2park_bookings_count
```

### Automations

Copy these automations via **Settings → Automations → Create Automation → Edit as YAML**. Update the license plates and persons to match your household.

#### Book on Arrival (Ida)

Triggers when Ida arrives home, books parking for `51-PX-PN` for 120 minutes, and sends a push notification to her phone. This replaces the old separate "Ida waarschuwing" automation.

```yaml
alias: "Parking - Auto Book on Arrival"
trigger:
  - platform: state
    entity_id: person.ida
    from: "not_home"
    to: "home"
condition:
  - condition: not
    conditions:
      - condition: state
        entity_id: binary_sensor.2park_low_balance
        state: "on"
action:
  - service: rest_command.create_twopark_booking
    data:
      license_plate: "51PXPN"
      duration_minutes: 120
  - service: notify.notify
    data:
      title: "Parking Booked"
      message: "Parking booked for Ida (51PXPN) for 120 minutes."
  - service: notify.mobile_app_2201123g
    data:
      message: "Parking booked for 51-PX-PN! Check de parkeerapp."
mode: single
```

To adapt this for another person, change the `entity_id` under `trigger`, update the license plate and duration, and replace the mobile notify service with the correct device.

#### Cancel on Departure

Triggers when a household member leaves home, canceling their active booking.

```yaml
alias: "Parking - Cancel on Departure"
trigger:
  - platform: state
    entity_id:
      - person.mark
      - person.ida
    from: "home"
    to: "not_home"
action:
  - variables:
      plates:
        person.mark: "51PXPN"
        person.ida: "51PXPN"
  - service: rest_command.cancel_twopark_booking
    data:
      license_plate: "{{ plates[trigger.entity_id] }}"
mode: single
```

#### Low Balance Alert

Sends a notification when the parking balance drops below €5.00.

```yaml
alias: "Parking - Alert on Low Balance"
trigger:
  - platform: state
    entity_id: binary_sensor.2park_low_balance
    to: "on"
action:
  - service: notify.notify
    data:
      title: "Low Parking Balance"
      message: >
        2Park balance is {{ states('sensor.2park_balance') }} EUR.
        Top up to keep automatic parking working.
mode: single
```

### Home Assistant Troubleshooting

| Issue | Solution |
|-------|----------|
| Timeout errors | Set `timeout: 120` on all rest_commands. Browser operations take 5-15s. |
| Connection refused | Ensure API container is running and reachable from HA network |
| `LOGIN_FAILED` errors | Check 2Park credentials. The site may be temporarily down. |
| Stale balance data | Lower `scan_interval` or call `homeassistant.update_entity` |
| Rate limit exceeded | Wait for `X-RateLimit-Reset` seconds, or increase `RATE_LIMIT_REQUESTS` |
| Sensor shows `unavailable` | Increase `timeout: 30` to `timeout: 60` in `sensors.yaml` — the browser can take 15-30s |
| `binary_sensor.2park_low_balance` not found | Ensure `template: !include template.yaml` is in `configuration.yaml` and restart HA |

## CLI Usage

The CLI tool displays active reservations and balance in your terminal:

```bash
./run.sh
```

Or manually:

```bash
uv run python main.py
```

```
==================================================
ACTIVE RESERVATIONS
==================================================
Reservation 1:
  Name: John Doe
  License Plate: AB-123-CD
  Start Time: 09:00
  End Time: 17:00
==================================================
ACCOUNT BALANCE
==================================================
EUR 25.50
==================================================
```

## Architecture

```
api.py              # FastAPI REST API server
scraper.py          # Stateless Playwright browser automation
models.py           # Pydantic request/response models
errors.py           # Error codes and exception handling
auth.py             # Bearer token authentication
rate_limit.py       # Rate limiting middleware
main.py             # CLI script
run.sh              # CLI convenience script
Dockerfile          # Container image
docker-compose.yml  # Docker Compose configuration
```

Each API request independently: authenticates the token, launches a headless browser, logs in to 2Park, performs the operation, and cleans up. This stateless design avoids session leaks and enables horizontal scaling.

## Testing

```bash
uv sync --extra dev
pytest tests/ -v
```

| Test File | Tests |
|-----------|-------|
| `test_license_plate.py` | 14 |
| `test_time_parsing.py` | 3 |

Integration tests against a running server:

```bash
docker compose up -d
python test_api.py
```

**Warning:** Booking operations in `test_api.py` create real bookings on your 2Park account.

## Security

- Never commit `.env` (already in `.gitignore`)
- Generate a strong API token: `openssl rand -hex 32`
- Don't expose the API directly to the internet without HTTPS
- Credentials are only transmitted to 2park.nl via the browser session

## Disclaimer

This is a personal hobby project. It automates interaction with 2park.nl using browser automation. Use at your own risk and in accordance with 2park.nl's Terms of Service. The author is not affiliated with 2park.nl.

## Documentation

- **[API.md](API.md)** - Complete API reference
- **[QUICKSTART.md](QUICKSTART.md)** - CLI quick reference
- **[CHANGES.md](CHANGES.md)** - Migration guide from previous version
- **[ROADMAP.md](ROADMAP.md)** - Planned features
