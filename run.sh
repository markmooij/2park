#!/bin/bash

# 2Park Checker Run Script
# This script sets up environment variables and runs the checker

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}2Park Reservation Checker${NC}"
echo "================================"
echo ""

# Check if .env file exists
if [ -f .env ]; then
    echo -e "${GREEN}✓${NC} Loading credentials from .env file..."
    export $(grep -v '^#' .env | xargs)
else
    echo -e "${YELLOW}⚠${NC} No .env file found."
    echo ""
    echo "Please set your credentials:"
    echo ""

    # Prompt for email if not set
    if [ -z "$TWOPARK_EMAIL" ]; then
        read -p "Enter your 2Park email: " TWOPARK_EMAIL
        export TWOPARK_EMAIL
    fi

    # Prompt for password if not set
    if [ -z "$TWOPARK_PASSWORD" ]; then
        read -sp "Enter your 2Park password: " TWOPARK_PASSWORD
        export TWOPARK_PASSWORD
        echo ""
    fi
fi

# Verify credentials are set
if [ -z "$TWOPARK_EMAIL" ] || [ -z "$TWOPARK_PASSWORD" ]; then
    echo -e "${RED}✗${NC} Missing credentials!"
    echo ""
    echo "Please either:"
    echo "  1. Create a .env file with your credentials (recommended)"
    echo "  2. Set environment variables manually"
    echo ""
    echo "Example .env file:"
    echo "  TWOPARK_EMAIL=your-email@example.com"
    echo "  TWOPARK_PASSWORD=your-password"
    echo ""
    exit 1
fi

echo -e "${GREEN}✓${NC} Credentials loaded"
echo ""

# Check if playwright browsers are installed
if [ ! -d "$HOME/.cache/ms-playwright/chromium-1200" ]; then
    echo -e "${YELLOW}⚠${NC} Playwright browsers not installed."
    echo "Installing Chromium browser..."
    uv run playwright install chromium
    echo ""
fi

# Run the script
echo "Starting 2Park Checker..."
echo "================================"
echo ""

uv run python main.py

# Exit with the same code as the Python script
exit $?
