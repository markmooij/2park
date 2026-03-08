# 2Park API & Checker

Complete REST API and automated tool for managing parking reservations on [2park.nl](https://mijn.2park.nl).

## Features

### REST API
- 🚀 **REST API** for parking automation with FastAPI
- 🔐 **Bearer token authentication**
- 📊 **Get account balance** via API endpoint
- ➕ **Create parking bookings** programmatically
- ⏱️ **Extend active bookings** with additional time
- ❌ **Cancel bookings** via API
- 🔄 **Standardized error responses** with error codes
- 📖 **Complete API documentation** with examples
- ⚖️ **Rate limiting** to prevent abuse
- 🆔 **License plate validation** for Dutch formats
- ⏱️ **Configurable timeouts** for browser operations

### CLI/Scraper
- 🚗 View active parking reservations with details (name, license plate, start/end times)
- 💰 Check current account balance
- 👀 Visible browser mode to see what's happening in real-time
- 📝 Detailed logging for debugging
- 🔒 Secure credential management via environment variables
- ⚡ Proper error handling and timeouts

## Prerequisites

- Python 3.12+
- Chrome/Chromium browser installed on your system

## Quick Start
## Quick Start

### For API Users

1. **Install dependencies:**
```bash
uv sync
uv run playwright install chromium
```

2. **Set up credentials:**
```bash
cp .env.example .env
nano .env  # Add your credentials and generate an API token
```

3. **Generate API token:**
```bash
openssl rand -hex 32
```

4. **Start the API server:**
```bash
python api.py
```

5. **Test the API:**
```bash
curl -X GET "http://localhost:8000/api/account/balance" \
  -H "Authorization: Bearer your-token-here"
```

📖 **See [API.md](API.md) for complete API documentation**

### For CLI Users

1. **Install dependencies:**
```bash
uv sync
uv run playwright install chromium
```

2. **Set up credentials:**
```bash
cp .env.example .env
nano .env  # Add your 2Park credentials
```

3. **Run the checker:**
```bash
./run.sh
```

The browser will open and you can watch the automation in action.

## API Usage

The 2Park API provides a stateless REST interface for parking automation.

### Available Endpoints

- `GET /api/account/balance` - Get current balance
- `POST /api/bookings` - Create a new booking
- `POST /api/bookings/{license_plate}/extend` - Extend a booking
- `POST /api/bookings/{license_plate}/cancel` - Cancel a booking

### Example: Create Booking

```bash
curl -X POST "http://localhost:8090/api/bookings" \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "license_plate": "AB-123-CD",
    "start_time": "now",
    "duration_minutes": 120
  }'
```

### Example: Get Balance

```bash
curl -X GET "http://localhost:8000/api/account/balance" \
  -H "Authorization: Bearer your-token"
```

Response:
```json
{
  "balance": 12.35,
  "currency": "EUR",
  "last_checked": "2025-01-05T13:55:00Z"
}
```

### Interactive API Documentation

Once the server is running, visit:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

📖 **Full API documentation:** [API.md](API.md)

## CLI Usage

### Easy way (with run script):
```bash
./run.sh
```

The run script will:
- Check for credentials in `.env` or prompt you for them
- Verify Playwright browsers are installed
- Run the checker with proper error handling

### Manual way:
```bash
# Set environment variables (if not using .env)
export TWOPARK_EMAIL="your-email@example.com"
export TWOPARK_PASSWORD="your-password"

# Run with uv
uv run python main.py

# Or run directly with Python
python main.py
```

The script will:
1. Launch a visible Chrome browser window
2. Navigate to the 2Park login page
3. Automatically log in with your credentials
4. Extract and display active reservations
5. Show your current account balance
6. Close the browser

## Configuration

### Environment Variables

**Required:**
- `TWOPARK_EMAIL` - Your 2Park account email
- `TWOPARK_PASSWORD` - Your 2Park account password
- `API_TOKEN` - Bearer token for API authentication

**Optional (Rate Limiting):**
- `RATE_LIMIT_REQUESTS` - Max requests per window (default: 10)
- `RATE_LIMIT_WINDOW_SECONDS` - Time window in seconds (default: 60)

**Optional (Timeouts - seconds, range 10-300):**
- `BROWSER_TIMEOUT` - Browser navigation timeout (default: 30)
- `NAVIGATION_TIMEOUT` - Page navigation timeout (default: 30)
- `SELECTOR_TIMEOUT` - Selector waiting timeout (default: 10)
- `SESSION_CACHE_TTL` - Session cache TTL in seconds (default: 300)

**Optional (Logging):**
- `LOG_LEVEL` - Logging level: DEBUG, INFO, WARNING, ERROR (default: INFO)
- `LOG_FILE` - Log file path (default: logs/app.log)

### API Server Settings

Edit `api.py` to configure:
- **Host:** Default `0.0.0.0`
- **Port:** Default `8000`
- **Log level:** Default `info`

### Browser Settings (CLI)

You can modify browser behavior in `main.py`:
- `headless=False` - Shows the browser window (set to `True` to hide it)
- `slow_mo=50` - Slows down operations by 50ms for visibility
- Window size: Default is 1920x1080

## Output Examples

### CLI Output

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
€ 25.50
==================================================
```

### API Response Examples

**Get Balance:**
```json
{
  "balance": 25.50,
  "currency": "EUR",
  "last_checked": "2025-01-05T14:00:00Z"
}
```

**Create Booking:**
```json
{
  "license_plate": "AB-123-CD",
  "start_time": "2025-01-05T14:00:00Z",
  "end_time": "2025-01-05T16:00:00Z",
  "status": "active"
}
```

**Error Response:**
```json
{
  "error": {
    "code": "BOOKING_CONFLICT",
    "message": "Active booking already exists for AB-123-CD"
  }
}
```

## Security Notes

- **Never commit your `.env` file or hardcode credentials** - it's already in `.gitignore`
- Credentials are only stored in environment variables
- The script does not store or transmit your credentials anywhere except to 2park.nl
- **API Token:** Generate a secure random token for API authentication
  ```bash
  openssl rand -hex 32
  ```
- **Rate Limiting:** Configure via environment variables to prevent abuse
- **Production:** Use HTTPS and consider rate limiting
- **Access Control:** Don't expose the API directly to the internet

## ⚠️ Important Disclaimer

This project is a **personal hobby project** created for educational purposes.

- This tool automates interaction with [2park.nl](https://mijn.2park.nl) using browser automation
- **Use at your own risk** - Always check 2park.nl's Terms of Service
- The author is **not affiliated** with 2park.nl
- **Respect rate limits** - Don't abuse this tool
- This is **not a production-ready solution** - Handle with care

By using this software, you agree to:
1. Review and comply with 2park.nl's Terms of Service
2. Use this tool responsibly and ethically
3. Not use this for commercial purposes without proper authorization
4. Accept responsibility for any consequences of using this software

## Troubleshooting

### Browser crashes or fails to launch

Try these solutions:
1. Make sure you've installed Playwright browsers: `playwright install chromium`
2. Ensure you have the necessary system dependencies (Playwright will tell you if any are missing)
3. Check the logs for specific error messages

### Timeout errors

- Increase timeout values via environment variables (`BROWSER_TIMEOUT`, `NAVIGATION_TIMEOUT`, `SELECTOR_TIMEOUT`)
- Check your internet connection
- The website might be slow or down

### Invalid license plate format

The API validates Dutch license plate formats. Supported formats include:
- Current EU format: `AB-12-CD`, `1-AB-23`
- Historic format: `XX-XX-XX`
- Use format like `AB-12-CD` or `1-AB-23`

### Rate limit exceeded

If you see rate limit errors:
- Wait before retrying (check `X-RateLimit-Reset` header)
- Increase `RATE_LIMIT_REQUESTS` and `RATE_LIMIT_WINDOW_SECONDS` environment variables

### Missing credentials error

Make sure you've set the environment variables:
```bash
export TWOPARK_EMAIL="your-email@example.com"
export TWOPARK_PASSWORD="your-password"
```

### Selectors not found

The website might have changed its structure. Check the browser console for the actual element selectors being used.

### Using the run script

For the easiest experience, use the included `run.sh` script:
```bash
./run.sh
```

This handles credentials, browser installation checks, and proper error handling automatically.

## Architecture

### API Structure

```
api.py              # FastAPI application with endpoints
scraper.py          # Stateless scraper for browser automation
models.py           # Pydantic models for requests/responses
errors.py           # Error codes and exception handling
auth.py             # Bearer token authentication
rate_limit.py       # Rate limiting middleware
config.py           # Configuration loader (future)
main.py             # CLI script (original functionality)
```

### Stateless Design

Each API request:
1. Authenticates the bearer token
2. Launches a new browser session (or reuses cached session)
3. Logs in to 2Park
4. Performs the requested operation
5. Cleans up all resources

This ensures no memory leaks and horizontal scalability.

### Session Caching

For better performance, the API can cache login sessions:
- Default TTL: 300 seconds (configurable via `SESSION_CACHE_TTL`)
- Reduces request time by reusing existing logins
- Automatic cleanup on session failure

### Rate Limiting

API requests are rate-limited by client IP:
- Default: 10 requests per 60 seconds
- Configurable via `RATE_LIMIT_REQUESTS` and `RATE_LIMIT_WINDOW_SECONDS`
- Returns 429 status code when limit exceeded
- Headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`

### CLI Structure

The CLI uses the `TwoParkChecker` class:
- `launch_browser()` - Launches browser with proper configuration
- `create_page()` - Creates a new page with viewport settings
- `login()` - Handles the login process
- `get_active_reservations()` - Extracts reservation data
- `get_current_balance()` - Extracts account balance
- `close()` - Properly closes the browser
- `run()` - Main execution flow with error handling

## Best Practices Implemented

✅ **Stateless API architecture**  
✅ **Bearer token authentication**  
✅ **License plate validation** for Dutch formats  
✅ **Rate limiting middleware**  
✅ **Standardized error responses** with error codes  
✅ **Configurable timeouts** via environment variables  
✅ **Proper error handling** with try-catch blocks  
✅ **Comprehensive logging** with request IDs  
✅ **Environment variables** for sensitive data  
✅ **Type hints** throughout codebase  
✅ **Pydantic models** for validation  
✅ **Browser cleanup** in context managers  
✅ **RESTful API design**  
✅ **OpenAPI documentation** (Swagger/ReDoc)  
✅ **CORS middleware** for Home Assistant  
✅ **Class-based organization**  
✅ **Graceful degradation**  

## Files Overview

```
2park_checker/
├── api.py              # FastAPI REST API server
├── scraper.py          # Stateless browser automation
├── models.py           # Pydantic request/response models
├── errors.py           # Error codes and exceptions
├── auth.py             # Authentication middleware
├── rate_limit.py       # Rate limiting middleware
├── main.py             # CLI checker script
├── run.sh              # Convenience script for CLI
├── API.md              # Complete API documentation
├── README.md           # This file
├── ROADMAP.md          # Project roadmap and future plans
├── CHANGES.md          # Change log and migration guide
├── QUICKSTART.md       # Quick reference guide
├── .env.example        # Environment variable template
├── Dockerfile          # Docker image definition
├── docker-compose.yml  # Docker Compose configuration
└── pyproject.toml      # Python dependencies
```

## Documentation

- **[API.md](API.md)** - Complete API documentation with examples
- **[QUICKSTART.md](QUICKSTART.md)** - Quick reference for CLI usage
- **[CHANGES.md](CHANGES.md)** - Migration guide from old version

## Testing

### Running Unit Tests

Install dev dependencies and run tests:

```bash
# Install dev dependencies
uv sync --extra dev

# Or install pytest directly
uv add --dev pytest

# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run specific test file
pytest tests/test_license_plate.py
```

### Test Coverage

| Test File | Tests | Status |
|-----------|-------|--------|
| `test_license_plate.py` | 4 | ✅ Passing |
| `test_time_parsing.py` | 3 | ✅ Passing |
| **Total** | **7** | **✅ Passing** |

### Integration Tests

The `test_api.py` script tests the running API server. Start the server first:

```bash
# Start the API server
python api.py

# In another terminal, run integration tests
python test_api.py
```

**Note:** Be careful with booking operations - they will create real bookings on your 2Park account!

---

## Docker Deployment

### Quick Start with Docker Compose

```bash
# Copy environment example
cp .env.example .env

# Edit .env with your credentials
nano .env

# Build and run
docker-compose up -d
```

### Environment Variables

```bash
# Required
TWOPARK_EMAIL=your-email@example.com
TWOPARK_PASSWORD=your-password
API_TOKEN=your-secure-token

# Optional (defaults shown)
RATE_LIMIT_REQUESTS=10
RATE_LIMIT_WINDOW_SECONDS=60
BROWSER_TIMEOUT=30
NAVIGATION_TIMEOUT=30
SELECTOR_TIMEOUT=10
SESSION_CACHE_TTL=300
LOG_LEVEL=INFO
```

### Accessing the API

Once running, the API is available at `http://localhost:8080`:

```bash
# Health check
curl http://localhost:8080/health

# Get balance
curl -H "Authorization: Bearer your-token" \
  http://localhost:8080/api/account/balance
```

### Viewing Logs

```bash
# View container logs
docker logs -f 2park-api
```

### Stop/Start

```bash
# Stop
docker-compose down

# Start
docker-compose up -d

# Restart
docker-compose restart
```

## Roadmap

See [ROADMAP.md](ROADMAP.md) for planned features and improvements.

## License

This is a personal automation tool. Use responsibly and in accordance with 2Park's terms of service.
