# Getting Started with 2Park API

Welcome! This guide will help you get up and running with the 2Park API in under 5 minutes.

## What You're Getting

A complete REST API that lets you:
- ✅ Check your 2Park account balance
- ✅ Create parking bookings programmatically
- ✅ Extend active bookings
- ✅ Cancel bookings
- ✅ All with simple HTTP requests

## Prerequisites

- Python 3.12 or higher
- A 2Park account (email & password)
- 5 minutes of your time

## Quick Setup (5 Steps)

### Step 1: Install Dependencies

```bash
# Install Python dependencies
uv sync

# Install browser for automation
uv run playwright install chromium
```

**Expected output:**
```
✓ Resolved packages
✓ Installed playwright, fastapi, uvicorn, etc.
✓ Downloaded Chromium
```

### Step 2: Create Your Configuration File

```bash
# Copy the example file
cp .env.example .env
```

### Step 3: Add Your Credentials

Edit `.env` file:

```bash
nano .env  # or use your favorite editor
```

Fill in these values:

```env
# Your 2Park login credentials
TWOPARK_EMAIL=your-email@example.com
TWOPARK_PASSWORD=your-password

# API authentication token (generate below)
API_TOKEN=paste-generated-token-here
```

**Generate a secure token:**
```bash
openssl rand -hex 32
```

Copy the output and paste it as `API_TOKEN` in your `.env` file.

### Step 4: Start the API Server

```bash
./start_api.sh
```

**You should see:**
```
╔════════════════════════════════════════════╗
║         2Park API Server Startup          ║
╚════════════════════════════════════════════╝

✓ Loading environment from .env file...
✓ All environment variables set
✓ Playwright browsers installed
✓ Dependencies installed

🚀 Starting API server...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Server is running!

  API Base URL:      http://localhost:8000
  Swagger UI:        http://localhost:8000/docs
  ReDoc:             http://localhost:8000/redoc
```

### Step 5: Test Your API

Open a new terminal and try this:

```bash
# Save your token to a variable for convenience
export API_TOKEN="your-token-from-env-file"

# Test the health check (no auth required)
curl http://localhost:8000/health

# Get your account balance
curl -H "Authorization: Bearer $API_TOKEN" \
  http://localhost:8000/api/account/balance
```

**Expected response:**
```json
{
  "balance": 12.35,
  "currency": "EUR",
  "last_checked": "2025-01-05T13:55:00Z"
}
```

🎉 **Congratulations! Your API is working!**

---

## Next Steps

### Explore the Interactive Documentation

Open your browser and visit:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

These provide interactive API testing right in your browser!

### Try Creating a Booking

```bash
curl -X POST "http://localhost:8000/api/bookings" \
  -H "Authorization: Bearer $API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "license_plate": "AB-123-CD",
    "start_time": "now",
    "duration_minutes": 120
  }'
```

**Response:**
```json
{
  "license_plate": "AB-123-CD",
  "start_time": "2025-01-05T14:00:00Z",
  "end_time": "2025-01-05T16:00:00Z",
  "status": "active"
}
```

### Try Extending a Booking

```bash
curl -X POST "http://localhost:8000/api/bookings/AB-123-CD/extend" \
  -H "Authorization: Bearer $API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "additional_minutes": 60
  }'
```

### Try Cancelling a Booking

```bash
curl -X POST "http://localhost:8000/api/bookings/AB-123-CD/cancel" \
  -H "Authorization: Bearer $API_TOKEN"
```

---

## Understanding the API

### Authentication

Every API request (except `/health`) needs this header:
```
Authorization: Bearer your-api-token-here
```

### Request Format

All POST requests use JSON:
```json
{
  "license_plate": "AB-123-CD",
  "start_time": "now",
  "duration_minutes": 60
}
```

### Response Format

Success responses return data:
```json
{
  "balance": 12.35,
  "currency": "EUR",
  "last_checked": "2025-01-05T13:55:00Z"
}
```

Error responses return standardized errors:
```json
{
  "error": {
    "code": "BOOKING_CONFLICT",
    "message": "Active booking already exists for AB-123-CD"
  }
}
```

### Time Format

- **Input:** Use `"now"` or ISO 8601 format: `"2025-01-05T14:00:00Z"`
- **Output:** Always ISO 8601 UTC: `"2025-01-05T14:00:00Z"`

---

## Common Use Cases

### Use Case 1: Check Balance Before Booking

```bash
# 1. Check balance
curl -H "Authorization: Bearer $API_TOKEN" \
  http://localhost:8000/api/account/balance

# 2. If balance is sufficient, create booking
curl -X POST -H "Authorization: Bearer $API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"license_plate":"AB-123","start_time":"now","duration_minutes":120}' \
  http://localhost:8000/api/bookings
```

### Use Case 2: Schedule Future Parking

```bash
# Park tomorrow at 9 AM for 8 hours
curl -X POST -H "Authorization: Bearer $API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "license_plate": "AB-123-CD",
    "start_time": "2025-01-06T09:00:00Z",
    "duration_minutes": 480
  }' \
  http://localhost:8000/api/bookings
```

### Use Case 3: Extend Running Late

```bash
# Running 30 minutes late? Extend your booking
curl -X POST -H "Authorization: Bearer $API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"additional_minutes": 30}' \
  http://localhost:8000/api/bookings/AB-123-CD/extend
```

### Use Case 4: Plans Changed, Cancel

```bash
# Cancel if you don't need the spot anymore
curl -X POST -H "Authorization: Bearer $API_TOKEN" \
  http://localhost:8000/api/bookings/AB-123-CD/cancel
```

---

## Integration Examples

### Python Script

```python
import requests
import os

API_BASE = "http://localhost:8000"
API_TOKEN = os.getenv("API_TOKEN")

headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

def get_balance():
    response = requests.get(f"{API_BASE}/api/account/balance", headers=headers)
    return response.json()

def create_booking(license_plate, duration_minutes):
    data = {
        "license_plate": license_plate,
        "start_time": "now",
        "duration_minutes": duration_minutes
    }
    response = requests.post(f"{API_BASE}/api/bookings", headers=headers, json=data)
    return response.json()

# Use it
balance = get_balance()
print(f"Current balance: €{balance['balance']}")

booking = create_booking("AB-123-CD", 120)
print(f"Booking created until {booking['end_time']}")
```

### JavaScript/Node.js

```javascript
const axios = require('axios');

const API_BASE = 'http://localhost:8000';
const API_TOKEN = process.env.API_TOKEN;

const headers = {
  'Authorization': `Bearer ${API_TOKEN}`,
  'Content-Type': 'application/json'
};

async function getBalance() {
  const response = await axios.get(`${API_BASE}/api/account/balance`, { headers });
  return response.data;
}

async function createBooking(licensePlate, durationMinutes) {
  const data = {
    license_plate: licensePlate,
    start_time: 'now',
    duration_minutes: durationMinutes
  };
  const response = await axios.post(`${API_BASE}/api/bookings`, data, { headers });
  return response.data;
}

// Use it
(async () => {
  const balance = await getBalance();
  console.log(`Balance: €${balance.balance}`);
  
  const booking = await createBooking('AB-123-CD', 120);
  console.log(`Booked until: ${booking.end_time}`);
})();
```

### Shell Script Automation

```bash
#!/bin/bash
# auto-park.sh - Automatically create parking booking

API_TOKEN="your-token"
LICENSE_PLATE="AB-123-CD"

# Create 2-hour booking
curl -X POST "http://localhost:8000/api/bookings" \
  -H "Authorization: Bearer $API_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"license_plate\": \"$LICENSE_PLATE\",
    \"start_time\": \"now\",
    \"duration_minutes\": 120
  }"

echo "Parking booked for $LICENSE_PLATE"
```

---

## Troubleshooting

### Problem: "Missing required environment variables"

**Solution:** Make sure your `.env` file has all three variables set:
```bash
cat .env
```

Should show:
```
TWOPARK_EMAIL=...
TWOPARK_PASSWORD=...
API_TOKEN=...
```

### Problem: "Cannot connect to API server"

**Solution:** Make sure the server is running:
```bash
./start_api.sh
```

Check if it's listening:
```bash
curl http://localhost:8000/health
```

### Problem: "Invalid API token"

**Solution:** 
1. Check your token in `.env`
2. Make sure you're using the exact same token in your requests
3. Generate a new token if needed: `openssl rand -hex 32`

### Problem: "LOGIN_FAILED error"

**Solution:**
1. Verify your 2Park credentials are correct
2. Try logging in manually at https://mijn.2park.nl
3. Check if your account is active

### Problem: "Port 8000 is already in use"

**Solution:**
```bash
# Kill the existing process
lsof -ti:8000 | xargs kill -9

# Or use a different port in api.py:
# uvicorn.run("api:app", port=8001)
```

### Problem: Requests are slow (5-10 seconds)

**This is normal!** Each request:
1. Launches a browser (~2-3 sec)
2. Logs into 2Park (~3-5 sec)
3. Performs the operation (~1-3 sec)
4. Cleans up (<1 sec)

**To speed up:** Consider implementing session caching (future enhancement)

---

## Understanding How It Works

### The Flow

```
Your Request → API Server → Browser Automation → 2Park Website → Response
```

1. **You send request** with auth token
2. **API verifies** your token
3. **Browser launches** (headless Chrome)
4. **Logs into 2Park** with your credentials
5. **Performs action** (check balance, create booking, etc.)
6. **Extracts data** from the website
7. **Returns JSON** response to you
8. **Cleans up** browser

### Why Stateless?

Each request is independent - no shared sessions. This means:
- ✅ No memory leaks
- ✅ No stale sessions
- ✅ Horizontally scalable
- ✅ Self-healing (crashes don't affect other requests)
- ❌ Slower (but more reliable)

---

## Available Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/` | API information | No |
| GET | `/health` | Health check | No |
| GET | `/api/account/balance` | Get balance | Yes |
| POST | `/api/bookings` | Create booking | Yes |
| POST | `/api/bookings/{plate}/extend` | Extend booking | Yes |
| POST | `/api/bookings/{plate}/cancel` | Cancel booking | Yes |

---

## CLI Alternative

If you prefer command-line interface over API:

```bash
# Use the original CLI script
./run.sh
```

This will:
- Open a visible browser
- Log in
- Show your reservations and balance
- Close automatically

---

## Further Reading

- **[API.md](API.md)** - Complete API documentation
- **[README.md](README.md)** - Full project documentation
- **[API_IMPLEMENTATION.md](API_IMPLEMENTATION.md)** - Technical details
- **Swagger UI** - http://localhost:8000/docs (when server is running)

---

## Getting Help

### Check the Logs

The API server shows detailed logs:
```
2025-01-05 14:00:00 - INFO - Logging in to 2Park...
2025-01-05 14:00:03 - INFO - Login successful
2025-01-05 14:00:04 - INFO - Fetching account balance...
```

### Test with the Test Script

```bash
python test_api.py
```

This runs automated tests to verify everything works.

### Common Error Codes

| Code | Meaning | What To Do |
|------|---------|------------|
| `INVALID_TOKEN` | Wrong API token | Check your token in `.env` |
| `LOGIN_FAILED` | Can't login to 2Park | Verify credentials |
| `BOOKING_CONFLICT` | Already have booking | Cancel existing first |
| `BOOKING_NOT_FOUND` | No booking for that plate | Check license plate |
| `TIMEOUT_ERROR` | Operation took too long | Try again, check internet |
| `SCRAPE_ERROR` | Can't extract data | Website might have changed |

---

## Security Reminders

⚠️ **Important:**
- Never commit `.env` to git (it's in `.gitignore`)
- Don't share your API token
- Use HTTPS in production (behind nginx/reverse proxy)
- Rotate tokens periodically
- Don't expose the API to the public internet

---

## What's Next?

You're all set! Here are some ideas:

1. **Automate your daily parking**
   - Create a cron job to book parking every morning
   
2. **Build a mobile app**
   - Use the API from iOS/Android
   
3. **Create a Telegram bot**
   - Control parking from Telegram messages
   
4. **Set up monitoring**
   - Alert when balance is low
   
5. **Deploy to production**
   - Use systemd or Docker
   - Put behind nginx with HTTPS

---

## Quick Reference Card

```bash
# Setup
uv sync && uv run playwright install chromium
cp .env.example .env && nano .env
openssl rand -hex 32  # Generate token

# Start server
./start_api.sh

# Get balance
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/account/balance

# Create booking (now, 2 hours)
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"license_plate":"AB-123","start_time":"now","duration_minutes":120}' \
  http://localhost:8000/api/bookings

# Extend (30 minutes)
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"additional_minutes":30}' \
  http://localhost:8000/api/bookings/AB-123/extend

# Cancel
curl -X POST -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/bookings/AB-123/cancel
```

---

**Happy parking! 🚗**