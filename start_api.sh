#!/bin/bash

# 2Park API Startup Script
# Starts the REST API server with proper configuration

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         2Park API Server Startup          ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
echo ""

# Check if .env file exists
if [ -f .env ]; then
    echo -e "${GREEN}✓${NC} Loading environment from .env file..."
    export $(grep -v '^#' .env | xargs)
else
    echo -e "${YELLOW}⚠${NC} No .env file found."
    echo ""
fi

# Check required environment variables
MISSING_VARS=()

if [ -z "$TWOPARK_EMAIL" ]; then
    MISSING_VARS+=("TWOPARK_EMAIL")
fi

if [ -z "$TWOPARK_PASSWORD" ]; then
    MISSING_VARS+=("TWOPARK_PASSWORD")
fi

if [ -z "$API_TOKEN" ]; then
    MISSING_VARS+=("API_TOKEN")
fi

if [ ${#MISSING_VARS[@]} -gt 0 ]; then
    echo -e "${RED}✗${NC} Missing required environment variables:"
    for var in "${MISSING_VARS[@]}"; do
        echo "    - $var"
    done
    echo ""
    echo "Please create a .env file with:"
    echo ""
    echo "  TWOPARK_EMAIL=your-email@example.com"
    echo "  TWOPARK_PASSWORD=your-password"
    echo "  API_TOKEN=your-secure-token"
    echo ""
    echo "Generate a secure token with:"
    echo "  openssl rand -hex 32"
    echo ""
    exit 1
fi

echo -e "${GREEN}✓${NC} All environment variables set"
echo ""

# Check if playwright browsers are installed
if [ ! -d "$HOME/.cache/ms-playwright/chromium-1200" ] && [ ! -d "$HOME/.cache/ms-playwright" ]; then
    echo -e "${YELLOW}⚠${NC} Playwright browsers not found. Installing..."
    uv run playwright install chromium
    echo ""
fi

echo -e "${GREEN}✓${NC} Playwright browsers installed"
echo ""

# Check if dependencies are installed
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}⚠${NC} Virtual environment not found. Installing dependencies..."
    uv sync
    echo ""
fi

echo -e "${GREEN}✓${NC} Dependencies installed"
echo ""

# Print configuration
echo -e "${BLUE}Configuration:${NC}"
echo "  Email: ${TWOPARK_EMAIL}"
echo "  API Token: ${API_TOKEN:0:10}...${API_TOKEN: -4}"
echo "  Host: 0.0.0.0"
echo "  Port: 8000"
echo ""

# Check if port is already in use
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo -e "${RED}✗${NC} Port 8000 is already in use!"
    echo ""
    echo "Kill the existing process with:"
    echo "  lsof -ti:8000 | xargs kill -9"
    echo ""
    exit 1
fi

# Start the server
echo -e "${GREEN}🚀 Starting API server...${NC}"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${GREEN}Server is running!${NC}"
echo ""
echo "  API Base URL:      http://localhost:8000"
echo "  Swagger UI:        http://localhost:8000/docs"
echo "  ReDoc:             http://localhost:8000/redoc"
echo "  Health Check:      http://localhost:8000/health"
echo ""
echo "Example requests:"
echo ""
echo "  # Get balance"
echo "  curl -H \"Authorization: Bearer \$API_TOKEN\" \\"
echo "    http://localhost:8000/api/account/balance"
echo ""
echo "  # Create booking"
echo "  curl -X POST -H \"Authorization: Bearer \$API_TOKEN\" \\"
echo "    -H \"Content-Type: application/json\" \\"
echo "    -d '{\"license_plate\":\"AB-123\",\"start_time\":\"now\",\"duration_minutes\":60}' \\"
echo "    http://localhost:8000/api/bookings"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
echo ""

# Run the server
uv run python api.py

# Exit with the same code as the server
exit $?
