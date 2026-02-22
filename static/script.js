// script.js
// ShieldHer – Frontend Logic
// Handles SOS trigger, GPS capture, API calls, and live status polling.
//
// ─── JETSON COMPATIBILITY ───────────────────────────────────────────
// To connect to a real Jetson Orin Nano, change DRONE_IP to the
// device's IP address. No other changes needed.
// Example: const DRONE_IP = "http://192.168.1.42:5000";
// ────────────────────────────────────────────────────────────────────
const DRONE_IP = "http://127.0.0.1:5000";

// Polling interval in milliseconds
const POLL_INTERVAL = 1500;

let pollTimer = null;    // Reference to polling interval
let vidTimer = null;     // Reference to video timestamp updater
let vidSeconds = 0;      // Video recording elapsed seconds
let sosActive = false;   // Track if SOS is currently active

// ── triggerSOS ──────────────────────────────────────────────────────
// Called when the user taps the SOS button.
// 1. Gets GPS from browser
// 2. Sends location to backend
// 3. Starts status polling
async function triggerSOS() {
  if (sosActive) return;
  sosActive = true;

  const btn = document.getElementById("sosBtn");
  btn.disabled = true;
  btn.querySelector(".sos-sublabel").textContent = "ACTIVATED";

  showProgress();
  setMessage("Initializing emergency protocol...");

  // Step 1: Get GPS
  activateStep("step1");
  let coords = { lat: null, lon: null };

  try {
    coords = await getGPS();
    setMessage("GPS acquired.");
  } catch (e) {
    setMessage("GPS unavailable. Sending without coordinates.");
  }
  completeStep("step1");

  // Step 2: Send to backend
  activateStep("step2");
  setMessage("Sending SOS to drone server...");
  showPanel("spinner");  // ← show spinner while awaiting server

  try {
    const res = await fetch(`${DRONE_IP}/start_sos`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ lat: coords.lat, lon: coords.lon })
    });
    const data = await res.json();
    hidePanel("spinner");  // ← hide once we get a response
    setMessage(data.message || "SOS dispatched.");
    completeStep("step2");
  } catch (e) {
    hidePanel("spinner");
    setMessage("Error: Could not reach drone server.");
    console.error("SOS send failed:", e);
    return;
  }

  // Steps 3–5 will be activated by the status poller
  startPolling();
  startVideoTimer();
}

// ── getGPS ──────────────────────────────────────────────────────────
// Returns a Promise that resolves with { lat, lon } from browser GPS.
function getGPS() {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error("Geolocation not supported"));
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => resolve({ lat: pos.coords.latitude, lon: pos.coords.longitude }),
      (err) => reject(err),
      { timeout: 8000, enableHighAccuracy: true }
    );
  });
}

// ── startPolling ────────────────────────────────────────────────────
// Polls /status every POLL_INTERVAL ms and updates the UI.
function startPolling() {
  pollTimer = setInterval(async () => {
    try {
      const res = await fetch(`${DRONE_IP}/status`);
      const data = await res.json();
      updateStatusPanel(data);
    } catch (e) {
      console.warn("Status poll failed:", e);
    }
  }, POLL_INTERVAL);
}

// ── updateStatusPanel ───────────────────────────────────────────────
// Takes JSON from /status and updates all UI cards + progress steps.
function updateStatusPanel(data) {
  showPanel("statusPanel");

  // Drone status
  if (data.drone_active) {
    setCard("cardDrone", "valDrone", "ACTIVE", "barDrone", 100);
    completeStep("step3");
    setMessage("Drone is airborne and responding.");
  } else {
    setCard("cardDrone", "valDrone", "INITIALIZING", "barDrone", 30);
    activateStep("step3");
  }

  // Camera status
  if (data.recording) {
    setCard("cardCamera", "valCamera", "RECORDING", "barCamera", 100);
    completeStep("step4");
    showPanel("videoSection");
  } else if (data.drone_active) {
    setCard("cardCamera", "valCamera", "CONNECTING", "barCamera", 50);
    activateStep("step4");
  }

  // AI status
  const aiStatus = data.ai_status || "Standby";
  const aiPercent = aiStatus === "Human Detected" ? 100
                  : aiStatus === "Camera Recording" ? 70
                  : aiStatus === "Drone Activated" ? 40 : 20;
  setCard("cardAI", "valAI", aiStatus.toUpperCase(), "barAI", aiPercent);

  if (aiStatus === "Human Detected") {
    completeStep("step5");
    document.getElementById("valAI").style.color = "var(--warn)";
    setMessage("⚠ Human detected in zone.");
  } else if (data.recording) {
    activateStep("step5");
  }

  // Battery
  if (data.battery) {
    const bat = data.battery;
    setCard("cardBattery", "valBattery", `${bat}%`, "barBattery", bat);
    if (bat < 30) document.getElementById("barBattery").style.background = "var(--danger)";
  }

  // GPS
  if (data.gps && data.gps.lat !== null) {
    const lat = parseFloat(data.gps.lat).toFixed(6);
    const lon = parseFloat(data.gps.lon).toFixed(6);
    document.getElementById("gpsCoords").textContent = `${lat}°N  ${lon}°E`;
  } else {
    document.getElementById("gpsCoords").textContent = "Signal acquiring...";
  }

  // Show reset button once everything is running
  if (data.ai_status === "Human Detected") {
    showPanel("resetSection");
  }
}

// ── startVideoTimer ─────────────────────────────────────────────────
// Updates the video timestamp overlay every second.
function startVideoTimer() {
  vidSeconds = 0;
  vidTimer = setInterval(() => {
    vidSeconds++;
    const h = String(Math.floor(vidSeconds / 3600)).padStart(2, "0");
    const m = String(Math.floor((vidSeconds % 3600) / 60)).padStart(2, "0");
    const s = String(vidSeconds % 60).padStart(2, "0");
    const el = document.getElementById("vidTimestamp");
    if (el) el.textContent = `${h}:${m}:${s}`;
  }, 1000);
}

// ── resetSystem ─────────────────────────────────────────────────────
// Sends reset request to backend and restores UI to initial state.
async function resetSystem() {
  clearInterval(pollTimer);
  clearInterval(vidTimer);
  sosActive = false;

  try {
    await fetch(`${DRONE_IP}/reset`, { method: "POST" });
  } catch (e) {
    console.warn("Reset call failed:", e);
  }

  // Restore UI
  document.getElementById("sosBtn").disabled = false;
  document.getElementById("sosBtn").querySelector(".sos-sublabel").textContent = "PRESS TO ACTIVATE";
  document.getElementById("sosMessage").textContent = "";

  hidePanel("progressSection");
  hidePanel("statusPanel");
  hidePanel("videoSection");
  hidePanel("resetSection");
  hidePanel("spinner");

  // Reset all steps
  ["step1","step2","step3","step4","step5"].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.className = "step";
  });
}

// ── UI Helpers ──────────────────────────────────────────────────────

function showProgress() {
  showPanel("progressSection");
}

function setMessage(msg) {
  const el = document.getElementById("sosMessage");
  if (el) el.textContent = msg;
}

function showPanel(id) {
  const el = document.getElementById(id);
  if (el) el.classList.remove("hidden");
}

function hidePanel(id) {
  const el = document.getElementById(id);
  if (el) el.classList.add("hidden");
}

function activateStep(id) {
  const el = document.getElementById(id);
  if (el && !el.classList.contains("done")) {
    el.className = "step active";
  }
}

function completeStep(id) {
  const el = document.getElementById(id);
  if (el) {
    el.className = "step done";
    el.querySelector(".step-icon").textContent = "✓";
  }
}

function setCard(cardId, valId, label, barId, percent) {
  const card = document.getElementById(cardId);
  const val  = document.getElementById(valId);
  const bar  = document.getElementById(barId);
  if (val) val.textContent = label;
  if (bar) bar.style.width = `${percent}%`;
  if (card && percent === 100) card.classList.add("active");
}
