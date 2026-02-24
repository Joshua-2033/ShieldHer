# shieldher/server/app.py
# ShieldHer v1.1 — Flask Mission Control API
#
# Exposes three structured endpoints:
#   POST /api/mission/start  → receive SOS + GPS, activate mission
#   GET  /api/mission/state  → return current drone state (polled by UI)
#   POST /api/mission/reset  → disarm and return to standby
#
# This server is designed to run on:
#   - Developer machine (LOCAL mode)
#   - Jetson Orin Nano (JETSON mode — change config.py only)
#
# Run: python app.py  (from shieldher/server/)

import sys
import os

# Ensure the project root is on the path so all shieldher.* imports resolve
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from flask import Flask, jsonify, request, render_template
from shieldher.core import drone_state, mission_controller
from shieldher import config

# ── Flask App Setup ────────────────────────────────────────────────
# template_folder and static_folder are resolved relative to this file
app = Flask(
    __name__,
    template_folder=os.path.join("..", "ui", "templates"),
    static_folder=os.path.join("..", "ui", "static")
)


# ── Route: GET / ───────────────────────────────────────────────────
# Serves the operator mission control interface.
@app.route("/")
def index():
    return render_template("index.html")


# ── Route: POST /api/mission/start ─────────────────────────────────
# Receives GPS coordinates from operator browser.
# Validates input, then hands off to mission_controller.
@app.route("/api/mission/start", methods=["POST"])
def mission_start():
    data = request.get_json(force=True, silent=True) or {}

    # Extract and validate GPS — gracefully handles null or missing values
    lat, lon = None, None
    try:
        raw_lat = data.get("lat")
        raw_lon = data.get("lon")
        if raw_lat is not None:
            lat = float(raw_lat)
        if raw_lon is not None:
            lon = float(raw_lon)
    except (ValueError, TypeError) as e:
        print(f"[API] Invalid GPS payload received: {e}")

    # Delegate all state changes and hardware calls to mission_controller
    mission_controller.start_mission(lat, lon)

    gps_note = "with GPS" if lat is not None else "without GPS (unavailable)"
    return jsonify({
        "status": "mission_active",
        "message": f"Mission started {gps_note}.",
        "gps": drone_state.gps_location
    }), 200


# ── Route: GET /api/mission/state ──────────────────────────────────
# Returns live mission state. Polled every ~1.5s by the operator UI.
# Field names match drone_state.py exactly.
@app.route("/api/mission/state")
def mission_state():
    return jsonify({
        "drone_active":     drone_state.drone_active,
        "recording_active": drone_state.recording_active,
        "ai_status":        drone_state.ai_status,
        "gps":              drone_state.gps_location,
        "battery":          drone_state.battery_level
    }), 200


# ── Route: POST /api/mission/patch ─────────────────────────────────
# Accepts a partial state update and writes it directly into drone_state.
# Used exclusively by tests/manual_trigger.py during development.
# Gated by ENABLE_MANUAL_TRIGGER in config.py.
#
# Accepted fields (all optional):
#   { "ai_status": str, "drone_active": bool, "recording_active": bool }
@app.route("/api/mission/patch", methods=["POST"])
def mission_patch():
    if not config.ENABLE_MANUAL_TRIGGER:
        return jsonify({"error": "Manual trigger is disabled in config.py."}), 403

    data = request.get_json(force=True, silent=True) or {}

    if "ai_status" in data:
        drone_state.ai_status = str(data["ai_status"])
    if "drone_active" in data:
        drone_state.drone_active = bool(data["drone_active"])
    if "recording_active" in data:
        drone_state.recording_active = bool(data["recording_active"])

    print(f"[API /patch] State updated: {data}")
    return jsonify({"status": "patched", "applied": data}), 200


# ── Route: POST /api/mission/reset ─────────────────────────────────
# Resets all mission state. Operator presses RESET on the UI.
@app.route("/api/mission/reset", methods=["POST"])
def mission_reset():
    mission_controller.reset_mission()
    return jsonify({
        "status": "standby",
        "message": "Mission reset. System at standby."
    }), 200


# ── Entry Point ────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 52)
    print("  ShieldHer v1.1 — Mission Control Server")
    print(f"  Mode    : {config.MISSION_MODE}")
    print(f"  Network : http://{config.HOST}:{config.PORT}")
    print(f"  Manual  : ENABLE_MANUAL_TRIGGER={config.ENABLE_MANUAL_TRIGGER}")
    print("=" * 52)

    app.run(host=config.HOST, port=config.PORT, debug=True)
