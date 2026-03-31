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

All endpoints except `/health` require a Bearer token in the `Authorization` header.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check (no auth) |
| `/api/account/balance` | GET | Get current account balance |
| `/api/bookings` | GET | List all active bookings |
| `/api/bookings` | POST | Create a new booking |
| `/api/bookings/{license_plate}/extend` | POST | Extend an existing booking |
| `/api/bookings/{license_plate}/cancel` | POST | Cancel a booking |

## curl Examples

All examples use port `8090` (default for both Docker and local). Replace `YOUR_API_TOKEN` with your actual token.

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
  "license_plate": "51-PXPN",
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
  "license_plate": "51-PXPN",
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

### Sensors: Balance and Bookings

Add to `configuration.yaml`:

```yaml
rest:
  - resource: "http://YOUR_2PARK_SERVER:8090/api/account/balance"
    method: GET
    headers:
      Authorization: "Bearer YOUR_API_TOKEN"
    scan_interval: 7200
    sensor:
      - name: "2Park Balance"
        value_template: "{{ value_json.balance }}"
        device_class: monetary
        unit_of_measurement: "EUR"
        icon: "mdi:cash"

  - resource: "http://YOUR_2PARK_SERVER:8090/api/bookings"
    method: GET
    headers:
      Authorization: "Bearer YOUR_API_TOKEN"
    scan_interval: 7200
    sensor:
      - name: "2Park Active Bookings"
        value_template: "{{ value_json.count }}"
        json_attributes:
          - bookings
        icon: "mdi:car"

template:
  - binary_sensor:
      - name: "2Park Low Balance"
        device_class: problem
        icon: "mdi:alert-circle"
        state: "{{ states('sensor.2park_balance') | float(0) < 5.0 }}"
```

### REST Commands

```yaml
rest_command:
  2park_create_booking:
    url: "http://YOUR_2PARK_SERVER:8090/api/bookings"
    method: POST
    headers:
      Authorization: "Bearer YOUR_API_TOKEN"
      Content-Type: "application/json"
    payload: >
      {"license_plate": "{{ license_plate }}", "start_time": "now", "duration_minutes": {{ duration_minutes }}}
    timeout: 120

  2park_cancel_booking:
    url: "http://YOUR_2PARK_SERVER:8090/api/bookings/{{ license_plate }}/cancel"
    method: POST
    headers:
      Authorization: "Bearer YOUR_API_TOKEN"
    timeout: 120

  2park_extend_booking:
    url: "http://YOUR_2PARK_SERVER:8090/api/bookings/{{ license_plate }}/extend"
    method: POST
    headers:
      Authorization: "Bearer YOUR_API_TOKEN"
      Content-Type: "application/json"
    payload: >
      {"additional_minutes": {{ additional_minutes }}}
    timeout: 120
```

**Important:** Set `timeout: 120` on all rest commands. Each API call launches a headless browser and logs in to 2park.nl, which takes 5-15 seconds. The default Home Assistant timeout of 10 seconds is too short.

### Automation: Book on Arrival

```yaml
alias: "Parking - Auto Book on Arrival"
trigger:
  - platform: state
    entity_id:
      - person.mark
      - person.janneke
    from: "not_home"
    to: "home"
condition:
  - condition: numeric_state
    entity_id: sensor.2park_balance
    above: 5.0
action:
  - variables:
      plates:
        person.mark: "51PXPN"
        person.janneke: "AB-12-CD"
      durations:
        person.mark: 120
        person.janneke: 60
  - service: rest_command.2park_create_booking
    data:
      license_plate: "{{ plates[trigger.entity_id] }}"
      duration_minutes: "{{ durations[trigger.entity_id] }}"
    response_variable: result
  - service: notify.notify
    data:
      title: "Parking Booked"
      message: >
        Parking booked for {{ trigger.to_state.name }}
        ({{ plates[trigger.entity_id] }}) for {{ durations[trigger.entity_id] }} minutes.
mode: single
```

### Automation: Cancel on Departure

```yaml
alias: "Parking - Cancel on Departure"
trigger:
  - platform: state
    entity_id:
      - person.mark
      - person.janneke
    from: "home"
    to: "not_home"
action:
  - variables:
      plates:
        person.mark: "51PXPN"
        person.janneke: "AB-12-CD"
  - service: rest_command.2park_cancel_booking
    data:
      license_plate: "{{ plates[trigger.entity_id] }}"
mode: single
```

### Automation: Low Balance Alert

```yaml
alias: "Parking - Low Balance Alert"
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

### Dashboard Card

```yaml
type: entities
title: 2Park Parking
entities:
  - entity: sensor.2park_balance
    name: Balance
    icon: mdi:cash
  - entity: sensor.2park_active_bookings
    name: Active Bookings
    icon: mdi:car
  - entity: binary_sensor.2park_low_balance
    name: Low Balance
    icon: mdi:alert-circle
```

### Home Assistant Troubleshooting

| Issue | Solution |
|-------|----------|
| Timeout errors | Set `timeout: 120` on all rest_commands. Browser operations take 5-15s. |
| Connection refused | Ensure API container is running and reachable from HA network |
| `LOGIN_FAILED` errors | Check 2Park credentials. The site may be temporarily down. |
| Stale balance data | Lower `scan_interval` or call `homeassistant.update_entity` |
| Rate limit exceeded | Wait for `X-RateLimit-Reset` seconds, or increase `RATE_LIMIT_REQUESTS` |

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
| `test_license_plate.py` | 4 |
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
