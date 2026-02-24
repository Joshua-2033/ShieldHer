// shieldher/ui/static/script.js
// ShieldHer v1.1 — Mission Control Frontend Logic
//
// Responsibilities:
//   - Capture operator GPS via browser geolocation
//   - POST to /api/mission/start on SOS press
//   - Poll /api/mission/state every POLL_INTERVAL ms
//   - Update all status cards and progress steps
//
// ─── JETSON DEPLOYMENT ──────────────────────────────────────────────
// API_BASE uses window.location.origin — it automatically resolves to
// whatever host served this page.
//
//   Laptop browser  → http://127.0.0.1:5000   (local dev)
//   Phone on Wi-Fi  → http://192.168.x.x:5000 (same network)
//   Jetson deploy   → http://<jetson-ip>:5000  (production)
//
// No manual IP changes needed anywhere. Ever.
// ────────────────────────────────────────────────────────────────────

const API_BASE      = window.location.origin;
const POLL_INTERVAL = 1500;   // ms between /api/mission/state requests

let pollTimer  = null;    // setInterval reference for state polling
let missionActive = false;  // Guard against double-press

// ── triggerSOS ──────────────────────────────────────────────────────
// Entry point: called when operator presses the SOS button.
async function triggerSOS() {
  if (missionActive) return;
  missionActive = true;

  const btn = document.getElementById("sosBtn");
  btn.disabled = true;
  btn.querySelector(".sos-sublabel").textContent = "ACTIVATED";

  showPanel("progressSection");
  setMessage("Initializing mission protocol...");

  // ── Step 1: Acquire GPS ──────────────────────────────────────────
  activateStep("step1");
  let coords = { lat: null, lon: null };

  try {
    coords = await getGPS();
    setMessage("Location acquired.");
  } catch (e) {
    setMessage("Location unavailable — proceeding without GPS.");
  }
  completeStep("step1");

  // ── Step 2: Send dispatch request ────────────────────────────────
  activateStep("step2");
  setMessage("Sending dispatch request...");
  showPanel("spinner");

  try {
    const res  = await fetch(`${API_BASE}/api/mission/start`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ lat: coords.lat, lon: coords.lon })
    });
    const data = await res.json();
    hidePanel("spinner");
    setMessage(data.message || "Dispatch confirmed.");
    completeStep("step2");
  } catch (err) {
    hidePanel("spinner");
    setMessage("ERROR: Could not reach mission server.");
    console.error("[ShieldHer] Dispatch failed:", err);
    return;
  }

  // Steps 3–5 are driven by polling /api/mission/state
  startPolling();
}

// ── getGPS ──────────────────────────────────────────────────────────
// Wraps browser geolocation in a Promise.
// Rejects if unavailable or denied — caller handles gracefully.
function getGPS() {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error("Geolocation API not available"));
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
// Polls /api/mission/state and updates the UI on each response.
function startPolling() {
  pollTimer = setInterval(async () => {
    try {
      const res  = await fetch(`${API_BASE}/api/mission/state`);
      const data = await res.json();
      updateMissionPanel(data);
    } catch (err) {
      console.warn("[ShieldHer] State poll failed:", err);
    }
  }, POLL_INTERVAL);
}

// ── updateMissionPanel ───────────────────────────────────────────────
// Reads the state JSON from /api/mission/state and updates every UI element.
function updateMissionPanel(data) {
  showPanel("statusPanel");

  // ── Drone System ────────────────────────────────────────────────
  if (data.drone_active) {
    setCard("cardDrone", "valDrone", "ACTIVE", "barDrone", 100);
    completeStep("step3");
  } else {
    setCard("cardDrone", "valDrone", "INITIALIZING", "barDrone", 30);
    activateStep("step3");
  }

  // ── Recording Status ────────────────────────────────────────────
  if (data.recording_active) {
    setCard("cardRecording", "valRecording", "ACTIVE", "barRecording", 100);
    completeStep("step4");
  } else if (data.drone_active) {
    setCard("cardRecording", "valRecording", "CONNECTING", "barRecording", 50);
    activateStep("step4");
  }

  // ── AI Monitor ──────────────────────────────────────────────────
  const ai = data.ai_status || "Standby";
  const aiPct = ai === "Human Detected" ? 100
              : ai === "Monitoring"     ? 70
              : ai === "Initializing"   ? 40 : 20;

  setCard("cardAI", "valAI", ai.toUpperCase(), "barAI", aiPct);

  if (ai === "Human Detected") {
    completeStep("step5");
    document.getElementById("valAI").style.color = "var(--warn)";
    setMessage("⚠ Human detected in zone.");
    showPanel("resetSection");
  } else if (data.recording_active) {
    activateStep("step5");
    setMessage("Drone system active. AI monitoring...");
  } else if (data.drone_active) {
    setMessage("Drone active. Waiting for recording confirmation...");
  }

  // ── Battery ─────────────────────────────────────────────────────
  const bat = data.battery;
  if (bat !== undefined) {
    setCard("cardBattery", "valBattery", `${bat}%`, "barBattery", bat);
    if (bat < 30) {
      document.getElementById("barBattery").style.background = "var(--danger)";
    }
  }

  // ── GPS Coordinates ─────────────────────────────────────────────
  const gps = data.gps;
  if (gps && gps.lat !== null && gps.lon !== null) {
    const lat = parseFloat(gps.lat).toFixed(6);
    const lon = parseFloat(gps.lon).toFixed(6);
    document.getElementById("gpsCoords").textContent = `${lat}°N  ${lon}°E`;
  } else {
    document.getElementById("gpsCoords").textContent = "Signal unavailable";
  }
}

// ── resetMission ────────────────────────────────────────────────────
// Sends POST /api/mission/reset and restores the UI to initial state.
async function resetMission() {
  clearInterval(pollTimer);
  missionActive = false;

  try {
    await fetch(`${API_BASE}/api/mission/reset`, { method: "POST" });
  } catch (err) {
    console.warn("[ShieldHer] Reset request failed:", err);
  }

  // Restore button
  const btn = document.getElementById("sosBtn");
  btn.disabled = false;
  btn.querySelector(".sos-sublabel").textContent = "PRESS TO ACTIVATE";
  setMessage("");

  // Hide all post-SOS panels
  ["progressSection", "statusPanel", "resetSection", "spinner"].forEach(hidePanel);

  // Reset step states
  ["step1", "step2", "step3", "step4", "step5"].forEach(id => {
    const el = document.getElementById(id);
    if (el) {
      el.className = "step";
      el.querySelector(".step-icon").textContent = "◎";
    }
  });

  // Reset AI card color
  const aiVal = document.getElementById("valAI");
  if (aiVal) aiVal.style.color = "";
}

// ── UI Helpers ──────────────────────────────────────────────────────

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
  if (val)  val.textContent  = label;
  if (bar)  bar.style.width  = `${percent}%`;
  if (card && percent === 100) card.classList.add("active");
}
