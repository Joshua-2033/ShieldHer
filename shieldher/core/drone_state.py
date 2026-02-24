# shieldher/core/drone_state.py
# ShieldHer — Shared Runtime State
#
# This module holds ONLY live mission variables.
# It is the single source of truth read by app.py and written by mission_controller.py.
#
# NO logic. NO functions. NO imports.
# If you need to add a new runtime value, add it here.

# ── Mission State ──────────────────────────────────────────────────
drone_active    = False       # True once the drone system has acknowledged startup
recording_active = False      # True once the camera/recording system is confirmed active
ai_status       = "Standby"   # Updated externally by AI script or manual_trigger.py

# ── Location ───────────────────────────────────────────────────────
gps_location = {
    "lat": None,              # Decimal degrees latitude from operator's browser
    "lon": None               # Decimal degrees longitude from operator's browser
}

# ── Hardware ───────────────────────────────────────────────────────
battery_level = 95            # Percentage — updated by drone telemetry when integrated
