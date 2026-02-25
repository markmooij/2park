# 2Park API Documentation

Complete REST API for managing parking bookings on 2park.nl

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Base URL](#base-url)
- [Endpoints](#endpoints)
  - [Get Account Balance](#get-account-balance)
  - [Create Booking](#create-booking)
  - [Extend Booking](#extend-booking)
  - [Cancel Booking](#cancel-booking)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Setup & Running](#setup--running)

## Overview

The 2Park API provides a stateless REST interface for automating parking management on 2park.nl. Each request creates a new browser session, performs the operation, and cleans up resources automatically.

**Features:**
- ✅ Stateless architecture (no persistent sessions)
- ✅ Bearer token authentication
- ✅ Standardized error responses
- ✅ Full CRUD operations for parking bookings
- ✅ Account balance queries
- ✅ ISO 8601 datetime format
- ✅ Comprehensive logging

## Authentication

All API endpoints (except `/` and `/health`) require Bearer token authentication.

### Setting up Authentication

1. Generate a secure random token:
```bash
openssl rand -hex 32
```

2. Set it in your `.env` file:
```bash
API_TOKEN=your-generated-token-here
```

3. Include it in all requests:
```bash
Authorization: Bearer your-generated-token-here
```

### Example Request with Auth
```bash
curl -X GET "http://localhost:8000/api/account/balance" \
  -H "Authorization: Bearer your-token-here"
```

## Base URL

**Development:** `http://localhost:8000`

**Production:** Configure based on your deployment

## Endpoints

### Health Check

**Endpoint:** `GET /health`

**Description:** Check if the API is running

**Authentication:** Not required

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-05T13:55:00Z"
}
```

---

### Get Account Balance

**Endpoint:** `GET /api/account/balance`

**Description:** Retrieve current account balance from 2park.nl

**Authentication:** Required

**Response:** `200 OK`
```json
{
  "balance": 12.35,
  "currency": "EUR",
  "last_checked": "2025-01-05T13:55:00Z"
}
```

**Response Fields:**
- `balance` (float): Current account balance
- `currency` (string): Currency code (always "EUR")
- `last_checked` (datetime): ISO 8601 timestamp when balance was retrieved

**Error Responses:**
- `401 Unauthorized`: Invalid or missing token
- `500 Internal Server Error`: Login failed or scraping error

**Example:**
```bash
curl -X GET "http://localhost:8000/api/account/balance" \
  -H "Authorization: Bearer your-token-here"
```

---

### Create Booking

**Endpoint:** `POST /api/bookings`

**Description:** Create a new parking booking

**Authentication:** Required

**Request Body:**
```json
{
  "license_plate": "XX-123-Y",
  "start_time": "now",
  "duration_minutes": 60
}
```

**Request Fields:**
- `license_plate` (string, required): License plate in any format
- `start_time` (string, required): Either "now" or ISO 8601 datetime
  - `"now"` - Start immediately
  - `"2025-01-05T14:00:00Z"` - Start at specific time
- `duration_minutes` (integer, required): Duration in minutes (1-1440)

**Response:** `201 Created`
```json
{
  "license_plate": "XX-123-Y",
  "start_time": "2025-01-05T14:00:00Z",
  "end_time": "2025-01-05T15:00:00Z",
  "status": "active"
}
```

**Response Fields:**
- `license_plate` (string): License plate
- `start_time` (datetime): Booking start time in ISO 8601
- `end_time` (datetime): Booking end time in ISO 8601
- `status` (string): Booking status ("active")

**Error Responses:**
- `400 Bad Request`: Invalid request format or time
- `401 Unauthorized`: Invalid or missing token
- `409 Conflict`: Active booking already exists for this license plate
- `500 Internal Server Error`: Scraping or booking creation failed

**Examples:**

Start parking now for 2 hours:
```bash
curl -X POST "http://localhost:8000/api/bookings" \
  -H "Authorization: Bearer your-token-here" \
  -H "Content-Type: application/json" \
  -d '{
    "license_plate": "AB-123-CD",
    "start_time": "now",
    "duration_minutes": 120
  }'
```

Schedule parking for tomorrow:
```bash
curl -X POST "http://localhost:8000/api/bookings" \
  -H "Authorization: Bearer your-token-here" \
  -H "Content-Type: application/json" \
  -d '{
    "license_plate": "AB-123-CD",
    "start_time": "2025-01-06T09:00:00Z",
    "duration_minutes": 480
  }'
```

---

### Extend Booking

**Endpoint:** `POST /api/bookings/{license_plate}/extend`

**Description:** Extend an existing parking booking

**Authentication:** Required

**Path Parameters:**
- `license_plate` (string): License plate of the booking to extend

**Request Body:**
```json
{
  "additional_minutes": 60
}
```

**Request Fields:**
- `additional_minutes` (integer, required): Additional minutes to add (1-1440)

**Response:** `200 OK`
```json
{
  "license_plate": "XX-123-Y",
  "new_end_time": "2025-01-05T16:00:00Z"
}
```

**Response Fields:**
- `license_plate` (string): License plate
- `new_end_time` (datetime): New end time after extension in ISO 8601

**Error Responses:**
- `400 Bad Request`: Invalid request format
- `401 Unauthorized`: Invalid or missing token
- `404 Not Found`: No active booking found for this license plate
- `500 Internal Server Error`: Scraping or extension failed

**Example:**

Extend parking by 30 minutes:
```bash
curl -X POST "http://localhost:8000/api/bookings/AB-123-CD/extend" \
  -H "Authorization: Bearer your-token-here" \
  -H "Content-Type: application/json" \
  -d '{
    "additional_minutes": 30
  }'
```

---

### Cancel Booking

**Endpoint:** `POST /api/bookings/{license_plate}/cancel`

**Description:** Cancel an existing parking booking

**Authentication:** Required

**Path Parameters:**
- `license_plate` (string): License plate of the booking to cancel

**Request Body:** None

**Response:** `200 OK`
```json
{
  "status": "cancelled",
  "cancelled_at": "2025-01-05T15:20:00Z"
}
```

**Response Fields:**
- `status` (string): Cancellation status (always "cancelled")
- `cancelled_at` (datetime): Timestamp when booking was cancelled in ISO 8601

**Error Responses:**
- `401 Unauthorized`: Invalid or missing token
- `404 Not Found`: No active booking found for this license plate
- `500 Internal Server Error`: Scraping or cancellation failed

**Example:**
```bash
curl -X POST "http://localhost:8000/api/bookings/AB-123-CD/cancel" \
  -H "Authorization: Bearer your-token-here"
```

---

## Error Handling

All errors follow a standardized format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message"
  }
}
```

### Error Codes

| Code | Description | HTTP Status |
|------|-------------|-------------|
| `LOGIN_FAILED` | Authentication with 2Park failed | 401 |
| `INVALID_TOKEN` | Invalid or missing API token | 401 |
| `MISSING_TOKEN` | No Authorization header provided | 401 |
| `NO_BALANCE` | Unable to retrieve account balance | 500 |
| `INSUFFICIENT_BALANCE` | Not enough balance for operation | 402 |
| `BOOKING_CONFLICT` | Active booking already exists | 409 |
| `BOOKING_NOT_FOUND` | No booking found for license plate | 404 |
| `INVALID_LICENSE_PLATE` | Invalid license plate format | 400 |
| `INVALID_TIME` | Invalid datetime format | 400 |
| `SCRAPE_ERROR` | Error scraping data from website | 500 |
| `TIMEOUT_ERROR` | Operation timed out | 504 |
| `ELEMENT_NOT_FOUND` | Required element not found on page | 500 |
| `BROWSER_ERROR` | Browser automation error | 500 |
| `INTERNAL_ERROR` | Unexpected server error | 500 |
| `VALIDATION_ERROR` | Request validation failed | 400 |

### Error Examples

**Invalid Token:**
```json
{
  "error": {
    "code": "INVALID_TOKEN",
    "message": "Invalid API token"
  }
}
```

**Booking Conflict:**
```json
{
  "error": {
    "code": "BOOKING_CONFLICT",
    "message": "Active booking already exists for AB-123-CD"
  }
}
```

**Booking Not Found:**
```json
{
  "error": {
    "code": "BOOKING_NOT_FOUND",
    "message": "No active booking found for AB-123-CD"
  }
}
```

---

## Examples

### Complete Workflow

#### 1. Check Balance
```bash
curl -X GET "http://localhost:8000/api/account/balance" \
  -H "Authorization: Bearer your-token-here"
```

Response:
```json
{
  "balance": 25.50,
  "currency": "EUR",
  "last_checked": "2025-01-05T14:00:00Z"
}
```

#### 2. Create Booking
```bash
curl -X POST "http://localhost:8000/api/bookings" \
  -H "Authorization: Bearer your-token-here" \
  -H "Content-Type: application/json" \
  -d '{
    "license_plate": "AB-123-CD",
    "start_time": "now",
    "duration_minutes": 120
  }'
```

Response:
```json
{
  "license_plate": "AB-123-CD",
  "start_time": "2025-01-05T14:00:00Z",
  "end_time": "2025-01-05T16:00:00Z",
  "status": "active"
}
```

#### 3. Extend Booking
```bash
curl -X POST "http://localhost:8000/api/bookings/AB-123-CD/extend" \
  -H "Authorization: Bearer your-token-here" \
  -H "Content-Type: application/json" \
  -d '{
    "additional_minutes": 60
  }'
```

Response:
```json
{
  "license_plate": "AB-123-CD",
  "new_end_time": "2025-01-05T17:00:00Z"
}
```

#### 4. Cancel Booking
```bash
curl -X POST "http://localhost:8000/api/bookings/AB-123-CD/cancel" \
  -H "Authorization: Bearer your-token-here"
```

Response:
```json
{
  "status": "cancelled",
  "cancelled_at": "2025-01-05T15:30:00Z"
}
```

### Python Client Example

```python
import requests

API_BASE = "http://localhost:8000"
API_TOKEN = "your-token-here"

headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

# Get balance
response = requests.get(f"{API_BASE}/api/account/balance", headers=headers)
balance = response.json()
print(f"Balance: €{balance['balance']}")

# Create booking
booking_data = {
    "license_plate": "AB-123-CD",
    "start_time": "now",
    "duration_minutes": 120
}
response = requests.post(
    f"{API_BASE}/api/bookings",
    headers=headers,
    json=booking_data
)
booking = response.json()
print(f"Booking created: {booking}")

# Extend booking
extend_data = {"additional_minutes": 60}
response = requests.post(
    f"{API_BASE}/api/bookings/AB-123-CD/extend",
    headers=headers,
    json=extend_data
)
extended = response.json()
print(f"New end time: {extended['new_end_time']}")

# Cancel booking
response = requests.post(
    f"{API_BASE}/api/bookings/AB-123-CD/cancel",
    headers=headers
)
cancelled = response.json()
print(f"Cancelled at: {cancelled['cancelled_at']}")
```

### JavaScript/Node.js Client Example

```javascript
const axios = require('axios');

const API_BASE = 'http://localhost:8000';
const API_TOKEN = 'your-token-here';

const headers = {
  'Authorization': `Bearer ${API_TOKEN}`,
  'Content-Type': 'application/json'
};

// Get balance
async function getBalance() {
  const response = await axios.get(`${API_BASE}/api/account/balance`, { headers });
  console.log(`Balance: €${response.data.balance}`);
}

// Create booking
async function createBooking(licensePlate, durationMinutes) {
  const response = await axios.post(
    `${API_BASE}/api/bookings`,
    {
      license_plate: licensePlate,
      start_time: 'now',
      duration_minutes: durationMinutes
    },
    { headers }
  );
  console.log('Booking created:', response.data);
  return response.data;
}

// Extend booking
async function extendBooking(licensePlate, additionalMinutes) {
  const response = await axios.post(
    `${API_BASE}/api/bookings/${licensePlate}/extend`,
    { additional_minutes: additionalMinutes },
    { headers }
  );
  console.log('Booking extended:', response.data);
  return response.data;
}

// Cancel booking
async function cancelBooking(licensePlate) {
  const response = await axios.post(
    `${API_BASE}/api/bookings/${licensePlate}/cancel`,
    {},
    { headers }
  );
  console.log('Booking cancelled:', response.data);
  return response.data;
}

// Run example
(async () => {
  await getBalance();
  await createBooking('AB-123-CD', 120);
  await extendBooking('AB-123-CD', 60);
  await cancelBooking('AB-123-CD');
})();
```

---

## Setup & Running

### 1. Install Dependencies

```bash
uv sync
uv run playwright install chromium
```

### 2. Configure Environment Variables

Create a `.env` file:

```bash
# 2Park credentials
TWOPARK_EMAIL=your-email@example.com
TWOPARK_PASSWORD=your-password

# API authentication token
API_TOKEN=your-secure-token-here
```

Generate a secure token:
```bash
openssl rand -hex 32
```

### 3. Start the API Server

```bash
# Using uv
uv run python api.py

# Or directly
python api.py
```

The server will start on `http://localhost:8000`

### 4. Test the API

```bash
# Health check
curl http://localhost:8000/health

# Get balance (requires auth)
curl -X GET "http://localhost:8000/api/account/balance" \
  -H "Authorization: Bearer your-token-here"
```

### 5. View API Documentation

Open your browser and navigate to:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `TWOPARK_EMAIL` | Yes | Your 2Park account email |
| `TWOPARK_PASSWORD` | Yes | Your 2Park account password |
| `API_TOKEN` | Yes | Bearer token for API authentication |

### Server Configuration

Edit `api.py` to change:
- **Host:** Default `0.0.0.0` (all interfaces)
- **Port:** Default `8000`
- **Log level:** Default `info`

```python
uvicorn.run(
    "api:app",
    host="0.0.0.0",
    port=8000,
    reload=True,
    log_level="info",
)
```

---

## Architecture

### Stateless Design

Each API request follows this flow:

1. **Authenticate:** Verify bearer token
2. **Initialize:** Start browser session
3. **Login:** Authenticate with 2Park
4. **Execute:** Perform requested operation
5. **Cleanup:** Close browser and free resources

This ensures:
- ✅ No memory leaks
- ✅ No stale sessions
- ✅ Horizontal scalability
- ✅ Crash recovery

### Performance Considerations

- **Browser startup:** ~2-3 seconds per request
- **Login:** ~3-5 seconds per request
- **Total latency:** ~5-10 seconds per operation

**Optimization tips:**
- Use headless mode (default in API)
- Consider caching session cookies (future enhancement)
- Run multiple instances for parallel requests
- Use a reverse proxy (nginx) for load balancing

---

## Security

### Best Practices

1. **Use HTTPS in production**
   ```bash
   # Behind reverse proxy (recommended)
   nginx -> https -> localhost:8000
   ```

2. **Secure your API token**
   - Use a strong random token (32+ characters)
   - Never commit `.env` to version control
   - Rotate tokens regularly

3. **Rate limiting**
   - Consider adding rate limiting middleware
   - Prevent abuse and DoS attacks

4. **Network security**
   - Don't expose API directly to internet
   - Use VPN or IP whitelisting
   - Consider API gateway

### Token Generation

```bash
# Generate secure token
openssl rand -hex 32

# Or use Python
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## Troubleshooting

### API won't start

**Error:** Missing environment variables

**Solution:** Ensure `.env` has all required variables:
```bash
TWOPARK_EMAIL=your-email@example.com
TWOPARK_PASSWORD=your-password
API_TOKEN=your-token-here
```

### Authentication fails

**Error:** `LOGIN_FAILED`

**Solution:** 
- Verify 2Park credentials
- Check if account is active
- Try logging in manually first

### Browser crashes

**Error:** `BROWSER_ERROR`

**Solution:**
```bash
# Reinstall browser
uv run playwright install chromium

# Check system dependencies
playwright install-deps chromium
```

### Timeout errors

**Error:** `TIMEOUT_ERROR`

**Solution:**
- Check internet connection
- Increase timeout in `scraper.py`
- Website might be slow or down

### Booking operations fail

**Error:** `SCRAPE_ERROR`

**Solution:**
- Website structure may have changed
- Check selectors in `scraper.py`
- Inspect page with visible browser:
  ```python
  # In scraper.py, change:
  headless=False
  ```

---

## Development

### Running in Development Mode

```bash
# Auto-reload on code changes
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

### Testing with Swagger UI

Navigate to `http://localhost:8000/docs` for interactive API testing.

### Logging

Adjust log level in `api.py`:
```python
logging.basicConfig(level=logging.DEBUG)  # More verbose
logging.basicConfig(level=logging.WARNING)  # Less verbose
```

---

## Production Deployment

### Using systemd (Linux)

Create `/etc/systemd/system/2park-api.service`:

```ini
[Unit]
Description=2Park API Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/2park_checker
EnvironmentFile=/opt/2park_checker/.env
ExecStart=/opt/2park_checker/.venv/bin/uvicorn api:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable 2park-api
sudo systemctl start 2park-api
```

### Using Docker

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Copy application
COPY . .

# Install Python dependencies
RUN pip install -r requirements.txt
RUN playwright install chromium
RUN playwright install-deps chromium

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t 2park-api .
docker run -p 8000:8000 --env-file .env 2park-api
```

---

## License

This API is for personal use. Please comply with 2park.nl terms of service.

---

## Support

For issues or questions:
1. Check the logs for detailed error messages
2. Review the troubleshooting section
3. Inspect the browser behavior with `headless=False`
4. Check if 2park.nl website structure has changed