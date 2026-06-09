# ============================================================
# 2Park Home Assistant Integration - Quick Start Guide
# ============================================================
#
# This directory contains all the files you need to integrate
# your 2Park API with Home Assistant.
#
# Files:
#   README.md            - This file
#   secrets.yaml         - API token (add to /config/secrets.yaml)
#   sensors.yaml         - REST sensors for balance & bookings
#   template.yaml        - Template sensor for formatted summary
#   rest_commands.yaml   - REST commands for cancel & extend
#   lovelace-card.yaml   - Lovelace dashboard card YAML
#   native-cards.yaml    - Dashboard using only (built-in cards, no HACS)
#
# ============================================================
# STEP 1: Prerequisites
# ============================================================
#
# Install button-card custom card from HACS:
#   1. Open Home Assistant -> HACS -> Frontend -> "+"
#   2. Search "button-card" -> Install
#   3. Restart Home Assistant
#
# Add the resource to your dashboard:
#   Dashboard -> Edit -> Three dots (..:) -> Edit as YAML
#   Add to resources:
#     - url: /hacsfiles/button-card/button-card.js
#       type: module
#
# ============================================================
# STEP 2: Add Configuration
# ============================================================
#
# Option A: Single configuration.yaml (simplest)
#   Add everything below to your main configuration.yaml:
#
#   sensor: !include sensors.yaml
#   template: !include template.yaml
#   rest_command: !include rest_commands.yaml
#
#   # Add the token to secrets.yaml:
#   # twopark_api_token: "your-token-here"
#
# Option B: Split files (recommended)
#   1. Copy secrets.yaml contents to /config/secrets.yaml
#   2. Add to configuration.yaml:
#        sensor: !include sensors.yaml
#        template: !include template.yaml
#        rest_command: !include rest_commands.yaml
#   3. Create sensors.yaml, template.yaml and rest_commands.yaml in /config/
#
# ============================================================
# STEP 3: Add Dashboard Card
# ============================================================
#
# 1. Go to your desired dashboard
# 2. Edit (..: menu) -> Edit as YAML
# 3. Add a new card -> "custom:button-card"
# 4. Paste the card YAML from lovelace-card.yaml
#
# For each booking, add a booking_card entry:
#
#   - type: custom:button-card
#     template: booking_card
#     variables:
#       plate: "51PXPN"            <- Your license plate
#       start: "2026-06-05T14:00Z" <- Start time from API
#       end: "2026-06-05T16:00Z"   <- End time from API
#       status: "active"
#
# To get current booking times:
#   curl -H "Authorization: Bearer $TOKEN" \
#     http://rasp-pi-4-service.local:8090/api/bookings
#
# ============================================================
# STEP 4: Restart Home Assistant
# ============================================================
#
# Configuration -> Reload -> Reload YAML (or restart HA)
#
# ============================================================
# INTERACTING WITH THE DASHBOARD
# ============================================================
#
# Tap a booking card -> Cancel the booking
# Long-press (hold) a booking card -> Extend by 60 minutes
#
# Both actions show a confirmation dialog before executing.
#
# ============================================================
# TROUBLESHOOTING
# ============================================================
#
# Sensors not updating?
#   - Check Developer Tools -> States for sensor.twopark_balance
#   - Check Developer Tools -> YAML -> Validate configuration
#   - Check Home Assistant logs for REST errors
#
# Card not showing?
#   - Verify button-card is installed (HACS -> Frontend)
#   - Check the resource is loaded (Browser dev tools -> Network)
#   - Try clearing browser cache
#
# Cancel/Extend not working?
#   - Check REST commands are defined (Developer Tools -> YAML)
#   - Verify the API token is correct in secrets.yaml
#   - Check Home Assistant logs for REST command errors
#
# ============================================================
