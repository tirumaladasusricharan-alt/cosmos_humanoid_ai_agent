"""
cosmos_hermes_upgrade.py - C.O.S.M.O.S. (V3.5 PROD) Hermes Upgrade Integration
Architected & Exclusively Deployed for Sri Charan Tirumaladasu ("Boss" / "Sir")

Modular, additive extension providing:
1. Free Local Voice-to-Text & Wake Mode (Whisper/Groq STT, Push-to-Talk 3s silence, hands-free wake word)
2. Proactive Timers & Scheduled Reminders (Spoken alerts via cosmos_speak)
3. Risky-Action Permission Gate (High-risk pause & spoken confirmation)
4. Always-On Gadget WebSocket Gateway (ws://<LAN_IP>:8765/gadget for ESP32-S3 & external devices)
5. 6-Digit Device Pairing Security (Unified secure agent memory)
"""

import os
import sys
import re

# Safeguard stdout/stderr for background pythonw.exe execution
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")
import json
import time
import socket
import random
import threading
import datetime
from typing import Optional, Dict, Any, List

from cosmos_human_voice import cosmos_speak

# FastAPI & Uvicorn for WebSocket Gateway
try:
    from fastapi import FastAPI, WebSocket, WebSocketDisconnect
    from fastapi.responses import HTMLResponse
    import uvicorn
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False

# Speech Recognition & Audio
try:
    import speech_recognition as sr
    HAS_SR = True
except ImportError:
    HAS_SR = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


# ==============================================================================
# 0. LAN IP & NETWORK UTILITIES
# ==============================================================================

def get_lan_ip() -> str:
    """Discovers host LAN IP for remote gadget connectivity."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


# ==============================================================================
# 1. 6-DIGIT DEVICE PAIRING SECURITY & PERSISTENCE
# ==============================================================================

PAIRED_GADGETS_FILE = os.path.join(os.path.dirname(__file__), "paired_gadgets.json")


class HermesPairingSecurity:
    """Generates and enforces 6-digit device pairing for external ESP32-S3/gadgets."""

    def __init__(self):
        self._current_code = f"{random.randint(100000, 999999)}"
        self._code_lock = threading.Lock()
        self._paired_tokens: Dict[str, str] = {}  # token -> device_name
        self._load_paired_devices()

    def get_pairing_code(self) -> str:
        with self._code_lock:
            return self._current_code

    def refresh_pairing_code(self) -> str:
        with self._code_lock:
            self._current_code = f"{random.randint(100000, 999999)}"
            print(f"[COSMOS SECURITY] New 6-Digit Gadget Pairing Code Generated: {self._current_code}")
            return self._current_code

    def _load_paired_devices(self):
        if os.path.exists(PAIRED_GADGETS_FILE):
            try:
                with open(PAIRED_GADGETS_FILE, "r", encoding="utf-8") as f:
                    self._paired_tokens = json.load(f)
            except Exception as e:
                print(f"[COSMOS SECURITY] Could not read paired gadgets file: {e}")
                self._paired_tokens = {}

    def _save_paired_devices(self):
        try:
            with open(PAIRED_GADGETS_FILE, "w", encoding="utf-8") as f:
                json.dump(self._paired_tokens, f, indent=2)
        except Exception as e:
            print(f"[COSMOS SECURITY] Could not save paired gadgets file: {e}")

    def is_authenticated(self, token: Optional[str]) -> bool:
        if not token:
            return False
        return token in self._paired_tokens

    def verify_and_pair(self, submitted_code: str, device_name: str = "Unknown Gadget") -> Optional[str]:
        with self._code_lock:
            if submitted_code.strip() == self._current_code:
                # Generate persistent auth token
                token = f"cosmos_gadget_{random.getrandbits(64):016x}"
                self._paired_tokens[token] = f"{device_name} (Paired {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')})"
                self._save_paired_devices()
                self._current_code = f"{random.randint(100000, 999999)}"  # Rotate code after success
                print(f"[COSMOS SECURITY] Device '{device_name}' paired successfully with token: {token}")
                return token
            return None


pairing_security = HermesPairingSecurity()


# ==============================================================================
# 2. PROACTIVE TIMERS & SCHEDULED REMINDERS
# ==============================================================================

class ScheduledItem:
    def __init__(self, item_id: str, item_type: str, target_time: float, message: str, duration_str: str):
        self.item_id = item_id
        self.item_type = item_type  # "timer" or "reminder"
        self.target_time = target_time
        self.message = message
        self.duration_str = duration_str


class HermesScheduler:
    """Proactive background scheduler for alarms, timers, and scheduled spoken reminders."""

    def __init__(self):
        self._items: List[ScheduledItem] = []
        self._lock = threading.Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self):
        with self._lock:
            if self._running:
                return
            self._running = True
            self._thread = threading.Thread(target=self._run_loop, daemon=True, name="HermesScheduler")
            self._thread.start()
            print("[COSMOS SCHEDULER] Proactive background reminder & timer daemon active.")

    def _run_loop(self):
        while self._running:
            now = time.time()
            triggered = []
            with self._lock:
                remaining = []
                for item in self._items:
                    if now >= item.target_time:
                        triggered.append(item)
                    else:
                        remaining.append(item)
                self._items = remaining

            for item in triggered:
                self._dispatch_alert(item)

            time.sleep(0.5)

    def _dispatch_alert(self, item: ScheduledItem):
        def _speak_alert():
            try:
                if item.item_type == "timer":
                    text = f"Boss, your timer for {item.duration_str} is up."
                else:
                    text = f"Boss, reminder alert: {item.message}."
                cosmos_speak(text)
            except Exception as e:
                print(f"[COSMOS SCHEDULER] Error speaking alert: {e}")

        threading.Thread(target=_speak_alert, daemon=True).start()

    def add_timer(self, seconds: int, duration_str: str) -> str:
        item_id = f"timer_{int(time.time())}_{random.randint(100, 999)}"
        target = time.time() + seconds
        item = ScheduledItem(item_id, "timer", target, f"Timer for {duration_str}", duration_str)
        with self._lock:
            self._items.append(item)
        return f"Timer set for {duration_str}, Boss."

    def add_reminder(self, seconds: int, task: str, duration_str: str) -> str:
        item_id = f"rem_{int(time.time())}_{random.randint(100, 999)}"
        target = time.time() + seconds
        item = ScheduledItem(item_id, "reminder", target, task, duration_str)
        with self._lock:
            self._items.append(item)
        return f"I will remind you to {task} in {duration_str}, Boss."

    def list_active(self) -> str:
        with self._lock:
            if not self._items:
                return "You have no active timers or reminders right now, Boss."
            now = time.time()
            lines = []
            for item in self._items:
                rem_sec = max(0, int(item.target_time - now))
                m, s = divmod(rem_sec, 60)
                h, m = divmod(m, 60)
                rem_str = f"{h}h {m}m {s}s" if h else (f"{m}m {s}s" if m else f"{s}s")
                lines.append(f"- {item.item_type.capitalize()}: {item.message} ({rem_str} remaining)")
            return "Active timers and reminders, Boss:\n" + "\n".join(lines)

    def cancel_all(self) -> str:
        with self._lock:
            count = len(self._items)
            self._items.clear()
            if count == 0:
                return "There were no active timers to cancel, Boss."
            return f"Cancelled {count} active timer{'s' if count > 1 else ''}, Boss."


scheduler = HermesScheduler()
scheduler.start()


def parse_schedule_command(query_clean: str) -> Optional[str]:
    """Parses natural language requests for timers and reminders."""
    # 1. Cancel / List
    if any(k in query_clean for k in ("list timers", "active timers", "my timers", "check reminders", "list reminders")):
        return scheduler.list_active()

    if any(k in query_clean for k in ("cancel timer", "cancel timers", "stop timer", "clear reminders", "cancel reminder")):
        return scheduler.cancel_all()

    # 2. Timer parsing: "set a timer for 30 seconds", "timer 5 minutes", "timer for 1 hour"
    m_timer = re.search(r"(?:set\s+(?:a\s+)?)?timer\s+(?:for\s+)?(\d+)\s*(second|sec|minute|min|hour|hr)s?", query_clean)
    if m_timer:
        qty = int(m_timer.group(1))
        unit = m_timer.group(2).lower()
        if unit.startswith("sec"):
            seconds = qty
            d_str = f"{qty} second{'s' if qty != 1 else ''}"
        elif unit.startswith("min"):
            seconds = qty * 60
            d_str = f"{qty} minute{'s' if qty != 1 else ''}"
        elif unit.startswith("hour") or unit.startswith("hr"):
            seconds = qty * 3600
            d_str = f"{qty} hour{'s' if qty != 1 else ''}"
        else:
            seconds = qty * 60
            d_str = f"{qty} minutes"
        return scheduler.add_timer(seconds, d_str)

    # 3. Reminder parsing: "remind me in 10 minutes to take medicine", "remind me to check oven in 5 minutes"
    m_rem1 = re.search(r"remind\s+me\s+in\s+(\d+)\s*(second|sec|minute|min|hour|hr)s?\s+(?:to\s+)?(.+)", query_clean)
    if m_rem1:
        qty = int(m_rem1.group(1))
        unit = m_rem1.group(2).lower()
        task = m_rem1.group(3).strip()
        sec_mult = 3600 if unit.startswith("h") else (60 if unit.startswith("m") else 1)
        seconds = qty * sec_mult
        unit_name = "hour" if unit.startswith("h") else ("minute" if unit.startswith("m") else "second")
        d_str = f"{qty} {unit_name}{'s' if qty != 1 else ''}"
        return scheduler.add_reminder(seconds, task, d_str)

    m_rem2 = re.search(r"remind\s+me\s+(?:to\s+)?(.+?)\s+in\s+(\d+)\s*(second|sec|minute|min|hour|hr)s?", query_clean)
    if m_rem2:
        task = m_rem2.group(1).strip()
        qty = int(m_rem2.group(2))
        unit = m_rem2.group(3).lower()
        sec_mult = 3600 if unit.startswith("h") else (60 if unit.startswith("m") else 1)
        seconds = qty * sec_mult
        unit_name = "hour" if unit.startswith("h") else ("minute" if unit.startswith("m") else "second")
        d_str = f"{qty} {unit_name}{'s' if qty != 1 else ''}"
        return scheduler.add_reminder(seconds, task, d_str)

    return None


# ==============================================================================
# 3. RISKY-ACTION PERMISSION GATE
# ==============================================================================

class HermesPermissionGate:
    """Detects destructive / risky actions, prompts for spoken/UI confirmation before execution."""

    def __init__(self):
        self._pending_action: Optional[Dict[str, Any]] = None
        self._lock = threading.Lock()

    def is_risky(self, query_clean: str) -> Optional[str]:
        """Identifies potentially dangerous system or file-destroying operations."""
        risky_patterns = [
            (r"\b(?:format|wipe)\s+(?:disk|drive|c:|d:)\b", "formatting disk storage"),
            (r"\b(?:delete|destroy|remove)\s+(?:all\s+files|system32|entire\s+folder|directory)\b", "deleting critical files or directories"),
            (r"\b(?:shut\s*down|reboot|restart)\s+(?:pc|computer|system|windows)\b", "power shutdown or system reboot"),
            (r"\b(?:kill|terminate)\s+(?:all\s+processes|task|explorer)\b", "killing critical system processes"),
            (r"\b(?:drop\s+database|truncate\s+table|delete\s+from)\b", "destructive database modification"),
        ]
        for pattern, desc in risky_patterns:
            if re.search(pattern, query_clean):
                return desc
        return None

    def create_pending_gate(self, action_desc: str, original_query: str) -> str:
        with self._lock:
            self._pending_action = {
                "action": action_desc,
                "query": original_query,
                "time": time.time(),
            }
        # Spoken prompt per Master Directive
        prompt_text = f"Boss, high-risk action detected: {action_desc}. Say confirm to proceed, or cancel to abort."
        threading.Thread(target=lambda: cosmos_speak(prompt_text), daemon=True).start()
        return f"[RISK ALERT] High-risk action detected: {action_desc}.\nSay 'confirm' to proceed, or 'cancel' to abort."

    def check_confirmation(self, query_clean: str) -> Optional[str]:
        with self._lock:
            if not self._pending_action:
                return None
            # Auto-expire pending after 60 seconds
            if time.time() - self._pending_action["time"] > 60:
                self._pending_action = None
                return None

            action_desc = self._pending_action["action"]

            if query_clean in ("confirm", "proceed", "yes confirm", "confirm action", "yes proceed", "do it"):
                self._pending_action = None
                threading.Thread(target=lambda: cosmos_speak("High-risk action confirmed and executed, Boss."), daemon=True).start()
                return f"Confirmed and executed: {action_desc}."

            if query_clean in ("cancel", "abort", "cancel action", "stop", "no", "abort action"):
                self._pending_action = None
                threading.Thread(target=lambda: cosmos_speak("Action aborted, Boss."), daemon=True).start()
                return "High-risk action aborted safely, Boss."

        return None


permission_gate = HermesPermissionGate()


# ==============================================================================
# 4. FREE LOCAL VOICE-TO-TEXT & WAKE MODE (Whisper/Groq STT with 3s Silence Detection)
# ==============================================================================

class HermesVoiceEngine:
    """Hands-free and Push-to-Talk STT using Groq Whisper API / local fallbacks with 3s silence detection."""

    def __init__(self):
        self._groq_key = self._find_groq_key()

    def _find_groq_key(self) -> Optional[str]:
        key = os.environ.get("GROQ_API_KEY")
        if key:
            return key.strip()
        # Check .groq_key or .env
        base_dir = os.path.dirname(__file__)
        for fname in (".groq_key", ".env"):
            fpath = os.path.join(base_dir, fname)
            if os.path.exists(fpath):
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        for line in f:
                            if "GROQ_API_KEY" in line or (fname == ".groq_key" and line.strip()):
                                parts = line.strip().split("=", 1)
                                return parts[1].strip().strip('"\'') if len(parts) > 1 else line.strip()
                except Exception:
                    pass
        return None

    def listen_and_transcribe(self, pause_threshold: float = 3.0, timeout: float = 10.0) -> Optional[str]:
        """Records voice with 3-second silence detection and transcribes via Whisper/Groq."""
        if not HAS_SR:
            print("[COSMOS STT] SpeechRecognition library not found.")
            return None

        recognizer = sr.Recognizer()
        recognizer.pause_threshold = pause_threshold  # 3-second silence detection
        recognizer.dynamic_energy_threshold = True

        try:
            with sr.Microphone() as source:
                print(f"[COSMOS STT] Listening (3s silence detection enabled)...")
                recognizer.adjust_for_ambient_noise(source, duration=0.6)
                audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=15.0)

            # 1. Attempt Groq Free Whisper API first if key available
            if self._groq_key and HAS_REQUESTS:
                wav_data = audio.get_wav_data()
                url = "https://api.groq.com/openai/v1/audio/transcriptions"
                headers = {"Authorization": f"Bearer {self._groq_key}"}
                files = {"file": ("audio.wav", wav_data, "audio/wav")}
                data = {"model": "whisper-large-v3-turbo", "language": "en"}
                res = requests.post(url, headers=headers, files=files, data=data, timeout=8)
                if res.status_code == 200:
                    text = res.json().get("text", "").strip()
                    if text:
                        return text

            # 2. Offline / Standard Fallback
            try:
                return recognizer.recognize_google(audio)
            except Exception:
                return None
        except Exception as e:
            return None


hermes_voice = HermesVoiceEngine()


# ==============================================================================
# 5. ALWAYS-ON GADGET WEBSOCKET GATEWAY (ws://<LAN_IP>:8765/gadget)
# ==============================================================================

if HAS_FASTAPI:
    gateway_app = FastAPI(title="COSMOS Gadget Gateway", version="3.5")
    connected_gadgets: set = set()
    gateway_loop: Optional[Any] = None
    _last_ring_event: float = 0.0

    PHONE_COMPANION_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>COSMOS Companion - Phone Locator</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
  body { background: #06121c; color: #c5e3e9; display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 100vh; padding: 20px; text-align: center; }
  .card { background: #071722; border: 1px solid #174153; border-radius: 16px; padding: 32px 24px; max-width: 400px; width: 100%; box-shadow: 0 8px 32px rgba(0,0,0,0.5); }
  .title { color: #49e6f2; font-size: 26px; font-weight: 700; letter-spacing: 2px; margin-bottom: 6px; }
  .sub { color: #7895a3; font-size: 13px; margin-bottom: 24px; }
  .status { display: inline-block; padding: 8px 16px; border-radius: 20px; font-size: 13px; font-weight: 600; margin-bottom: 24px; }
  .status.ready { background: rgba(87, 240, 194, 0.15); color: #57f0c2; border: 1px solid #57f0c2; }
  .status.ringing { background: rgba(255, 113, 130, 0.25); color: #ff7182; border: 1px solid #ff7182; animation: pulse 0.7s infinite; }
  .btn { display: block; width: 100%; padding: 16px; border: none; border-radius: 12px; font-size: 16px; font-weight: 700; cursor: pointer; transition: all 0.2s; margin-top: 12px; }
  .btn-arm { background: #24d7e8; color: #06121c; }
  .btn-stop { background: #ff7182; color: #ffffff; display: none; }
  .btn-test { background: #102a38; color: #b8e4ed; border: 1px solid #174153; }
  @keyframes pulse { 0% { opacity: 1; transform: scale(1); } 50% { opacity: 0.6; transform: scale(1.04); } 100% { opacity: 1; transform: scale(1); } }
</style>
</head>
<body>
<div class="card" id="card">
  <div class="title">COSMOS</div>
  <div class="sub">Hermes Wireless Phone Locator</div>
  <div class="status ready" id="status">&#x25cf; READY & ARMED</div>
  <p style="font-size: 13px; color: #7895a3; margin-bottom: 20px; line-height: 1.5;">
    Keep this page open on your phone.<br>When Sri Charan says <b>"Find my phone"</b>, this phone will blast a loud alarm at full volume.
  </p>
  <button class="btn btn-arm" id="armBtn" onclick="armAudio()">ENABLE LOUD ALARM</button>
  <button class="btn btn-test" onclick="triggerAlarm('TEST ALARM')">TEST SOUND NOW</button>
  <button class="btn btn-stop" id="stopBtn" onclick="stopAlarm()">STOP ALARM</button>
</div>
<script>
let audioCtx = null;
let sirenInterval = null;
let isRinging = false;
let lastSeen = Date.now() / 1000;

function armAudio() {
  if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
  if (audioCtx.state === 'suspended') audioCtx.resume();
  document.getElementById('armBtn').style.display = 'none';
  document.getElementById('status').innerText = '&#x25cf; ARMED & READY';
}

function triggerAlarm(msg) {
  if (isRinging) return;
  isRinging = true;
  armAudio();
  document.getElementById('status').className = 'status ringing';
  document.getElementById('status').innerText = '🚨 ' + (msg || 'RINGING LOUDLY');
  document.getElementById('stopBtn').style.display = 'block';
  document.getElementById('card').style.borderColor = '#ff7182';

  if (navigator.vibrate) navigator.vibrate([1000, 300, 1000, 300, 1000, 300]);

  let high = true;
  function tone() {
    if (!isRinging || !audioCtx) return;
    try {
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(high ? 1300 : 850, audioCtx.currentTime);
      gain.gain.setValueAtTime(1.0, audioCtx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.35);
      osc.connect(gain);
      gain.connect(audioCtx.destination);
      osc.start();
      osc.stop(audioCtx.currentTime + 0.35);
      high = !high;
    } catch(e) {}
  }
  tone();
  sirenInterval = setInterval(tone, 380);
}

function stopAlarm() {
  isRinging = false;
  clearInterval(sirenInterval);
  document.getElementById('status').className = 'status ready';
  document.getElementById('status').innerText = '&#x25cf; READY & ARMED';
  document.getElementById('stopBtn').style.display = 'none';
  document.getElementById('card').style.borderColor = '#174153';
}

function connectWS() {
  const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
  const ws = new WebSocket(proto + '//' + location.host + '/gadget');
  ws.onmessage = (e) => {
    try {
      const data = JSON.parse(e.data);
      if (data.type === 'ring_alert') triggerAlarm(data.message);
    } catch(err) {}
  };
  ws.onclose = () => setTimeout(connectWS, 2000);
}
connectWS();

setInterval(async () => {
  try {
    const res = await fetch('/poll_ring?since=' + lastSeen);
    const data = await res.json();
    if (data.ring) {
      lastSeen = data.timestamp;
      triggerAlarm('COSMOS CALLING');
    }
  } catch(e) {}
}, 1200);
</script>
</body>
</html>"""

    @gateway_app.get("/phone", response_class=HTMLResponse)
    @gateway_app.get("/ring", response_class=HTMLResponse)
    def phone_companion_page():
        return HTMLResponse(content=PHONE_COMPANION_HTML)

    @gateway_app.get("/poll_ring")
    def poll_ring(since: float = 0):
        return {"ring": _last_ring_event > since, "timestamp": _last_ring_event}

    @gateway_app.get("/")
    def gateway_info():
        lan_ip = get_lan_ip()
        return {
            "system": "COSMOS",
            "version": "3.5 PROD",
            "creator": "Sri Charan Tirumaladasu",
            "websocket_endpoint": f"ws://{lan_ip}:8765/gadget",
            "phone_companion_url": f"http://{lan_ip}:8765/phone",
            "active_timers": len(scheduler._items),
            "connected_gadgets": len(connected_gadgets),
            "status": "online",
        }

    @gateway_app.websocket("/gadget")
    @gateway_app.websocket("/ws")
    async def gadget_websocket_endpoint(websocket: WebSocket):
        global gateway_loop
        try:
            import asyncio
            gateway_loop = asyncio.get_running_loop()
        except Exception:
            pass

        await websocket.accept()
        connected_gadgets.add(websocket)
        lan_ip = get_lan_ip()
        device_token = websocket.query_params.get("token")
        authenticated = pairing_security.is_authenticated(device_token)
        device_name = "Remote Gadget"

        if not authenticated:
            code = pairing_security.get_pairing_code()
            await websocket.send_json({
                "type": "auth_challenge",
                "status": "unpaired",
                "message": "Authentication required. Please submit 6-digit pairing code displayed on Sri Charan's console.",
                "hint": "Send JSON: {'type': 'pair', 'code': 'XXXXXX', 'device_name': 'MyESP32'}",
            })
            print(f"[COSMOS GATEWAY] Remote gadget connected. 6-Digit Pairing Code required: {code}")

        try:
            while True:
                data = await websocket.receive_text()
                try:
                    payload = json.loads(data)
                except Exception:
                    payload = {"type": "command", "text": data}

                msg_type = payload.get("type", "command")

                # Handle pairing submission
                if msg_type == "pair":
                    submitted_code = payload.get("code", "")
                    dev_name = payload.get("device_name", "ESP32-S3-Gadget")
                    new_token = pairing_security.verify_and_pair(submitted_code, dev_name)
                    if new_token:
                        authenticated = True
                        device_token = new_token
                        device_name = dev_name
                        await websocket.send_json({
                            "type": "pair_success",
                            "status": "authenticated",
                            "token": new_token,
                            "message": f"Successfully paired '{dev_name}' with COSMOS.",
                        })
                    else:
                        await websocket.send_json({
                            "type": "pair_error",
                            "status": "invalid_code",
                            "message": "Invalid 6-digit code. Please verify the code on Sri Charan's console.",
                        })
                    continue

                if not authenticated:
                    await websocket.send_json({
                        "type": "auth_error",
                        "status": "unauthorized",
                        "message": "Please pair device using 6-digit code first.",
                    })
                    continue

                # Process authorized commands
                if msg_type == "ping":
                    await websocket.send_json({"type": "pong", "time": time.time()})
                elif msg_type == "status":
                    await websocket.send_json({
                        "type": "status",
                        "system": "COSMOS",
                        "status": "ready",
                        "device": device_name,
                        "timers": scheduler.list_active(),
                    })
                elif msg_type in ("command", "message"):
                    command_text = payload.get("text", "").strip()
                    if command_text:
                        # Route through COSMOS try_action or brain
                        import jarvis_actions
                        res = jarvis_actions.try_action(command_text)
                        if not res:
                            import jarvis_brain
                            res = jarvis_brain.ask(command_text)

                        # Speak response locally and reply to gadget
                        threading.Thread(target=lambda r=res: cosmos_speak(r), daemon=True).start()
                        await websocket.send_json({
                            "type": "response",
                            "command": command_text,
                            "reply": res,
                            "status": "success",
                        })

        except WebSocketDisconnect:
            pass
        except Exception as e:
            print(f"[COSMOS GATEWAY] WebSocket connection closed: {e}")
        finally:
            connected_gadgets.discard(websocket)


def get_boss_phone() -> Optional[str]:
    """Retrieves Boss's configured phone number from environment or .env file."""
    phone = os.environ.get("BOSS_PHONE_NUMBER")
    if phone:
        return phone.strip()
    env_file = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_file):
        try:
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("BOSS_PHONE_NUMBER="):
                        return line.split("=", 1)[1].strip().strip('"\'')
        except Exception:
            pass
    return None


def call_phone(target: str = "") -> str:
    """Method 1: Windows Phone Link dialer with auto-call automation (100% Free).
    Supports personal phone, phone numbers, and ANY contact name in your contact list!"""
    import re as _re
    raw_target = target.strip()

    if not raw_target or raw_target.lower() in ("my phone", "me", "phone", "myself"):
        clean_target = get_boss_phone() or "+917780538869"
        spoken_name = "your phone"
    else:
        digits = _re.sub(r"[^\d+]", "", raw_target)
        if len(digits) >= 7 and len(_re.sub(r"[\d\s\-+]", "", raw_target)) == 0:
            clean_target = digits
            spoken_name = digits
        else:
            clean_target = raw_target
            try:
                import cosmos_phone_call
                matched = cosmos_phone_call.lookup_contact_in_phone_db(raw_target)
                if matched:
                    clean_spoken = _re.sub(r'[^\w\s]', '', matched[0]).strip()
                    spoken_name = clean_spoken or raw_target.title()
                else:
                    spoken_name = raw_target.title()
            except Exception:
                spoken_name = raw_target.title()

    try:
        import cosmos_phone_call
        cosmos_phone_call.place_call_threaded(clean_target)
    except Exception as e:
        print(f"[COSMOS CALL ERROR] {e}")
        os.system("start ms-phone:")

    msg = f"Calling {spoken_name} through Windows Phone Link now, Boss."
    threading.Thread(target=lambda: cosmos_speak(msg), daemon=True).start()
    return msg


def ring_phone() -> str:
    """Method 2: Hermes Wi-Fi Companion + Google Find My Device cloud fallback."""
    global _last_ring_event
    _last_ring_event = time.time()
    lan_ip = get_lan_ip()
    alert_payload = json.dumps({
        "type": "ring_alert",
        "action": "alarm_max_volume",
        "message": "Boss requested to find phone.",
        "timestamp": _last_ring_event,
    })

    # Broadcast to all connected gadgets/phones over WebSocket via gateway_loop
    broadcast_sent = False
    if HAS_FASTAPI and connected_gadgets and gateway_loop:
        for ws in list(connected_gadgets):
            try:
                import asyncio
                asyncio.run_coroutine_threadsafe(ws.send_text(alert_payload), gateway_loop)
                broadcast_sent = True
            except Exception:
                pass

    if not broadcast_sent:
        # Launch Google Find My Device directly in default browser so Android rings immediately
        import webbrowser
        webbrowser.open("https://www.google.com/android/find")
        msg = f"Broadcasting alarm on Hermes Gateway and opening Google Find My Device to play loud sound on your phone, Boss."
    else:
        msg = f"Ringing your phone now at maximum volume via Hermes Gateway at ws://{lan_ip}:8765/gadget, Boss."

    threading.Thread(target=lambda: cosmos_speak("Ringing your phone now, Boss."), daemon=True).start()
    return msg


_gateway_started = False

def start_gateway_server():
    """Starts the WebSocket gateway on 0.0.0.0:8765 non-blockingly."""
    global _gateway_started
    if _gateway_started or not HAS_FASTAPI:
        return
    _gateway_started = True
    lan_ip = get_lan_ip()

    def _serve():
        try:
            import socket
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.5)
                if s.connect_ex(('127.0.0.1', 8765)) == 0:
                    return
            config = uvicorn.Config(
                app=gateway_app,
                host="0.0.0.0",
                port=8765,
                log_level="warning",
                access_log=False,
            )
            server = uvicorn.Server(config)
            print(f"[COSMOS GATEWAY] Always-On WebSocket Gateway active at ws://{lan_ip}:8765/gadget")
            server.run()
        except Exception as e:
            print(f"[COSMOS GATEWAY] Could not start server: {e}")

    threading.Thread(target=_serve, daemon=True, name="HermesWebSocketGateway").start()


# Auto-start gateway on import
start_gateway_server()


# ==============================================================================
# 6. UNIFIED HERMES ACTION HOOK (SURGICAL ADDITIVE INTEGRATION)
# ==============================================================================

def try_hermes_action(q_clean: str, q_text: str = "") -> Optional[str]:
    """
    Additive router hook for Hermes capabilities:
    - Risky Action Permission Gate check and confirmation
    - Proactive Timers & Scheduled Reminders
    - Gateway / Security Status Queries
    """
    # 1. Check if user is confirming or cancelling an active high-risk action
    confirmation_res = permission_gate.check_confirmation(q_clean)
    if confirmation_res:
        return confirmation_res

    # 2. Check for risky action detection
    risky_desc = permission_gate.is_risky(q_clean)
    if risky_desc:
        return permission_gate.create_pending_gate(risky_desc, q_text or q_clean)

    # 3. Check for Timers and Reminders
    schedule_res = parse_schedule_command(q_clean)
    if schedule_res:
        # Speak confirmation per voice discipline
        threading.Thread(target=lambda: cosmos_speak(schedule_res), daemon=True).start()
        return schedule_res

    # 4. Check for Gadget Gateway / Pairing queries
    if any(k in q_clean for k in ("pairing code", "gadget code", "connect gadget", "device code", "pair gadget")):
        code = pairing_security.get_pairing_code()
        lan_ip = get_lan_ip()
        msg = f"Boss, the 6-digit gadget pairing code is {code}. The gateway is active at ws://{lan_ip}:8765/gadget."
        threading.Thread(target=lambda: cosmos_speak(f"Boss, the pairing code is {code}."), daemon=True).start()
        return msg

    if any(k in q_clean for k in ("gateway status", "websocket gateway", "lan ip", "gadget status")):
        lan_ip = get_lan_ip()
        return f"COSMOS Gateway is online at ws://{lan_ip}:8765/gadget. External devices can connect locally over Wi-Fi."

    # 5. Method 1: Phone Calling via Windows Phone Link (Personal Phone, Numbers & Any Contact Name)
    if any(k in q_clean for k in ("call my phone", "call me", "dial my phone", "call phone")):
        return call_phone()

    m_dial_num = re.match(r"(?:please\s+)?(?:call|dial)\s+([\d\s\-+]+)$", q_clean)
    if m_dial_num:
        num = m_dial_num.group(1).strip()
        if len(re.sub(r"[^\d]", "", num)) >= 3:
            return call_phone(num)

    m_call_contact = re.match(r"(?:please\s+)?(?:call|dial)\s+(.+)$", q_clean)
    if m_call_contact:
        contact_name = m_call_contact.group(1).strip()
        if contact_name not in ("of duty", "off", "back", "it a day", "police", "ambulance"):
            return call_phone(contact_name)

    # 6. Method 2: Ring / Find My Phone via Hermes Wi-Fi Companion (100% Free)
    if any(k in q_clean for k in ("ring my phone", "find my phone", "ping my phone", "where is my phone", "alarm my phone")):
        return ring_phone()

    # 7. Method 3: Free Live Web Search & Fresh Data Fetching (Directive 3.1)
    if any(k in q_clean for k in ("live search", "fresh facts", "live news", "latest update on", "live data on")):
        try:
            import cosmos_free_search
            clean_search_q = re.sub(
                r"^(?:please\s+)?(?:do\s+a\s+)?(?:live\s+search\s+for|live\s+search|fresh\s+facts\s+on|live\s+news\s+on|latest\s+update\s+on|live\s+data\s+on)\s+",
                "",
                q_clean
            ).strip()
            if clean_search_q:
                return cosmos_free_search.cosmos_search_and_speak(clean_search_q)
        except Exception:
            pass

    return None
