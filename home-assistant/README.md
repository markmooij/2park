# ============================================================
# 2Park Home Assistant Integration — Setup Guide
# ============================================================
#
# This directory contains all the files you need to integrate
# your 2Park API with Home Assistant.
#
# Files:
#   secrets.yaml         — API token (with Bearer prefix)
#   sensors.yaml         — REST sensors for balance & bookings
#   template.yaml        — Template sensor for formatted summary
#   rest_commands.yaml   — REST commands for cancel & extend
#   native-cards.yaml    — Dashboard using only (built-in cards)
#   native-cards-improved.yaml — Improved dashboard layout
#
# ============================================================
# STEP 1: Copy files to /config/
# ============================================================
#
# Copy ALL files from this directory to your HA /config/ folder:
#
#   scp home-assistant/*.yaml root@homeassistant.local:/config/
#
# Or copy manually via the File Editor add-on in HA.
#
# ============================================================
# STEP 2: Verify configuration.yaml
# ============================================================
#
# Your /config/configuration.yaml should include these lines:
#
#   sensor: !include sensors.yaml
#   template: !include template.yaml
#   rest_command: !include rest_commands.yaml
#
# If these lines already exist, make sure they're uncommented.
#
# ============================================================
# STEP 3: Restart Home Assistant
# ============================================================
#
#   Settings → System → Power & Startup → Restart
#
# ============================================================
# STEP 4: Add Dashboard Card
# ============================================================
#
# Go to your dashboard → Edit → Three dots → Edit as YAML
# Paste the card content from native-cards-improved.yaml
#
# ============================================================
# ENTITY NAMES
# ============================================================
#
# These are the entity IDs you'll reference in cards:
#
#   sensor.2park_balance          — Current account balance (EUR)
#   sensor.2park_bookings_count   — Number of active bookings
#   sensor.2park_summary          — Human-readable summary string
#
# ============================================================
# TROUBLESHOOTING
# ============================================================
#
# Sensors not showing?
#   - Check Developer Tools → States → search "2park"
#   - Verify secrets.yaml has the Bearer prefix
#   - Check Configuration → YAML → Validate configuration
#
# Balance shows 0?
#   - The API might return 0 if there are no recent transactions
#   - Wait a few minutes for the sensor to update
#   - Check HA logs for REST errors
#
# Cancel/Extend not working?
#   - Verify the 2Park API is running (http://rasp-pi-4-service.local:8090)
#   - Check HA logs for REST command errors
#
# ============================================================
