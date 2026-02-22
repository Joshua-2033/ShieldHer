# drone_state.py
# Stores all global drone simulation variables.
# This file is designed to be easily replaced by real hardware state
# when running on Jetson Orin Nano.

import random

# --- Drone State ---
drone_active = False       # Is the drone powered and flying?
recording = False          # Is the camera recording?
ai_status = "Standby"      # Current AI detection status
gps_location = {           # Last known GPS coordinates from user device
    "lat": None,
    "lon": None
}
battery_level = 100        # Simulated battery percentage

def reset():
    """Reset all drone state to default (standby)."""
    global drone_active, recording, ai_status, gps_location, battery_level
    drone_active = False
    recording = False
    ai_status = "Standby"
    gps_location = {"lat": None, "lon": None}
    battery_level = random.randint(85, 100)  # Simulate a realistic starting charge

def get_state():
    """Return current drone state as a dictionary (for /status endpoint)."""
    return {
        "drone_active": drone_active,
        "recording": recording,
        "ai_status": ai_status,
        "gps": gps_location,
        "battery": battery_level
    }
