# app.py
# Main Flask server for ShieldHer simulation backend.
# All API routes are defined here.
# Designed to run locally now, and on Jetson Orin Nano later
# by simply pointing the frontend to the Jetson's IP address.

import os
import threading
import time
from flask import Flask, jsonify, request, render_template, send_file, Response

import drone_state  # Our in-memory state module

app = Flask(__name__, template_folder="templates", static_folder="../static")

# ------------------------------------------------------------------
# Route: GET /
# Serves the main ShieldHer mobile interface.
# ------------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")


# ------------------------------------------------------------------
# Route: POST /start_sos
# Receives GPS from frontend, kicks off drone simulation sequence.
# ------------------------------------------------------------------
@app.route("/start_sos", methods=["POST"])
def start_sos():
    try:
        data = request.get_json(force=True, silent=True) or {}

        # Safely extract GPS — may be None if browser denied location access
        lat = data.get("lat")
        lon = data.get("lon")

        # Validate that coords are real numbers if provided
        if lat is not None:
            lat = float(lat)
        if lon is not None:
            lon = float(lon)

        drone_state.gps_location = {"lat": lat, "lon": lon}

    except (ValueError, TypeError) as e:
        # GPS values were present but malformed — log and continue without them
        print(f"[WARNING] Invalid GPS data received: {e}")
        drone_state.gps_location = {"lat": None, "lon": None}

    # Reset state before starting a new session
    drone_state.drone_active = False
    drone_state.recording = False
    drone_state.ai_status = "Initializing..."

    # Kick off background simulation thread
    thread = threading.Thread(target=simulate_drone_sequence, daemon=True)
    thread.start()

    gps_note = "with GPS" if drone_state.gps_location["lat"] else "without GPS (unavailable)"
    return jsonify({
        "message": f"SOS received. Drone activating {gps_note}.",
        "gps": drone_state.gps_location
    })


# ------------------------------------------------------------------
# Simulation: Drone activation sequence (runs in background thread)
# Time 0s → Initializing
# Time 2s → Drone Activated
# Time 5s → Recording Started
# Time 8s → Human Detected
# ------------------------------------------------------------------
def simulate_drone_sequence():
    # T+2s: Drone is now airborne
    time.sleep(2)
    drone_state.drone_active = True
    drone_state.ai_status = "Drone Activated"

    # T+5s: Camera starts recording
    time.sleep(3)
    drone_state.recording = True
    drone_state.ai_status = "Camera Recording"

    # T+8s: AI detects a person
    time.sleep(3)
    drone_state.ai_status = "Human Detected"


# ------------------------------------------------------------------
# Route: GET /status
# Returns current drone state as JSON.
# Polled every few seconds by the frontend.
# ------------------------------------------------------------------
@app.route("/status")
def status():
    return jsonify(drone_state.get_state())


# ------------------------------------------------------------------
# Route: GET /video_feed
# Returns a placeholder video stream.
# Replace this route's body with real Jetson camera stream later.
# On Jetson: use cv2.VideoCapture(0) and yield MJPEG frames here.
# ------------------------------------------------------------------
@app.route("/video_feed")
def video_feed():
    placeholder_path = os.path.join(app.static_folder, "placeholder.jpg")
    if os.path.exists(placeholder_path):
        return send_file(placeholder_path, mimetype="image/jpeg")
    # If no placeholder image exists, return a simple 1x1 gray pixel
    import base64
    # Minimal valid gray JPEG
    gray_pixel = (
        b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00'
        b'\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t'
        b'\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a'
        b'\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\x1eC'
        b'\x00\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01'
        b'\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4'
        b'\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b'
        b'\xff\xc4\x00\xb5\x10\x00\x02\x01\x03\x03\x02\x04\x03\x05\x05'
        b'\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xfb\xff\xd9'
    )
    return Response(gray_pixel, mimetype="image/jpeg")


# ------------------------------------------------------------------
# Route: POST /reset
# Resets drone state back to standby.
# ------------------------------------------------------------------
@app.route("/reset", methods=["POST"])
def reset_drone():
    drone_state.reset()
    return jsonify({"message": "Drone reset to standby."})


if __name__ == "__main__":
    drone_state.reset()
    print("ShieldHer Simulation Server running at http://127.0.0.1:5000")
    app.run(debug=True, host="0.0.0.0", port=5000)
