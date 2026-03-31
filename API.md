# 2Park API Documentation

Complete REST API for managing parking bookings on 2park.nl

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Base URL](#base-url)
- [Endpoints](#endpoints)
  - [Health Check](#health-check)
  - [Get Account Balance](#get-account-balance)
  - [List Active Bookings](#list-active-bookings)
  - [Create Booking](#create-booking)
  - [Extend Booking](#extend-booking)
  - [Cancel Booking](#cancel-booking)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [Setup & Running](#setup--running)

## Overview

The 2Park API provides a stateless REST interface for automating parking management on 2park.nl. Each request creates a new browser session, performs the operation, and cleans up resources automatically.

**Key characteristics:**
- Stateless architecture (no persistent sessions)
- Bearer token authentication
- Consistent error response format across all endpoints
- All datetimes in ISO 8601 / UTC
- Rate limiting by client IP
- Request tracing via `X-Request-ID` header

## Authentication

All endpoints except `/health` and `/` require a Bearer token.

### Setup

1. Generate a token:
```bash
openssl rand -hex 32
```

2. Set it in `.env`:
```bash
API_TOKEN=your-generated-token-here
```

3. Include in all requests:
```
Authorization: Bearer your-generated-token-here
```

## Base URL

| Environment | URL |
|-------------|-----|
| Docker (default) | `http://localhost:8090` |
| Local development | `http://localhost:8090` (configurable via `PORT` env var) |

## Endpoints

### Health Check

`GET /health`

No authentication required.

```bash
curl http://localhost:8090/health
```

```json
{
  "status": "healthy",
  "timestamp": "2026-03-31T13:22:02Z",
  "rate_limit": {
    "max_requests": 10,
    "window_seconds": 60
  }
}
```

---

### Get Account Balance

`GET /api/account/balance`

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8090/api/account/balance
```

**Response:** `200 OK`
```json
{
  "balance": 15.97,
  "currency": "EUR",
  "last_checked": "2026-03-31T13:27:13Z"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `balance` | float | Current balance in EUR |
| `currency` | string | Always `"EUR"` |
| `last_checked` | datetime | ISO 8601 timestamp |

---

### List Active Bookings

`GET /api/bookings`

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8090/api/bookings
```

**Response:** `200 OK`
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

| Field | Type | Description |
|-------|------|-------------|
| `bookings` | array | List of active booking objects |
| `count` | int | Number of active bookings |

---

### Create Booking

`POST /api/bookings`

```bash
curl -X POST http://localhost:8090/api/bookings \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "license_plate": "51-PXPN",
    "start_time": "now",
    "duration_minutes": 120
  }'
```

**Request body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `license_plate` | string | Yes | Dutch license plate (e.g. `"AB-12-CD"`, `"51PXPN"`) |
| `start_time` | string | Yes | `"now"` or ISO 8601 datetime (e.g. `"2026-04-01T09:00:00Z"`) |
| `duration_minutes` | int | Yes | Duration in minutes (1-1440) |

**Response:** `201 Created`
```json
{
  "license_plate": "51-PXPN",
  "start_time": "2026-03-31T13:27:13Z",
  "end_time": "2026-03-31T15:27:13Z",
  "status": "active"
}
```

---

### Extend Booking

`POST /api/bookings/{license_plate}/extend`

```bash
curl -X POST http://localhost:8090/api/bookings/51-PXPN/extend \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"additional_minutes": 60}'
```

**Request body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `additional_minutes` | int | Yes | Minutes to add (1-1440) |

**Response:** `200 OK`
```json
{
  "license_plate": "51-PXPN",
  "new_end_time": "2026-03-31T16:27:13Z"
}
```

---

### Cancel Booking

`POST /api/bookings/{license_plate}/cancel`

No request body required.

```bash
curl -X POST http://localhost:8090/api/bookings/51-PXPN/cancel \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:** `200 OK`
```json
{
  "status": "cancelled",
  "cancelled_at": "2026-03-31T13:30:00Z"
}
```

---

## Error Handling

**Every** error response uses this format, regardless of the error type:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable description"
  }
}
```

This includes validation errors, authentication errors, 404s, and server errors. You can always parse errors the same way.

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INVALID_TOKEN` | 401 | Missing or invalid Bearer token |
| `LOGIN_FAILED` | 401 | 2Park login failed (bad credentials or site unavailable) |
| `VALIDATION_ERROR` | 422 | Invalid request (bad license plate, missing fields, wrong types) |
| `INVALID_TIME` | 400 | Unparseable `start_time` value |
| `BOOKING_NOT_FOUND` | 404 | No active booking for the given license plate |
| `BOOKING_CONFLICT` | 409 | Active booking already exists for this plate |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `TIMEOUT_ERROR` | 504 | Browser operation timed out |
| `BROWSER_ERROR` | 500 | Browser automation failure |
| `SCRAPE_ERROR` | 500 | Failed to extract data from 2park.nl |
| `NO_BALANCE` | 500 | Could not read balance from page |
| `INTERNAL_ERROR` | 500 | Unexpected server error |

### Examples

**Missing auth:**
```bash
curl http://localhost:8090/api/account/balance
```
```json
{"error": {"code": "INVALID_TOKEN", "message": "Missing Authorization header"}}
```

**Invalid license plate:**
```bash
curl -X POST http://localhost:8090/api/bookings \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"license_plate": "X", "start_time": "now", "duration_minutes": 60}'
```
```json
{"error": {"code": "VALIDATION_ERROR", "message": "license_plate: Value error, Invalid license plate format: X. Use format like 'AB-12-CD', 'AB123CD', or '51-PXPN'"}}
```

---

## Rate Limiting

Requests are rate-limited by client IP address.

**Default:** 10 requests per 60 seconds.

Every response includes rate limit headers:

```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 7
X-RateLimit-Reset: 45
```

| Header | Description |
|--------|-------------|
| `X-RateLimit-Limit` | Maximum requests per window |
| `X-RateLimit-Remaining` | Requests remaining in current window |
| `X-RateLimit-Reset` | Seconds until the window resets |

When exceeded:
```json
{"error": {"code": "RATE_LIMIT_EXCEEDED", "message": "Rate limit exceeded. Please try again later."}}
```

Configure via environment variables:
```bash
RATE_LIMIT_REQUESTS=10
RATE_LIMIT_WINDOW_SECONDS=60
```

---

## Response Headers

Every response includes:

| Header | Description |
|--------|-------------|
| `X-Request-ID` | Unique UUID for request tracing (useful for debugging in logs) |
| `X-RateLimit-Limit` | Rate limit maximum |
| `X-RateLimit-Remaining` | Remaining requests |
| `X-RateLimit-Reset` | Seconds until reset |

---

## Setup & Running

### Local Development

```bash
uv sync
uv run playwright install chromium
cp .env.example .env
nano .env  # Set TWOPARK_EMAIL, TWOPARK_PASSWORD, API_TOKEN
python api.py
```

### Docker

```bash
cp .env.example .env
nano .env
docker compose up -d
```

### Interactive Documentation

Once running:
- **Swagger UI:** http://localhost:8090/docs
- **ReDoc:** http://localhost:8090/redoc

---

## Performance

Each API call launches a headless browser, logs in to 2park.nl, and performs the operation. Expect:

- **5-15 seconds** per request (depending on 2park.nl responsiveness)
- **~200MB memory** per concurrent browser instance

Set HTTP client timeouts to at least **120 seconds** when calling this API (especially from Home Assistant).

---

## License

This API is for personal use. Please comply with 2park.nl's terms of service.
