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
#   rest_commands.yaml   — REST commands for cancel, extend & create
#   native-cards.yaml    — Dashboard using only (built-in cards)
#   native-cards-improved.yaml — Dynamic dashboard card (recommended)
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
# Paste the card content from `native-cards-improved.yaml`
#
# The card is fully dynamic — it reads active bookings from the API
# and shows Cancel/Extend buttons for each booking automatically.
# No hardcoded license plates needed.
#
# REST commands available:
#   - rest_command.cancel_twopark_booking   (cancel a booking by plate)
#   - rest_command.extend_twopark_booking   (extend by N minutes)
#   - rest_command.create_twopark_booking   (create a new booking)
#
# ============================================================
# ENTITY NAMES
# ============================================================
#
# These are the entity IDs you'll reference in cards:
#
# | Entity ID | Description |
# |-----------|-------------|
# | `sensor.2park_balance` | Current account balance (EUR) |
# | `sensor.2park_bookings_count` | Number of active bookings |
# | `sensor.2park_bookings_dynamic` | Dynamic booking attributes (plate, end time) for each active booking |
# | `sensor.2park_summary` | Human-readable summary string |
#
# #### `sensor.2park_bookings_dynamic` Attributes
#
# This sensor exposes per-booking attributes for the dynamic card:
#
# | Attribute | Example Value | Description |
# |-----------|---------------|-------------|
# | `booking_1_plate` | `51PXPN` | License plate of booking 1 |
# | `booking_1_start` | `2026-03-31T14:46:00Z` | Start time of booking 1 |
# | `booking_1_end` | `2026-03-31T17:00:00Z` | End time of booking 1 |
# | `booking_1_status` | `active` | Status of booking 1 |
# | `booking_2_plate` ... `booking_5_*` | ... | Same for bookings 2-5 |
#
# Supports up to 5 concurrent bookings. If you regularly have more, extend the template sensor and card pattern.
#
# ============================================================
# AUTOMATION EXAMPLES
# ============================================================
#
# These automations are deployed on the author's Home Assistant.
# Adapt the entity IDs, license plates, and notify services to
# match your setup.
#
# --- Book on Arrival (Ida) ---
#
# When Ida arrives home: book parking for 51-PX-PN and send a
# push notification to her phone. Replaces the old separate
# "Ida waarschuwing" automation.
#
#   alias: "Parking - Auto Book on Arrival"
#   trigger:
#     - platform: state
#       entity_id: person.ida
#       from: "not_home"
#       to: "home"
#   condition:
#     - condition: not
#       conditions:
#         - condition: state
#           entity_id: binary_sensor.2park_low_balance
#           state: "on"
#   action:
#     - service: rest_command.create_twopark_booking
#       data:
#         license_plate: "51PXPN"
#         duration_minutes: 120
#     - service: notify.notify
#       data:
#         title: "Parking Booked"
#         message: "Parking booked for Ida (51PXPN) for 120 minutes."
#     - service: notify.mobile_app_2201123g
#       data:
#         message: "Parking booked for 51-PX-PN! Check de parkeerapp."
#   mode: single
#
# --- Cancel on Departure ---
#
#   alias: "Parking - Cancel on Departure"
#   trigger:
#     - platform: state
#       entity_id:
#         - person.mark
#         - person.ida
#       from: "home"
#       to: "not_home"
#   action:
#     - variables:
#         plates:
#           person.mark: "51PXPN"
#           person.ida: "51PXPN"
#     - service: rest_command.cancel_twopark_booking
#       data:
#         license_plate: "{{ plates[trigger.entity_id] }}"
#   mode: single
#
# --- Low Balance Alert ---
#
#   alias: "Parking - Alert on Low Balance"
#   trigger:
#     - platform: state
#       entity_id: binary_sensor.2park_low_balance
#       to: "on"
#   action:
#     - service: notify.notify
#       data:
#         title: "Low Parking Balance"
#         message: >
#           2Park balance is {{ states('sensor.2park_balance') }} EUR.
#           Top up to keep automatic parking working.
#   mode: single
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
# Forcing refresh?
#    - Call `homeassistant.update_entity` on `sensor.2park_balance` or
#      `sensor.2park_bookings_count` to trigger an immediate API poll
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
