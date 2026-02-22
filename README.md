# ShieldHer – AI-Assisted Safety Drone Interface

> **Seed-money demo** built for college project presentation.
> A **simulation layer** for a real drone system (Jetson Orin Nano + YOLOv8).

---

## What This Is

ShieldHer is a mobile-first web application that simulates a drone-based personal safety system.

When a user presses **SOS**:
1. The browser captures their GPS coordinates.
2. Coordinates are sent to a Flask backend.
3. The backend simulates a drone activating, camera recording, and AI detecting a person.
4. The frontend updates live with drone status, camera feed, and AI results.

The simulation is **hardware-ready** — when you deploy this on Jetson Orin Nano, you only change one line.

---

## Project Structure

```
ShieldHer/
├── backend_simulator/
│   ├── app.py          ← Flask server + API routes
│   ├── drone_state.py  ← In-memory drone variables
│   └── templates/
│       └── index.html  ← Mobile UI
│
├── static/
│   ├── style.css       ← Dark tactical theme
│   └── script.js       ← SOS logic, GPS, status polling
│
└── README.md
```

---

## How to Run Locally

### 1. Install Python dependencies

```bash
pip install flask
```

### 2. Start the server

```bash
cd backend_simulator
python app.py
```

### 3. Open in browser

```
http://127.0.0.1:5000
```

For mobile testing on the same WiFi network, use your machine's local IP:
```
http://192.168.x.x:5000
```

---

## Simulation Mode — What Happens

| Time after SOS | Event                |
|---------------|----------------------|
| T + 0s        | Drone initializing   |
| T + 2s        | Drone activated      |
| T + 5s        | Camera recording     |
| T + 8s        | Human detected (AI)  |

All state lives in memory (`drone_state.py`). No database needed.

---

## Jetson Orin Nano Deployment

### Step 1 — Run the Flask server on Jetson

```bash
python app.py
# Server binds to 0.0.0.0:5000 automatically
```

### Step 2 — Update the frontend IP

In `static/script.js`, change **one line**:

```js
// Before (local simulation):
const DRONE_IP = "http://127.0.0.1:5000";

// After (Jetson on local network):
const DRONE_IP = "http://192.168.1.42:5000";  // ← Jetson's IP
```

### Step 3 — Replace simulation logic

In `app.py`, replace `simulate_drone_sequence()` with real hardware calls:
- Arm the drone via MAVLink / DroneKit
- Start `cv2.VideoCapture(0)` for camera
- Load and run your YOLOv8 model

The `/video_feed` endpoint is already structured to serve MJPEG frames when ready.

---

## API Reference

| Method | Route         | Description                        |
|--------|---------------|------------------------------------|
| GET    | `/`           | Serves the mobile UI               |
| POST   | `/start_sos`  | Receives GPS, starts simulation    |
| GET    | `/status`     | Returns current drone state JSON   |
| GET    | `/video_feed` | Returns camera image / stream      |
| POST   | `/reset`      | Resets drone to standby            |

---

## Tech Stack

- **Backend**: Python 3 · Flask
- **Frontend**: HTML · CSS · Vanilla JS
- **Fonts**: Orbitron · Share Tech Mono · Rajdhani
- **Target Hardware**: Jetson Orin Nano · YOLOv8

---

*ShieldHer v1.0 · Simulation Mode · Built for demo and seed funding presentation.*
