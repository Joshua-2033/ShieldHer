# ShieldHer v1.1
## AI-Assisted Safety Drone — Mission Control Interface

ShieldHer is a **local mission control interface** for a drone-based personal safety system.

It is **not** drone firmware. It is the **operator-facing command layer** that:
- Receives SOS + GPS from the operator's phone browser
- Sends commands to the Jetson Orin Nano backend
- Launches external drone and AI detection scripts
- Displays live mission status

---

## Architecture

```
ShieldHer/
│
├── shieldher/
│   ├── config.py                   ← Runtime flags (HOST, PORT, MODE)
│   │
│   ├── server/
│   │   └── app.py                  ← Flask API server
│   │
│   ├── core/
│   │   ├── mission_controller.py   ← Command bridge to hardware
│   │   └── drone_state.py          ← Shared runtime variables
│   │
│   └── ui/
│       ├── templates/
│       │   └── index.html          ← Operator mission control UI
│       └── static/
│           ├── style.css
│           └── script.js
│
├── tests/
│   └── manual_trigger.py           ← Developer state injection tool
│
└── README.md
```

---

## API Endpoints

| Method | Route                  | Purpose                                        |
|--------|------------------------|------------------------------------------------|
| GET    | `/`                    | Serve mission control UI                       |
| POST   | `/api/mission/start`   | Receive SOS + GPS, activate mission            |
| GET    | `/api/mission/state`   | Return live mission state (polled by UI)       |
| POST   | `/api/mission/reset`   | Reset mission to standby                       |
| POST   | `/api/mission/patch`   | Inject state updates (dev tool, gated by config) |

---

## How to Run Locally

### 1. Install dependencies

```bash
pip install flask requests
```

### 2. Start the server

```bash
cd ShieldHer
python3 -m shieldher.server.app
```

> Using `python3 -m` ensures all internal package imports (`shieldher.core`, `shieldher.config`) resolve correctly regardless of where you run from. Running `python app.py` directly from inside the folder will cause import errors.

### 3. Open the interface

```
http://127.0.0.1:5000
```

On the same Wi-Fi network (phone testing):
```
http://<your-machine-ip>:5000
```

> **GPS on mobile:** Location capture is implemented but may not function on mobile devices over non-HTTPS local networks due to browser security policies. Use ngrok or laptop testing for full GPS demo. HTTPS support is planned for v1.2.

---

## Developer Testing (No Hardware)

Use `manual_trigger.py` to inject state updates into a running server
without a drone or AI script connected.

```bash
# Local testing (default — targets 127.0.0.1)
cd ShieldHer
python tests/manual_trigger.py

# Optional — when targeting Jetson over Wi-Fi
python tests/manual_trigger.py --host <jetson-ip>
```

The tool presents an interactive menu:
- Set AI status (Initializing / Monitoring / Human Detected)
- Activate drone / recording flags
- Print current live server state
- Reset all state

> Requires `ENABLE_MANUAL_TRIGGER = True` in `shieldher/config.py`
>
> **This tool is disabled automatically when `ENABLE_MANUAL_TRIGGER = False`.
> It is intended only for development and simulation — set it to `False` before any production deployment.**

---

## Known Limitations

**GPS on mobile browsers**

Location capture is implemented and the backend fully accepts coordinates. However, mobile browsers enforce a Secure Context requirement — the Geolocation API is silently blocked on plain `http://` pages. This is a browser security policy, not a ShieldHer bug.

For the current version, GPS works reliably on laptop browsers at `http://127.0.0.1:5000`. Mobile GPS support via HTTPS (ngrok or self-signed certificate) is planned for v1.2.

---

## Jetson Orin Nano Deployment

### Step 1 — Update config.py

```python
HOST         = "0.0.0.0"   # already correct
PORT         = 5000        # already correct
MISSION_MODE = "JETSON"    # ← change this
```

### Step 2 — No frontend changes needed

`script.js` uses `window.location.origin` — API calls automatically
target whichever IP the browser used to load the page. Phone, laptop,
or Jetson all work without touching any code.

### Step 3 — Point mission_controller.py to real scripts

In `shieldher/core/mission_controller.py`, update the subprocess paths:

```python
# _launch_drone_script():
subprocess.Popen(["python3", "/opt/shieldher/drone_demo.py"])

# _launch_ai_script():
subprocess.Popen(["python3", "/opt/shieldher/ai_detect.py"])
```

### Step 4 — Run on Jetson

```bash
cd ShieldHer
python3 -m shieldher.server.app
```

Phone connects to: `http://<jetson-ip>:5000`

---

## State Reference

All variables live in `shieldher/core/drone_state.py`:

| Variable          | Type    | Description                          |
|-------------------|---------|--------------------------------------|
| `drone_active`    | bool    | Drone system acknowledged and live   |
| `recording_active`| bool    | Recording system confirmed active    |
| `ai_status`       | str     | Current AI detection status string   |
| `gps_location`    | dict    | `{lat, lon}` from operator browser   |
| `battery_level`   | int     | Battery percentage                   |

---

## Version History

| Version | Notes                                              |
|---------|----------------------------------------------------|
| v1.0    | Initial simulation with timer-based state changes  |
| v1.1    | Professional architecture, subprocess integration, structured API, manual trigger tool |

---

*ShieldHer v1.1 · Local Mission Control · Jetson Orin Nano Ready*
