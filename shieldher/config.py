# config.py
# ShieldHer — Central Runtime Configuration
#
# This is the single place to change settings for different environments.
# When deploying to Jetson Orin Nano, only this file needs to change.
#
# Usage: imported by app.py and mission_controller.py

# ── Network ────────────────────────────────────────────────────────
# "0.0.0.0" binds to all interfaces so phones on the same Wi-Fi
# can reach the Jetson at http://<jetson-ip>:5000
HOST = "0.0.0.0"
PORT = 5000

# ── Mission Mode ───────────────────────────────────────────────────
# "LOCAL"  → runs on developer machine (no hardware)
# "JETSON" → update this string when deploying to real hardware
MISSION_MODE = "LOCAL"

# ── Developer Tools ────────────────────────────────────────────────
# When True, tests/manual_trigger.py is allowed to push state updates.
# Set to False for a hardened production deployment.
ENABLE_MANUAL_TRIGGER = True
