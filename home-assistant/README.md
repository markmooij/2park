# ============================================================
# 2Park Home Assistant Integration — Setup Guide
# ============================================================
#
# This directory contains all the files you need to integrate
# your 2Park API with Home Assistant.
#
# Files:
#   secrets.yaml              — API token + server hostname
#   sensors.yaml              — REST sensors for balance & bookings
#   template.yaml             — Template sensor for dynamic booking attributes
#   binary_sensors.yaml       — Binary sensor for low balance alert
#   rest_commands.yaml        — REST commands for cancel, extend & create
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
# STEP 2: Fix the server hostname
# ============================================================
#
# Open /config/secrets.yaml and verify the twopark_api_host value.
# The default is:
#
#   twopark_api_host: "http://rasp-pi-4-service.local:8090"
#
# If the hostname rasp-pi-4-service.local does NOT resolve from
# your Home Assistant (most common issue!), replace it with the
# server's IP address, e.g.:
#
#   twopark_api_host: "http://192.168.1.100:8090"
#
# To test: SSH into your HA machine and run:
#
#   curl http://rasp-pi-4-service.local:8090/health
#
# If that fails, use the IP address instead.
#
# ============================================================
# STEP 3: Verify configuration.yaml
# ============================================================
#
# Your /config/configuration.yaml should include these lines:
#
#   sensor: !include sensors.yaml
#   template: !include template.yaml
#   binary_sensor: !include binary_sensors.yaml
#   rest_command: !include rest_commands.yaml
#
# ============================================================
# STEP 4: Restart Home Assistant
# ============================================================
#
#   Settings → System → Power & Startup → Restart
#
# ============================================================
# STEP 5: Add Dashboard Card
# ============================================================
#
# After restart, go to your dashboard → Edit → Three dots → Edit as YAML
#
# Paste this card. It shows balance + booking count at the top,
# then a row for each active booking with Cancel and +60m buttons.
#
# Card YAML:
#
#   type: vertical-stack
#   cards:
#     - type: horizontal-stack
#       cards:
#         - type: entities
#           title: "€{{ states('sensor.2park_balance') }}"
#           show_header_toggle: false
#           entities:
#             - entity: sensor.2park_balance
#               name: Balance
#               icon: mdi:cash
#         - type: entities
#           title: "{{ states('sensor.2park_bookings_count') | int(0) }} active"
#           show_header_toggle: false
#           entities:
#             - entity: sensor.2park_bookings_count
#               name: Bookings
#               icon: mdi:parking
#     - type: conditional
#       conditions:
#         - entity: sensor.2park_bookings_dynamic
#           attribute: booking_1_plate
#           state_not: ""
#       card:
#         type: horizontal-stack
#         cards:
#           - type: entity
#             entity: sensor.2park_bookings_dynamic
#             name: "{{ state_attr('sensor.2park_bookings_dynamic', 'booking_1_plate') }}"
#             icon: mdi:car
#             secondary_info: "Until {{ as_timestamp(state_attr('sensor.2park_bookings_dynamic', 'booking_1_end')) | timestamp_custom('%H:%M', true) }}"
#           - type: button
#             name: Cancel
#             icon: mdi:cancel
#             tap_action:
#               action: call-service
#               service: rest_command.cancel_twopark_booking
#               data:
#                 license_plate: "{{ state_attr('sensor.2park_bookings_dynamic', 'booking_1_plate') }}"
#               confirmation:
#                 text: "Cancel {{ state_attr('sensor.2park_bookings_dynamic', 'booking_1_plate') }}?"
#           - type: button
#             name: +60m
#             icon: mdi:arrow-up-bold
#             tap_action:
#               action: call-service
#               service: rest_command.extend_twopark_booking
#               data:
#                 license_plate: "{{ state_attr('sensor.2park_bookings_dynamic', 'booking_1_plate') }}"
#                 additional_minutes: 60
#               confirmation:
#                 text: "Extend {{ state_attr('sensor.2park_bookings_dynamic', 'booking_1_plate') }} by 60 min?"
#     # --- Repeat for bookings 2-5 (same pattern, change index) ---
#     # You can duplicate the conditional block above for booking_2 through booking_5
#     - type: conditional
#       conditions:
#         - entity: sensor.2park_bookings_dynamic
#           attribute: booking_1_plate
#           state: ""
#           state_not: "exists"
#         - entity: sensor.2park_bookings_count
#           state: "0"
#       card:
#         type: markdown
#         title: No Active Bookings
#         content: >
#           **No active parking sessions.** Bookings made via the API or
#           2Park website will appear here automatically.
#
#           **Current Balance:** €{{ states('sensor.2park_balance') }}
#
# ============================================================
# ENTITY NAMES
# ============================================================
#
# | Entity ID | Description |
# |-----------|-------------|
# | `sensor.2park_balance` | Current account balance (EUR) |
# | `sensor.2park_bookings_count` | Number of active bookings |
# | `sensor.2park_bookings_dynamic` | Dynamic booking attributes (plate, end time) per booking |
# | `sensor.2park_summary` | Human-readable summary string |
# | `binary_sensor.2park_low_balance` | ON when balance < €5.00 |
#
# #### `sensor.2park_bookings_dynamic` Attributes
#
# | Attribute | Example | Description |
# |-----------|---------|-------------|
# | `booking_1_plate` | `51PXPN` | License plate of booking 1 |
# | `booking_1_start` | `2026-06-30T14:46:00Z` | Start time |
# | `booking_1_end` | `2026-06-30T17:00:00Z` | End time |
# | `booking_1_status` | `active` | Status |
# | `booking_2_plate` ... `booking_5_*` | ... | Same for bookings 2-5 |
#
# Supports up to 5 concurrent bookings.
#
# ============================================================
# REST COMMANDS
# ============================================================
#
# | Command | Description |
# |---------|-------------|
# | `rest_command.create_twopark_booking` | Create booking (params: license_plate, duration_minutes) |
# | `rest_command.cancel_twopark_booking` | Cancel booking (params: license_plate) |
# | `rest_command.extend_twopark_booking` | Extend booking (params: license_plate, additional_minutes) |
#
# ============================================================
# AUTOMATION EXAMPLES
# ============================================================
#
# --- Book on Arrival (Ida) ---
#
# When Ida arrives home: book parking for 51-PX-PN and send a
# push notification to her phone. Replaces the old separate
# "Ida waarschuwing" automation — this single automation does both.
#
#   alias: "Parking - Auto Book on Arrival"
#   description: "When Ida arrives home, book parking and send notification"
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
# When Mark or Ida leaves home, cancel the active booking.
# Both use plate 51PXPN — adjust if you have separate plates.
#
#   alias: "Parking - Cancel on Departure"
#   description: "Cancel parking when Mark or Ida leaves home"
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
#   description: "Notify when 2Park balance is low"
#   trigger:
#     - platform: state
#       entity_id: binary_sensor.2park_low_balance
#       to: "on"
#   action:
#     - service: notify.notify
#       data:
#         title: "⚠️ Low Parking Balance"
#         message: >
#           2Park balance is {{ states('sensor.2park_balance') }} EUR.
#           Top up to keep automatic parking working.
#   mode: single
#
# ============================================================
# TROUBLESHOOTING
# ============================================================
#
# Sensors show 0 / balance not updating?
#   - Most common cause: the hostname in secrets.yaml doesn't resolve.
#     Run from the HA machine:
#       curl http://rasp-pi-4-service.local:8090/health
#     If it fails, change twopark_api_host in secrets.yaml to the IP:
#       twopark_api_host: "http://192.168.1.100:8090"
#   - After fixing the hostname, force a refresh:
#       Settings → Developer Tools → Actions → homeassistant.update_entity
#       Target: sensor.2park_balance
#
# Template sensor errors (TypeError: NoneType has no len())?
#   - This means the REST sensor's `bookings` attribute is None because
#     the REST sensor itself is failing (hostname issue above).
#     Fix the hostname, restart HA — the template errors will clear.
#
# Cancel/Extend not working?
#   - Check HA logs for errors. The rest_command timeout is 120s.
#   - Verify the 2Park API is running:
#       curl http://localhost:8090/health
#     (run on the 2Park server itself)
#   - Verify HA can reach the 2Park API (see hostname test above).
#
# Rest commands timeout?
#   - Each API call launches a headless browser that takes 5-25 seconds.
#     The timeout of 120s should be sufficient. If still timing out,
#     the hostname might be wrong (see above).
#
# Forcing a refresh:
#   - Call `homeassistant.update_entity` on sensor.2park_balance or
#     sensor.2park_bookings_count to trigger an immediate API poll.
#     Wait 60 seconds (the timeout) for it to complete.
#
# ============================================================
