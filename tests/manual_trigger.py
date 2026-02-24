# tests/manual_trigger.py
# ShieldHer — Manual Mission Trigger (Developer Tool)
#
# Purpose:
#   Allows a developer to manually push state updates into the RUNNING
#   ShieldHer server without needing a real drone or AI script.
#
# How it works:
#   Sends HTTP requests to the Flask server — the same way the browser
#   does. This means changes are made inside the server's own memory,
#   so the UI sees them instantly via its polling loop.
#
#   ⚠ Previous approach (direct import + write) did NOT work because
#   Python imports create a separate copy of the module in a new process.
#   Writing to that copy never touched the running Flask server's memory.
#
# Requirements:
#   - ShieldHer server (app.py) must already be running
#   - ENABLE_MANUAL_TRIGGER = True in config.py
#
# Usage:
#   cd ShieldHer/
#   python tests/manual_trigger.py
#   python tests/manual_trigger.py --host 192.168.1.42  (Jetson on network)

import sys
import argparse

try:
    import requests
except ImportError:
    print("[ManualTrigger] Missing dependency. Run: pip install requests")
    sys.exit(1)


# ── Config ────────────────────────────────────────────────────────
DEFAULT_HOST = "http://127.0.0.1:5000"


def build_base_url(host: str) -> str:
    """Ensure host has http:// prefix."""
    if not host.startswith("http"):
        host = f"http://{host}"
    return host.rstrip("/")


# ── API Calls (HTTP → Flask server) ───────────────────────────────

def api_patch_state(base_url: str, payload: dict) -> bool:
    """
    POST to /api/mission/patch — sends a partial state update to the server.
    Returns True on success.
    """
    try:
        res = requests.post(f"{base_url}/api/mission/patch", json=payload, timeout=3)
        res.raise_for_status()
        return True
    except requests.exceptions.ConnectionError:
        print(f"\n  ✗ Cannot reach server at {base_url}")
        print("    Is app.py running?\n")
        return False
    except requests.exceptions.HTTPError as e:
        print(f"\n  ✗ Server returned error: {e}\n")
        return False


def api_get_state(base_url: str) -> dict | None:
    """GET /api/mission/state — fetch live state from server."""
    try:
        res = requests.get(f"{base_url}/api/mission/state", timeout=3)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print(f"  ✗ Could not fetch state: {e}")
        return None


def api_reset(base_url: str) -> bool:
    """POST /api/mission/reset."""
    try:
        res = requests.post(f"{base_url}/api/mission/reset", timeout=3)
        res.raise_for_status()
        return True
    except Exception as e:
        print(f"  ✗ Reset failed: {e}")
        return False


def api_start_mission(base_url: str) -> bool:
    """POST /api/mission/start with null GPS."""
    try:
        res = requests.post(
            f"{base_url}/api/mission/start",
            json={"lat": None, "lon": None},
            timeout=3
        )
        res.raise_for_status()
        return True
    except Exception as e:
        print(f"  ✗ Mission start failed: {e}")
        return False


# ── Display ───────────────────────────────────────────────────────

def print_state(base_url: str) -> None:
    state = api_get_state(base_url)
    if not state:
        return
    print("\n── Live Server State ───────────────────────────")
    print(f"  drone_active    : {state.get('drone_active')}")
    print(f"  recording_active: {state.get('recording_active')}")
    print(f"  ai_status       : {state.get('ai_status')}")
    print(f"  gps             : {state.get('gps')}")
    print(f"  battery         : {state.get('battery')}%")
    print("────────────────────────────────────────────────\n")


# ── Menu ──────────────────────────────────────────────────────────

def run_menu(base_url: str) -> None:
    print("\n╔══════════════════════════════════════╗")
    print("║   ShieldHer — Manual Trigger Tool   ║")
    print(f"║   Server : {base_url[:28].ljust(26)} ║")
    print("╚══════════════════════════════════════╝\n")

    options = {
        "1": ("Start mission (no GPS)",      lambda: api_start_mission(base_url)),
        "2": ("Set AI → Initializing",       lambda: api_patch_state(base_url, {"ai_status": "Initializing"})),
        "3": ("Set AI → Monitoring",         lambda: api_patch_state(base_url, {"ai_status": "Monitoring"})),
        "4": ("Set AI → Human Detected",     lambda: api_patch_state(base_url, {"ai_status": "Human Detected"})),
        "5": ("Set AI → No Target",          lambda: api_patch_state(base_url, {"ai_status": "No Target"})),
        "6": ("Activate drone system",       lambda: api_patch_state(base_url, {"drone_active": True})),
        "7": ("Activate recording",          lambda: api_patch_state(base_url, {"recording_active": True})),
        "8": ("Print live server state",     lambda: print_state(base_url)),
        "9": ("Reset mission",               lambda: api_reset(base_url)),
        "q": ("Quit",                        None),
    }

    while True:
        print("Select action:")
        for key, (label, _) in options.items():
            print(f"  [{key}] {label}")

        choice = input("\n> ").strip().lower()

        if choice == "q":
            print("Exiting.")
            break
        elif choice in options:
            label, action = options[choice]
            if action:
                success = action()
                if success is not False:
                    print(f"  ✓ {label}")
        else:
            print("  Invalid choice.\n")


# ── Entry Point ───────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ShieldHer Manual Trigger")
    parser.add_argument(
        "--host",
        default=DEFAULT_HOST,
        help="Server base URL or IP (default: http://127.0.0.1:5000)"
    )
    args = parser.parse_args()
    base_url = build_base_url(args.host)
    run_menu(base_url)
