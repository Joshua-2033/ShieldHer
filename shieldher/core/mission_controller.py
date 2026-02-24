# shieldher/core/mission_controller.py
# ShieldHer — Mission Controller
#
# This is the bridge between the operator UI and the drone hardware.
# It receives commands from app.py and translates them into system actions.
#
# Current mode: LOCAL (subprocess placeholders)
# Jetson integration: replace subprocess calls with real MAVLink / SDK calls.
#
# Functions:
#   start_mission(lat, lon)  → arm system, start external scripts
#   reset_mission()          → disarm system, clear state
#   update_ai_status(status) → push AI status update into shared state

import subprocess
import sys
import os

# Add root to path so shieldher package resolves when run from any directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from shieldher.core import drone_state


def start_mission(lat: float | None, lon: float | None) -> None:
    """
    Called when the operator presses SOS.

    1. Writes GPS into shared state.
    2. Marks system as active.
    3. Launches external drone + AI scripts via subprocess.

    Jetson integration point:
        Replace subprocess lines with MAVLink arm commands
        or your drone SDK's takeoff call.
    """
    # Write operator location into shared state
    drone_state.gps_location = {"lat": lat, "lon": lon}

    # Mark mission as live
    drone_state.drone_active    = True
    drone_state.recording_active = True
    drone_state.ai_status       = "Initializing"

    # ── External script launch ─────────────────────────────────────
    # TODO (Jetson): Replace with real drone controller integration.
    # Example for Jetson:
    #   subprocess.Popen(["python3", "/opt/shieldher/drone_demo.py"])
    #   subprocess.Popen(["python3", "/opt/shieldher/ai_detect.py"])
    #
    # For LOCAL mode, these calls are intentionally left as placeholders.
    # Uncomment and point to your actual scripts when hardware is ready.

    if _is_jetson_mode():
        _launch_drone_script()
        _launch_ai_script()
    else:
        print("[MissionController] LOCAL mode — external scripts not launched.")
        print(f"[MissionController] Mission started. GPS: lat={lat}, lon={lon}")


def reset_mission() -> None:
    """
    Resets all shared state back to standby.
    Called when the operator presses RESET or on server restart.

    Jetson integration point:
        Send disarm command to drone before clearing state.
    """
    # TODO (Jetson): Send disarm / return-to-home command here.

    drone_state.drone_active     = False
    drone_state.recording_active = False
    drone_state.ai_status        = "Standby"
    drone_state.gps_location     = {"lat": None, "lon": None}

    print("[MissionController] Mission reset. System at standby.")


def update_ai_status(status: str) -> None:
    """
    Updates the AI detection status in shared state.

    Called by:
      - tests/manual_trigger.py  (developer testing)
      - Future: AI script pushing updates via internal API

    Args:
        status: Human-readable status string, e.g. "Human Detected"
    """
    drone_state.ai_status = status
    print(f"[MissionController] AI status updated → {status}")


# ── Internal Helpers ───────────────────────────────────────────────

def _is_jetson_mode() -> bool:
    """Returns True if config specifies Jetson deployment."""
    try:
        from shieldher import config
        return config.MISSION_MODE == "JETSON"
    except ImportError:
        return False


def _launch_drone_script() -> None:
    """
    Launches the external drone control script.
    Jetson integration point — update path to your actual script.
    """
    try:
        subprocess.Popen(
            ["python3", "drone_demo.py"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        print("[MissionController] Drone script launched.")
    except FileNotFoundError:
        print("[MissionController] WARNING: drone_demo.py not found. Skipping.")


def _launch_ai_script() -> None:
    """
    Launches the external YOLOv8 AI detection script.
    Jetson integration point — update path to your actual script.
    """
    try:
        subprocess.Popen(
            ["python3", "ai_detect.py"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        print("[MissionController] AI detection script launched.")
    except FileNotFoundError:
        print("[MissionController] WARNING: ai_detect.py not found. Skipping.")
