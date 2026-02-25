# 2Park API & Checker

Complete REST API and automated tool for managing parking reservations on [2park.nl](https://mijn.2park.nl).

## Features

### REST API (New!)
- 🚀 **Stateless REST API** for parking automation
- 🔐 **Bearer token authentication**
- 📊 **Get account balance** via API endpoint
- ➕ **Create parking bookings** programmatically
- ⏱️ **Extend active bookings** with additional time
- ❌ **Cancel bookings** via API
- 🔄 **Standardized error responses**
- 📖 **Complete API documentation** with examples

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
curl -X POST "http://localhost:8000/api/bookings" \
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

**For API:**
- `TWOPARK_EMAIL` - Your 2Park account email (required)
- `TWOPARK_PASSWORD` - Your 2Park account password (required)
- `API_TOKEN` - Bearer token for API authentication (required for API)

**For CLI:**
- `TWOPARK_EMAIL` - Your 2Park account email (required)
- `TWOPARK_PASSWORD` - Your 2Park account password (required)

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
- **Production:** Use HTTPS and consider rate limiting
- **Access Control:** Don't expose the API directly to the internet

## Troubleshooting

### Browser crashes or fails to launch

Try these solutions:
1. Make sure you've installed Playwright browsers: `playwright install chromium`
2. Ensure you have the necessary system dependencies (Playwright will tell you if any are missing)
3. Check the logs for specific error messages

### Timeout errors

- Increase timeout values in the script (default is 30000ms for navigation, 10000ms for selectors)
- Check your internet connection
- The website might be slow or down

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
api.py           # FastAPI application with endpoints
scraper.py       # Stateless scraper for browser automation
models.py        # Pydantic models for requests/responses
errors.py        # Error codes and exception handling
auth.py          # Bearer token authentication
main.py          # CLI script (original functionality)
```

### Stateless Design

Each API request:
1. Authenticates the bearer token
2. Launches a new browser session
3. Logs in to 2Park
4. Performs the requested operation
5. Cleans up all resources

This ensures no memory leaks and horizontal scalability.

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
✅ **Standardized error responses** with error codes  
✅ **Proper error handling** with try-catch blocks  
✅ **Comprehensive logging** for debugging  
✅ **Environment variables** for sensitive data  
✅ **Type hints** throughout codebase  
✅ **Pydantic models** for validation  
✅ **Browser cleanup** in context managers  
✅ **Timeouts** on all async operations  
✅ **RESTful API design**  
✅ **OpenAPI documentation** (Swagger/ReDoc)  
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
├── main.py             # CLI checker script
├── run.sh              # Convenience script for CLI
├── API.md              # Complete API documentation
├── README.md           # This file
├── CHANGES.md          # Change log and migration guide
├── QUICKSTART.md       # Quick reference guide
├── .env.example        # Environment variable template
└── pyproject.toml      # Python dependencies
```

## Documentation

- **[API.md](API.md)** - Complete API documentation with examples
- **[QUICKSTART.md](QUICKSTART.md)** - Quick reference for CLI usage
- **[CHANGES.md](CHANGES.md)** - Migration guide from old version

## License

This is a personal automation tool. Use responsibly and in accordance with 2Park's terms of service.