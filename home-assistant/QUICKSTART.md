# ============================================================
# 2Park Home Assistant Integration — Quick Start
# ============================================================
#
# Prerequisites:
#   - Home Assistant running (not in Docker)
#   - 2Park API running at http://rasp-pi-4-service.local:8090
#
# ============================================================
# 1. COPY FILES
# ============================================================
#
# Copy all files from home-assistant/ to /config/:
#
#   scp home-assistant/*.yaml root@homeassistant.local:/config/
#
# ============================================================
# 2. VERIFY configuration.yaml
# ============================================================
#
# Make sure these lines are in /config/configuration.yaml:
#
#   sensor: !include sensors.yaml
#   template: !include template.yaml
#   rest_command: !include rest_commands.yaml
#
# ============================================================
# 3. RESTART HA
# ============================================================
#
# Settings → System → Power & Startup → Restart
#
# ============================================================
# 4. ADD DASHBOARD CARD
# ============================================================
#
# Dashboard → Edit → Three dots → Edit as YAML
# Paste the card from native-cards-improved.yaml
#
# The card is dynamic — it shows cancel/extend buttons for
# each active booking automatically. No hardcoded plates.
#
# ============================================================
# ENTITY IDs
# ============================================================
#
# sensor.2park_balance              — Account balance in EUR
# sensor.2park_bookings_count       — Active booking count
# sensor.2park_bookings_dynamic     — Dynamic booking attributes
# sensor.2park_summary              — Formatted summary text
#
# ============================================================
# FORCING A REFRESH
# ============================================================
#
# The REST sensors poll the API every 5 minutes. To force
# an immediate update:
#
#   Service: homeassistant.update_entity
#   Target:
#     entity_id:
#       - sensor.2park_balance
#       - sensor.2park_bookings_count
#
# ============================================================
