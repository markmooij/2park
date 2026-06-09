# Home Assistant Integration for 2Park API
#
# Add this to your Home Assistant configuration.
# Requires the `rest` integration (built-in) and `rest_command` (built-in).
# For the dashboard card, install the custom card:
#   HACS → Frontend → Search "button-card" → Install
#
# Files:
#   sensors.yaml      - REST sensors for balance & bookings
#   template.yaml     - Template sensor for formatted summary (use `template:` key)
#   rest_commands.yaml - REST commands for cancel & extend
#   secrets.yaml      - API token
#   lovelace-card.yaml - Full dashboard with button-card
#   native-cards.yaml  - Dashboard using only (built-in cards)
#
# ============================================================
# 1. REST SENSORS (add to: sensors.yaml or inside sensors: block)
# ============================================================

# --- Account Balance ---
- platform: rest
  name: "2Park Balance"
  resource: http://rasp-pi-4-service.local:8090/api/account/balance
  method: GET
  headers:
    Authorization: !secret twopark_api_token
    Content-Type: application/json
  value_template: "{{ value_json.balance }}"
  unit_of_measurement: "EUR"
  json_attributes:
    - currency
    - last_checked
  scan_interval: 300  # 5 minutes

# --- Active Bookings Count ---
- platform: rest
  name: "2Park Bookings Count"
  resource: http://rasp-pi-4-service.local:8090/api/bookings
  method: GET
  headers:
    Authorization: !secret twopark_api_token
    Content-Type: application/json
  value_template: "{{ value_json.count }}"
  json_attributes:
    - bookings
  scan_interval: 60  # 1 minute

# ============================================================
# 2. REST COMMANDS (add to: rest_commands.yaml or inside rest_command: block)
# ============================================================

# Cancel a booking — call with:
#   service: rest_command.cancel_twopark_booking
#   data:
#     license_plate: "51PXPN"
cancel_twopark_booking:
  url: "http://rasp-pi-4-service.local:8090/api/bookings/{{ license_plate }}/cancel"
  method: POST
  headers:
    Authorization: !secret twopark_api_token
    Content-Type: application/json
  timeout: 120

# Extend a booking — call with:
#   service: rest_command.extend_twopark_booking
#   data:
#     license_plate: "51PXPN"
#     additional_minutes: 60
extend_twopark_booking:
  url: "http://rasp-pi-4-service.local:8090/api/bookings/{{ license_plate }}/extend"
  method: POST
  headers:
    Authorization: !secret twopark_api_token
    Content-Type: application/json
  payload: '{"additional_minutes": {{ additional_minutes }}}'
  timeout: 120

# ============================================================
# 3. TEMPLATE SENSOR (optional — formats bookings as a friendly string)
# ============================================================

# sensor:
#   - platform: template
#     sensors:
#       twopark_booking_summary:
#         value_template: >
#           {% set bookings = states('sensor.twopark_bookings_count') | int %}
#           {% if bookings == 0 %}
#             No active bookings
#           {% else %}
#             {{ bookings }} active booking(s)
#           {% endif %}

# ============================================================
# 4. LOVELACE DASHBOARD CARD
#    Paste this into a YAML dashboard or use the UI card editor.
#    Requires custom card: button-card (from HACS)
# ============================================================

# --- Example YAML card (for a vertical-stack or grid) ---
# card:
#   type: vertical-stack
#   cards:
#     # Balance summary
#     - type: custom:button-card
#       name: Account Balance
#       icon: "mdi:wallet"
#       label: "€ {{ states('sensor.twopark_balance') }}"
#       styles:
#         name:
#           - font-size: 14px
#           - color: gray
#         label:
#           - font-size: 24px
#           - font-weight: bold
#         icon:
#           - color: green
#       state:
#         - operator: template
#           value: "{{ states('sensor.twopark_balance') | float > 0 }}"
#           styles:
#             icon:
#               - color: green
#         - operator: default
#           styles:
#             icon:
#               - color: red

#     # Active bookings
#     - type: custom:button-card
#       name: Active Bookings
#       icon: "mdi:parking"
#       show_label: true
#       label: "{{ states('sensor.twopark_bookings_count') }} active"
#       styles:
#         name:
#           - font-size: 14px
#           - color: gray
#       state:
#         - operator: template
#           value: "{{ states('sensor.twopark_bookings_count') | int > 0 }}"
#           styles:
#             icon:
#               - color: orange
#         - operator: default
#           styles:
#             icon:
#               - color: gray

#     # Individual booking cards (using template for dynamic cards)
#     # Note: button-card doesn't support dynamic loops natively.
#     # For a fully dynamic list, use a custom card like "lovelace-auto-entities"
#     # or build the cards in the UI. Here's a template approach:

#     - type: custom:button-card
#       template: booking_card
#       variables:
#         plate: "51PXPN"
#         start: "2026-06-05T14:00:00Z"
#         end: "2026-06-05T16:00:00Z"
#         status: "active"

# ============================================================
# TEMPLATE DEFINITIONS (add to: button-card-templates.yaml or inside
#   button_card_templates: in ui-lovelace.yaml)
# ============================================================

# button_card_templates:
#   booking_card:
#     type: custom:button-card
#     styles:
#       grid:
#         - grid-template-areas: '"i n" "i l" "i b"'
#         - grid-template-columns: 40px 1fr
#         - grid-template-rows: 1fr 1fr 45px
#       name:
#         - font-size: 16px
#         - font-weight: bold
#       label:
#         - font-size: 12px
#       badge:
#         - font-size: 10px
#       card:
#         - border-radius: 12px
#         - padding: 12px
#         - box-shadow: 0 2px 8px rgba(0,0,0,0.1)
#     variables:
#       plate: ""
#       start: ""
#       end: ""
#       status: "active"
#     icon: "mdi:car"
#     name: "={{ vars.plate }}"
#     label: >
#       ={{ "from_iso8601(vars.start) | as_local | timestamp_custom('%H:%M') }}
#       →
#       {{ "from_iso8601(vars.end) | as_local | timestamp_custom('%H:%M') }}"
#     badges:
#       - type: template
#         badge_color: >
#           {{ "green" if vars.status == "active" else "red" }}
#         badge: >
#           {{ "active" | capitalize }}
#     tap_action:
#       action: more-info
#     hold_action:
#       action: call-service
#       service: rest_command.cancel_twopark_booking
#       service_data:
#         license_plate: "={{ vars.plate }}"
#       confirmation:
#         text: "Cancel booking for {{ vars.plate }}?"
#     double_tap_action:
#       action: call-service
#       service: rest_command.extend_twopark_booking
#       service_data:
#         license_plate: "={{ vars.plate }}"
#         additional_minutes: 60
#       confirmation:
#         text: "Extend {{ vars.plate }} by 60 minutes?"

# ============================================================
# 5. FULL LOVELACE CARD — Single Page Setup
#    Copy everything below into your dashboard YAML.
#    Adjust the license plates and times to match your bookings.
# ============================================================

# --- Complete card example (copy into UI or YAML dashboard) ---
#
# For a fully dynamic setup, use the `button-card` template approach
# above with a `lovelace-gen` or `auto-entities` card.
# Here's a practical single-card version:

# type: custom:button-card
# name: "2Park Dashboard"
# icon: "mdi:car-key"
# styles:
#   grid:
#     - grid-template-areas: >
#         "balance balance balance"
#         "plate1 plate1 plate1"
#         "plate2 plate2 plate2"
#         "cancel1 cancel1 extend1"
#         "cancel2 cancel2 extend2"
#     - grid-template-columns: 1fr 1fr 1fr
#     - gap: 8px
#   card:
#     - background: var(--card-background-color)
#     - border-radius: 16px
#     - padding: 16px
#   name:
#     - font-size: 18px
#     - font-weight: bold
#     - color: var(--primary-text-color)

# ============================================================
# NOTES
# ============================================================
#
# 1. Side-loaded bookings: The /api/bookings endpoint returns ALL
#    active reservations on your 2Park account, including side-loaded
#    ones. No separate API call needed.
#
# 2. Token: Store your API token in secrets.yaml:
#      twopark_api_token: "b6a32d1cde51a1dce7e21343f8233a501afe49cbf3bc0983263591fbf3e3ce43"
#
# 3. The extend command adds minutes to the CURRENT end time.
#    E.g., if booking ends at 14:00 and you extend by 60 min,
#    it will end at 15:00.
#
# 4. For automatic card generation from the API response, consider
#    using the "button-card" custom card with a template that
#    iterates over the bookings list. See the templates section above.
#
# 5. If you don't have button-card installed:
#    - Go to HACS → Frontend → "+" → Search "button-card"
#    - Install and restart Home Assistant
#    - Add to your ui-lovelace.yaml:
#        resources:
#          - url: /hacsfiles/button-card/button-card.js
#            type: module
