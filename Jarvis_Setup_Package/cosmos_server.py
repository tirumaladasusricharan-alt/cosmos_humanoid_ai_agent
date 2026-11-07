"""
cosmos_server.py - C.O.S.M.O.S. Unified Backend & 3D Humanoid Engine
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Architected, Designed & Deployed Exclusively for Sri Charan Tirumaladasu ("Boss" / "Sir")

Capabilities:
1. Serves ./cosmos frontend directly on http://127.0.0.1:8080 with 0 latency
2. Full API State synchronization (/api/state, /api/mic_toggle, /api/replay, /api/mute_toggle, /api/query)
3. Extended Full-Statement Voice Listener (PyAudioWPatch hardware support, zero cut-off, .wav recording)
4. Dynamic working microphone auto-detection (DirectSound Realtek live signal isolation)
5. Strict Hardware Audio Lock preventing Realtek sound card driver collision between TTS & Mic
6. State-Bound Voice Greetings ("Namaste boss...", "Tell me sir...", "Ok boss...")
7. Auto-Popup & Dust-to-Humanoid ignition on calling "Cosmos" or pressing Alt / Alt+Space
8. Multi-Model Local Council + Live DuckDuckGo Browser Search + Polyglot Coder + Hermes Gateway
"""

import os
import sys
sys.dont_write_bytecode = True

if sys.platform == 'win32':
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
import time
import json
import threading
import subprocess
import webbrowser
import ctypes
from ctypes import wintypes
from datetime import datetime
from typing import Optional

# Ensure pyaudiowpatch is aliased before speech_recognition imports on Windows
if sys.platform == "win32":
    try:
        import pyaudiowpatch as pyaudio
        sys.modules.setdefault("pyaudio", pyaudio)
    except Exception as _pyaudio_err:
        print(f"[PyAudioWPatch Notice]: {_pyaudio_err}", flush=True)

# Ensure correct working directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
try:
    os.chdir(BASE_DIR)
except Exception:
    pass

# Safeguard stdout/stderr for background pythonw.exe execution
import tempfile
log_path = os.path.join(tempfile.gettempdir(), "cosmos_server.log")
if sys.stdout is None:
    try:
        sys.stdout = open(log_path, "a", encoding="utf-8")
    except Exception:
        pass
if sys.stderr is None:
    try:
        sys.stderr = open(log_path, "a", encoding="utf-8")
    except Exception:
        pass

import requests
import speech_recognition as sr
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Backend modules under strict zero-regression lock
import jarvis_voice
import jarvis_brain
import jarvis_actions
import cosmos_voice_full
import cosmos_live_voice
import cosmos_power_updates
from cosmos_voice_full import (
    cosmos_speak,
    cosmos_master_solve,
    log_everything_to_score,
    RECORDINGS_DIR,
    SESSION_SCORE_FILE
)

user32 = ctypes.windll.user32 if sys.platform == "win32" else None

# ═══════════════════════════════════════════════════════════════════════
#  GLOBAL STATE MANAGEMENT & HARDWARE AUDIO LOCK
# ═══════════════════════════════════════════════════════════════════════
state_lock = threading.Lock()
hardware_audio_lock = threading.Lock()
voice_ready_event = threading.Event()
voice_ready_event.set()
current_state = "idle"       # "idle" | "listening" | "talking"
mic_enabled = True           # Microphone listening active
is_muted = False             # Sound output muted
is_sleeping = False          # Background quiet mode (active after "close yourself")
has_greeted_initial = False  # Track fresh wake vs subsequent wake
last_wake_time = time.time() # Track wake trigger for dust-to-humanoid ignition
wake_counter = 0             # Increment on wake to trigger 3x particle animation
last_response = "Namaste boss, welcome to your world again."
last_transcript = ""

message_history = [
    {"id": 1, "sender": "bot", "text": "Namaste Boss! Online and ready for your commands."}
]
message_seq = 1

def add_chat_message(sender: str, text: str):
    global message_seq, message_history
    if not text or not str(text).strip():
        return
    try:
        import cosmos_openbot_features
        text = cosmos_openbot_features.scrub_openbot_secrets(str(text))
    except Exception:
        pass
    with state_lock:
        message_seq += 1
        msg = {"id": message_seq, "sender": sender, "text": str(text).strip()}
        message_history.append(msg)
        if len(message_history) > 60:
            message_history = message_history[-60:]
        return msg

app = FastAPI(title="COSMOS Humanoid AI", description="Architected by Sri Charan Tirumaladasu")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Determine Frontend Directory
FRONTEND_DIR = os.path.join(BASE_DIR, "cosmos frontend")
if not os.path.exists(FRONTEND_DIR):
    FRONTEND_DIR = os.path.join(os.path.dirname(BASE_DIR), "cosmos frontend")


# ═══════════════════════════════════════════════════════════════════════
#  PORT RECOVERY & CLEANUP
# ═══════════════════════════════════════════════════════════════════════
def free_ports(*ports):
    """Safely terminates any prior stale processes holding target ports."""
    try:
        import psutil
        current_pid = os.getpid()
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['pid'] == current_pid:
                continue
            try:
                conns = proc.net_connections(kind='inet') if hasattr(proc, 'net_connections') else proc.connections(kind='inet')
                for conn in conns:
                    if conn.laddr.port in ports:
                        print(f"[COSMOS CLEANUP] Terminating stale PID {proc.pid} holding port {conn.laddr.port}", flush=True)
                        proc.terminate()
                        try:
                            proc.wait(timeout=1.0)
                        except Exception:
                            proc.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except Exception as e:
        print(f"[Port Cleanup Notice]: {e}", flush=True)


# ═══════════════════════════════════════════════════════════════════════
#  DYNAMIC WORKING MICROPHONE AUTO-DETECTION
# ═══════════════════════════════════════════════════════════════════════
def get_best_microphone_index() -> Optional[int]:
    """Dynamically tests and selects the working hardware microphone with a clean, low-noise baseline."""
    try:
        import audioop

        # 1. Test Windows Default Recording Device (device_index=None) first
        try:
            with sr.Microphone(device_index=None) as source:
                energy = 0
                for _ in range(3):
                    buf = source.stream.read(source.CHUNK)
                    energy += audioop.rms(buf, 2)
                avg_energy = energy / 3
                # Baseline idle noise should be calm (5 to 800 RMS). Realtek DirectSound bug spikes to 16,000+!
                if 5 < avg_energy < 800:
                    print(f"[COSMOS MIC] Selected default system microphone (device_index=None, energy={avg_energy:.1f})", flush=True)
                    return None
        except Exception as def_err:
            print(f"[COSMOS MIC Default Test Note]: {def_err}", flush=True)

        p = pyaudio.PyAudio()
        candidates = []
        for i in range(p.get_device_count()):
            d = p.get_device_info_by_index(i)
            name = d.get('name', '')
            if d.get('maxInputChannels', 0) > 0 and 'loopback' not in name.lower():
                api = p.get_host_api_info_by_index(d['hostApi']).get('name', '')
                candidates.append((i, name, api))
        p.terminate()

        # Prioritize stable MME / WASAPI and heavily penalize buggy DirectSound drivers
        scored = []
        for idx, name, api in candidates:
            score = 0
            if "mme" in api.lower():
                score += 10
            elif "wasapi" in api.lower():
                score += 5
            elif "directsound" in api.lower():
                score -= 20  # Heavily penalize DirectSound due to 16,000+ DC offset driver bug
            if "microphone array" in name.lower():
                score += 5
            scored.append((score, idx, name, api))
        scored.sort(key=lambda x: x[0], reverse=True)

        for score, idx, name, api in scored:
            try:
                with sr.Microphone(device_index=idx) as source:
                    energy = 0
                    for _ in range(3):
                        buf = source.stream.read(source.CHUNK)
                        energy += audioop.rms(buf, 2)
                    avg_energy = energy / 3
                    # Only accept healthy, clean microphones (reject any DC offset buzz >= 800)
                    if 5 < avg_energy < 800:
                        print(f"[COSMOS MIC] Selected active microphone [{idx}]: {name} ({api}, energy={avg_energy:.1f})", flush=True)
                        return idx
            except Exception:
                continue
    except Exception as e:
        print(f"[COSMOS MIC Detection Note]: {e}", flush=True)
    return None


# ═══════════════════════════════════════════════════════════════════════
#  VOICE OUTPUT WRAPPER (SYNCS "TALKING" STATE & PREVENTS ECHO/COLLISION)
# ═══════════════════════════════════════════════════════════════════════
def is_audio_speaking() -> bool:
    """Returns True if COSMOS is actively synthesizing speech or playing audio through the speakers."""
    if hardware_audio_lock.locked():
        return True
    if not voice_ready_event.is_set():
        return True
    try:
        import pygame
        if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
            return True
    except Exception:
        pass
    try:
        from cosmos_natural_interruption import barge_manager
        if barge_manager.is_speaking:
            return True
    except Exception:
        pass
    return False


def speak_cosmos(text: str, full_chat_text: Optional[str] = None):
    """Speaks text while setting UI state to TALKING, routing dual-channel output, and locking hardware audio."""
    global current_state, last_response
    if not text:
        return

    # Process through dual channel layer: code blocks to chat/clipboard, acoustic speech to TTS
    proc = cosmos_live_voice.dual_channel_process(text)
    chat_display = full_chat_text if full_chat_text else proc["chat_text"]
    voice_to_speak = proc["voice_text"]

    # Auto-inject any code blocks into Windows clipboard
    if proc.get("code_blocks"):
        try:
            cosmos_power_updates.copy_code_to_clipboard(proc["code_blocks"][0])
        except Exception:
            pass

    # Pause microphone while speaking
    voice_ready_event.clear()
    time.sleep(0.08)
    with state_lock:
        current_state = "talking"
        last_response = voice_to_speak
    add_chat_message("bot", chat_display)
    print(f"\n[COSMOS VOICE]: {voice_to_speak}", flush=True)
    try:
        if not is_muted and voice_to_speak:
            with hardware_audio_lock:
                cosmos_speak(voice_to_speak)
    except Exception as e:
        print(f"[COSMOS Voice Output Error]: {e}", flush=True)
    finally:
        time.sleep(0.2)
        with state_lock:
            if mic_enabled and not is_sleeping:
                current_state = "listening"
            else:
                current_state = "idle"
        voice_ready_event.set()


# ═══════════════════════════════════════════════════════════════════════
#  WINDOW FOCUS & POPUP AUTOMATION
# ═══════════════════════════════════════════════════════════════════════
_browser_pids = set()

def launch_humanoid_window():
    """Launches the 3D Humanoid in dedicated standalone app window mode."""
    global _browser_pids
    url = f"http://127.0.0.1:8080/?v={int(time.time())}"
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    launched = False
    for browser in [chrome_path, edge_path]:
        if os.path.exists(browser):
            try:
                proc = subprocess.Popen([browser, f"--app={url}"])
                _browser_pids.add(proc.pid)
                launched = True
                break
            except Exception:
                pass
    if not launched:
        try:
            webbrowser.open(url)
        except Exception:
            pass


def _is_cosmos_frontend_hwnd(hwnd) -> bool:
    """
    Returns True ONLY if hwnd belongs to Chrome/Edge running the COSMOS frontend UI.
    CRITICAL: Never touches Antigravity IDE, VS Code, PowerShell, or Python!
    """
    if not user32 or not hwnd:
        return False
    length = user32.GetWindowTextLengthW(hwnd)
    if length <= 0:
        return False
    buff = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buff, length + 1)
    title = buff.value.lower()

    # 1. ABSOLUTE SHIELD: Never touch Antigravity IDE, VS Code, terminals, or developer tools!
    for forbidden in ("antigravity", "visual studio code", "vscode", "powershell", "cmd.exe", "terminal", "python", "cursor", "gemini"):
        if forbidden in title:
            return False

    # 2. Check Process Name: Must be Chrome or Edge
    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    try:
        import psutil
        p = psutil.Process(pid.value)
        pname = p.name().lower()
        if pname not in ("chrome.exe", "msedge.exe", "browser.exe"):
            return False
    except Exception:
        return False

    # 3. Window title must belong to the COSMOS 3D frontend
    if any(k in title for k in ("cosmos - humanoid ai", "127.0.0.1:8080", "localhost:8080", "cosmos humanoid")):
        return True
    return False


def bring_cosmos_to_front() -> bool:
    """Brings the 3D Humanoid window to the front immediately, breaking Windows 11 foreground lock."""
    global wake_counter
    wake_counter += 1
    found = False
    if not user32:
        launch_humanoid_window()
        return True
    try:
        def enum_cb(hwnd, extra):
            nonlocal found
            if _is_cosmos_frontend_hwnd(hwnd):
                user32.ShowWindow(hwnd, 9)  # SW_RESTORE
                # Simulate Alt key down/up to break Windows 11 foreground lock
                user32.keybd_event(0x12, 0, 0, 0)
                user32.keybd_event(0x12, 0, 2, 0)
                # Force Topmost momentarily to break Windows foreground lock
                user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0040)
                fore_thread = user32.GetWindowThreadProcessId(user32.GetForegroundWindow(), None)
                app_thread = ctypes.windll.kernel32.GetCurrentThreadId()
                if fore_thread != app_thread:
                    user32.AttachThreadInput(fore_thread, app_thread, True)
                    user32.BringWindowToTop(hwnd)
                    user32.SetForegroundWindow(hwnd)
                    user32.AttachThreadInput(fore_thread, app_thread, False)
                else:
                    user32.BringWindowToTop(hwnd)
                    user32.SetForegroundWindow(hwnd)
                # Release topmost to standard window
                user32.SetWindowPos(hwnd, -2, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0040)
                found = True
            return True

        EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
        user32.EnumWindows(EnumWindowsProc(enum_cb), 0)
    except Exception:
        pass

    if not found:
        launch_humanoid_window()

    return found


def close_cosmos_window():
    """Smoothly closes the COSMOS 3D Humanoid browser window without touching Antigravity, VS Code, or system tools."""
    global _browser_pids
    print("[COSMOS WINDOW] Closing 3D Humanoid browser window...", flush=True)

    # 1. Terminate tracked browser subprocesses
    for pid in list(_browser_pids):
        try:
            import psutil
            p = psutil.Process(pid)
            pname = p.name().lower()
            if pname in ("chrome.exe", "msedge.exe"):
                for child in p.children(recursive=True):
                    try:
                        child.kill()
                    except Exception:
                        pass
                p.kill()
        except Exception:
            pass
        _browser_pids.discard(pid)

    # 2. Terminate any browser process running specifically with --app=http://127.0.0.1:8080
    try:
        import psutil
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                pname = (proc.info.get('name') or '').lower()
                if pname not in ("chrome.exe", "msedge.exe"):
                    continue
                cmd = " ".join(proc.info.get('cmdline') or []).lower()
                if "--app=http://127.0.0.1:8080" in cmd or "--app=http://localhost:8080" in cmd:
                    proc.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except Exception:
        pass

    # 3. Close ONLY verified frontend HWNDs
    if user32:
        try:
            def enum_cb(hwnd, extra):
                if _is_cosmos_frontend_hwnd(hwnd):
                    user32.ShowWindow(hwnd, 0)  # SW_HIDE: vanish instantly
                    user32.PostMessageW(hwnd, 0x0112, 0xF060, 0)  # WM_SYSCOMMAND SC_CLOSE
                    user32.PostMessageW(hwnd, 0x0010, 0, 0)        # WM_CLOSE
                return True

            EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
            user32.EnumWindows(EnumWindowsProc(enum_cb), 0)
        except Exception as e:
            print(f"[Close Window Notice]: {e}", flush=True)


# ═══════════════════════════════════════════════════════════════════════
#  EXTENDED VOICE LISTENER (SAFE CYCLE MICROPHONE + ZERO CUTOFF)
# ═══════════════════════════════════════════════════════════════════════
def extended_listener_worker():
    """Continuous background listener with robust mic calibration and zero cut-off."""
    global current_state, mic_enabled, has_greeted_initial, last_transcript, last_response, last_wake_time, is_sleeping
    
    if sys.platform == "win32":
        try:
            ctypes.windll.ole32.CoInitialize(None)
        except Exception:
            pass

    best_mic_idx = get_best_microphone_index()
    recognizer = sr.Recognizer()
    recognizer.dynamic_energy_threshold = True
    recognizer.dynamic_energy_adjustment_damping = 0.15
    recognizer.dynamic_energy_ratio = 1.12
    # Proven human conversational listener settings: 0.8s pause threshold & 0.4s non-speaking duration
    recognizer.pause_threshold = 0.8
    recognizer.non_speaking_duration = 0.4

    print(f"[COSMOS LISTENER]: Worker started with microphone device index={best_mic_idx} (native hardware sample rate engine).", flush=True)

    while True:
        if not mic_enabled:
            with state_lock:
                current_state = "idle"
            time.sleep(0.3)
            continue

        try:
            # Open microphone at native hardware sample rate (44.1kHz Realtek) for maximum acoustic clarity
            with sr.Microphone(device_index=best_mic_idx) as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.8)
                # Restrain ambient baseline to stay sensitive to natural human speaking & whisper
                if recognizer.energy_threshold > 350:
                    recognizer.energy_threshold = 280
                elif recognizer.energy_threshold < 70:
                    recognizer.energy_threshold = 70
                recognizer.dynamic_energy_threshold = True
                recognizer.dynamic_energy_ratio = 1.15
                print(f"[COSMOS MIC CALIBRATED]: Sensitive baseline clamped={recognizer.energy_threshold:.1f}, dynamic ratio={recognizer.dynamic_energy_ratio}", flush=True)

                while mic_enabled:
                    # Prevent unbounded runaway threshold in background noise
                    if recognizer.energy_threshold > 450:
                        recognizer.energy_threshold = 300

                    # Wait if speech playback is active
                    if not voice_ready_event.wait(timeout=0.2):
                        continue

                    # If audio is actively speaking, maintain TALKING state and wait
                    if is_audio_speaking():
                        time.sleep(0.08)
                        continue

                    with state_lock:
                        if current_state != "talking":
                            current_state = "listening"

                    try:
                        audio = recognizer.listen(source, timeout=5, phrase_time_limit=15)
                    except sr.WaitTimeoutError:
                        continue

                    if not mic_enabled or not voice_ready_event.is_set():
                        continue

                    # Keep mic capture 100% in RAM — clean uncorrupted audio stream directly to STT
                    wav_path = ""

                    # Clean low-voice digital AGC pre-gain before STT (boosts quiet voice without clipping)
                    try:
                        import audioop
                        raw_pcm = audio.get_raw_data()
                        rms = audioop.rms(raw_pcm, 2)
                        if 10 < rms < 1200:
                            gain = min(2.5, 1800.0 / max(rms, 80))
                            boosted_pcm = audioop.mul(raw_pcm, 2, gain)
                            audio = sr.AudioData(boosted_pcm, audio.sample_rate, audio.sample_width)
                    except Exception:
                        pass

                    # Transcribe via Google STT (direct en-IN, with immediate fallback to te-IN for Telugu, then en-US)
                    query = ""
                    try:
                        query = recognizer.recognize_google(audio, language="en-IN").strip()
                    except sr.UnknownValueError:
                        try:
                            query = recognizer.recognize_google(audio, language="te-IN").strip()
                        except sr.UnknownValueError:
                            try:
                                query = recognizer.recognize_google(audio, language="en-US").strip()
                            except Exception:
                                continue
                    except sr.RequestError as e:
                        print(f"[STT API Error]: {e}", flush=True)
                        continue

                    if not query:
                        continue

                    # Filter out STT noise artifacts (e.g. isolated spaced characters like "క ర స మన క న య హ యర")
                    tokens = query.strip().split()
                    if len(tokens) >= 3 and sum(1 for t in tokens if len(t) <= 1) / len(tokens) > 0.45:
                        print(f"[COSMOS STT Noise Filtered]: '{query}'", flush=True)
                        continue

                    # Parse wake command
                    has_wake, command = jarvis_voice.parse_wake_command(query)
                    is_close = jarvis_voice.is_close_command(query)

                    # Background Quiet / Sleep Mode enforcement:
                    # If COSMOS was closed ("close yourself"), she MUST remain completely silent
                    # and must NEVER speak until the user explicitly summons her with the wake word ("COSMOS")!
                    if is_sleeping:
                        if not has_wake:
                            continue
                        else:
                            is_sleeping = False
                            print("[COSMOS WAKE]: User summoned COSMOS from sleep mode.", flush=True)

                    print(f"\n[BOSS VOICE DETECTED]: \"{query}\"", flush=True)
                    with state_lock:
                        last_transcript = query
                        current_state = "talking"
                    add_chat_message("user", query)

                    # Instant Bulletproof Barge-in / Stop Check (<50ms cutoff)
                    try:
                        import cosmos_unified_mega_suite
                        if cosmos_unified_mega_suite.unified_barge_manager.is_stop_command(query):
                            cosmos_unified_mega_suite.unified_barge_manager.trigger_interruption(f"Spoken keyword: {query}")
                            stop_audio_speaking()
                            with state_lock:
                                current_state = "idle"
                            continue
                    except Exception:
                        pass

                    # Auto-popup window & trigger dust-to-humanoid assembly whenever Cosmos is called
                    if has_wake:
                        last_wake_time = time.time()
                        bring_cosmos_to_front()

                    if is_close:
                        is_sleeping = True
                        reply = "Ok boss, I will wait for you, until your next order."
                        speak_cosmos(reply)
                        with state_lock:
                            current_state = "idle"
                        # Smoothly and completely close window after speech finishes
                        close_cosmos_window()
                        log_everything_to_score(query, reply, wav_path)
                        continue

                    if has_wake and not command:
                        # Spoke just wake word (e.g. "Hey Cosmos" / "Cosmos")
                        if not has_greeted_initial:
                            has_greeted_initial = True
                            reply = "Namaste boss, welcome to your world again."
                        else:
                            reply = "Tell me sir, what you want to say?"
                        speak_cosmos(reply)
                        log_everything_to_score(query, reply, wav_path)
                        continue

                    # Spoken command provided (either with or without wake word)
                    actual_command = command if command else query
                    has_greeted_initial = True

                    # Check if query asks to inspect screen
                    screen_info = None
                    try:
                        import jarvis_screen
                        if jarvis_screen.should_capture_screen(actual_command):
                            screen_info = jarvis_screen.capture_screen_text(actual_command)
                    except Exception as scr_err:
                        print(f"[Screen OCR Note]: {scr_err}", flush=True)

                    # 1. Obey OS, browser & automation actions (open browser, open youtube, etc.)
                    action_handled = False
                    try:
                        action_reply = jarvis_actions.try_action(actual_command)
                        if not action_reply:
                            action_reply = jarvis_actions.try_hermes_action(actual_command)
                        if action_reply:
                            speak_cosmos(action_reply)
                            log_everything_to_score(query, action_reply, wav_path)
                            action_handled = True
                    except Exception as act_err:
                        print(f"[Action Router Note]: {act_err}", flush=True)

                    if action_handled:
                        continue

                    # 2. Multi-Model Council + Universal Coder + Live Search + Screen Context + Brain
                    try:
                        if screen_info:
                            solution = jarvis_brain.think(
                                actual_command + f"\n\n[USER SCREEN CONTENT EXTRACTED VIA OCR]:\n{screen_info}",
                                screen_context=True
                            )
                        else:
                            solution = jarvis_brain.think(actual_command)
                        if not solution:
                            try:
                                import cosmos_unified_mega_suite
                                solution = cosmos_unified_mega_suite.cosmos_unified_dispatch(actual_command)
                            except Exception as mega_err:
                                print(f"[Mega Suite Spoken Fallback]: {mega_err}", flush=True)
                        if not solution:
                            is_coding_request = any(k in actual_command.lower() for k in ("code", "function", "class", "script", "debug", "fix this", "syntax", "refactor", "algorithm", "python", "javascript", "sql"))
                            if is_coding_request:
                                solution = cosmos_master_solve(actual_command)
                        if not solution:
                            solution = "I'm right here with you, Charan. I'm listening closely--tell me what's on your mind."
                        try:
                            import cosmos_emotional_solace
                            solution = cosmos_emotional_solace.sanitize_robotic_helpline(solution, user_prompt=actual_command)
                        except Exception:
                            pass
                        speak_cosmos(solution)
                        log_everything_to_score(query, solution, wav_path)
                    except Exception as brain_err:
                        err_reply = f"Sir, I encountered an issue processing that: {brain_err}"
                        speak_cosmos(err_reply)
                        log_everything_to_score(query, err_reply, wav_path)

        except Exception as mic_err:
            print(f"[Microphone Listener Exception]: {mic_err}", flush=True)
            time.sleep(1.0)


# ═══════════════════════════════════════════════════════════════════════
#  WINDOWS GLOBAL ALT / ALT+SPACE HOTKEY THREAD
# ═══════════════════════════════════════════════════════════════════════
_global_hook_proc = None
_global_hook_handle = None

def hotkey_summon_action():
    """Triggered on Alt tap, Alt+Space, or Ctrl+Alt anywhere on Windows."""
    global has_greeted_initial, current_state, last_wake_time, is_sleeping
    is_sleeping = False
    last_wake_time = time.time()
    print("\n[GLOBAL HOTKEY]: Alt / Alt+Space summoned COSMOS!", flush=True)
    
    # 1. Bring window to front
    bring_cosmos_to_front()

    # 2. State-bound voice greeting
    def greet():
        global has_greeted_initial
        if not has_greeted_initial:
            has_greeted_initial = True
            speak_cosmos("Namaste boss, welcome to your world again.")
        else:
            speak_cosmos("Tell me sir, what you want to say?")

    threading.Thread(target=greet, daemon=True).start()


def start_global_hotkey_thread():
    if sys.platform != "win32" or not user32:
        return

    global _global_hook_proc, _global_hook_handle

    def _listen():
        global _global_hook_proc, _global_hook_handle
        
        # Register standard Windows Hotkeys
        MOD_ALT = 0x0001
        MOD_CONTROL = 0x0002
        VK_SPACE = 0x20
        WM_HOTKEY = 0x0312

        user32.RegisterHotKey(None, 101, MOD_ALT, VK_SPACE)
        user32.RegisterHotKey(None, 102, MOD_CONTROL | MOD_ALT, VK_SPACE)
        user32.RegisterHotKey(None, 103, MOD_CONTROL, VK_SPACE)

        WH_KEYBOARD_LL = 13
        WM_KEYDOWN = 0x0100
        WM_KEYUP = 0x0101
        WM_SYSKEYDOWN = 0x0104
        WM_SYSKEYUP = 0x0105
        VK_ALT_KEYS = {0x12, 0xA4, 0xA5}

        class KeyboardEvent(ctypes.Structure):
            _fields_ = [
                ("vk_code", wintypes.DWORD),
                ("scan_code", wintypes.DWORD),
                ("flags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("extra_info", ctypes.c_size_t),
            ]

        hook_proc_type = ctypes.WINFUNCTYPE(
            ctypes.c_ssize_t,
            ctypes.c_int,
            ctypes.c_size_t,
            ctypes.c_void_p,
        )
        get_module_handle = ctypes.windll.kernel32.GetModuleHandleW
        get_module_handle.argtypes = (wintypes.LPCWSTR,)
        get_module_handle.restype = ctypes.c_void_p
        
        pressed_keys = set()
        alt_press_time = 0.0
        alt_combo_used = False

        def keyboard_hook(code, message, data):
            nonlocal alt_press_time, alt_combo_used
            if code == 0 and message in (WM_KEYDOWN, WM_SYSKEYDOWN, WM_KEYUP, WM_SYSKEYUP):
                event = ctypes.cast(data, ctypes.POINTER(KeyboardEvent)).contents
                key = event.vk_code
                was_alt_down = bool(pressed_keys & VK_ALT_KEYS)
                
                if message in (WM_KEYDOWN, WM_SYSKEYDOWN):
                    pressed_keys.add(key)
                else:
                    pressed_keys.discard(key)

                alt_down = bool(pressed_keys & VK_ALT_KEYS)

                if alt_down and not was_alt_down:
                    alt_press_time = time.monotonic()
                    alt_combo_used = any(k not in VK_ALT_KEYS for k in pressed_keys)
                elif alt_down and key not in VK_ALT_KEYS:
                    alt_combo_used = True

                # Single Alt tap detection
                if was_alt_down and not alt_down:
                    held = time.monotonic() - alt_press_time
                    if not alt_combo_used and 0.02 < held < 0.85:
                        hotkey_summon_action()
                    alt_combo_used = False

            return user32.CallNextHookEx(_global_hook_handle, code, message, data)

        _global_hook_proc = hook_proc_type(keyboard_hook)
        user32.SetWindowsHookExW.argtypes = (ctypes.c_int, hook_proc_type, ctypes.c_void_p, wintypes.DWORD)
        user32.SetWindowsHookExW.restype = ctypes.c_void_p
        user32.CallNextHookEx.argtypes = (ctypes.c_void_p, ctypes.c_int, ctypes.c_size_t, ctypes.c_void_p)
        user32.CallNextHookEx.restype = ctypes.c_ssize_t
        
        _global_hook_handle = user32.SetWindowsHookExW(
            WH_KEYBOARD_LL,
            _global_hook_proc,
            get_module_handle(None),
            0,
        )

        print("[COSMOS HOTKEY]: Global Alt / Alt+Space keyboard hooks active.", flush=True)
        message = wintypes.MSG()
        while True:
            result = user32.GetMessageW(ctypes.byref(message), None, 0, 0)
            if result in (-1, 0):
                break
            if message.message == WM_HOTKEY:
                hotkey_summon_action()
            user32.TranslateMessage(ctypes.byref(message))
            user32.DispatchMessageW(ctypes.byref(message))

        if _global_hook_handle:
            user32.UnhookWindowsHookEx(_global_hook_handle)
        user32.UnregisterHotKey(None, 101)
        user32.UnregisterHotKey(None, 102)
        user32.UnregisterHotKey(None, 103)

    t = threading.Thread(target=_listen, daemon=True)
    t.start()


# ═══════════════════════════════════════════════════════════════════════
#  REST API ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════
@app.post("/api/client_log")
async def client_log(request: Request):
    try:
        data = await request.json()
        print(f"\n[CLIENT JS ERROR]: {data}", flush=True)
        with open(os.path.join(BASE_DIR, "client_js_errors.log"), "a", encoding="utf-8") as f:
            f.write(datetime.now().strftime("[%Y-%m-%d %H:%M:%S] ") + json.dumps(data) + "\n")
    except Exception:
        pass
    return {"status": "logged"}


@app.get("/api/state")
async def get_state():
    """Poll endpoint consumed by frontend every 250ms."""
    with state_lock:
        effective_state = current_state
        if is_audio_speaking():
            effective_state = "talking"
        elif not mic_enabled or is_sleeping:
            effective_state = "idle"

        return {
            "state": effective_state,
            "mic_enabled": mic_enabled,
            "muted": is_muted,
            "is_sleeping": is_sleeping,
            "control_mode": getattr(sys.modules.get("cosmos_unified_mega_suite"), "COSMOS_UNIFIED_STATE", {}).get("control_mode", "agent"),
            "crisis_autonomy": getattr(sys.modules.get("cosmos_unified_mega_suite"), "COSMOS_UNIFIED_STATE", {}).get("crisis_autonomy", {}),
            "somatic": getattr(sys.modules.get("cosmos_unified_mega_suite"), "COSMOS_UNIFIED_STATE", {}).get("somatic", {}),
            "affect": getattr(sys.modules.get("cosmos_unified_mega_suite"), "COSMOS_UNIFIED_STATE", {}).get("affect", {}),
            "token_telemetry": getattr(sys.modules.get("cosmos_unified_mega_suite"), "COSMOS_UNIFIED_STATE", {}).get("token_telemetry", {}),
            "last_response": last_response,
            "last_transcript": last_transcript,
            "wake_time": last_wake_time,
            "wake_counter": wake_counter,
            "messages": list(message_history),
            "system": "COSMOS",
            "creator": "Sri Charan Tirumaladasu",
            "timestamp": time.time()
        }


@app.post("/api/mic_toggle")
async def toggle_mic():
    """Toggles Python microphone listener on or off."""
    global mic_enabled, current_state, is_sleeping
    with state_lock:
        mic_enabled = not mic_enabled
        if mic_enabled:
            current_state = "listening"
            is_sleeping = False
        else:
            current_state = "idle"
        new_state = mic_enabled
        ui_state = current_state
    print(f"[API] Microphone toggled: mic_enabled={new_state}, state={ui_state}, is_sleeping={is_sleeping}", flush=True)
    return {"mic_enabled": new_state, "state": ui_state}


@app.post("/api/replay")
async def replay_response():
    """Re-speaks the last generated response via cosmos_speak."""
    global last_response
    with state_lock:
        text = last_response
    if text:
        threading.Thread(target=speak_cosmos, args=(text,), daemon=True).start()
        return {"status": "replaying", "text": text}
    return {"status": "empty", "text": ""}



# ═══════════════════════════════════════════════════════════════════════
#  COGNEE KNOWLEDGE GRAPH REST ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════
@app.get("/api/cognee/graph")
async def get_cognee_graph():
    """Returns the live persistent knowledge graph ontology."""
    try:
        import cosmos_cognee_memory
        graph = cosmos_cognee_memory.get_graph()
        return {
            "status": "connected",
            "creator_lock": graph.creator_lock,
            "nodes": graph.nodes,
            "edges": graph.edges,
            "last_updated": graph.last_updated
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/cognee/query")
async def query_cognee(request: Request):
    """Executes a real-time semantic query across the Cognee Knowledge Graph."""
    try:
        data = await request.json()
    except Exception:
        data = {}
    q = data.get("query", "").strip()
    try:
        import cosmos_cognee_memory
        results = cosmos_cognee_memory.get_graph().search_graph(q)
        context = cosmos_cognee_memory.query_graph_sync(q)
        return {
            "status": "success",
            "query": q,
            "results": results,
            "context": context
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/mute_toggle")
async def toggle_mute():
    """Toggles audio mute."""
    global is_muted
    with state_lock:
        is_muted = not is_muted
        muted_status = is_muted
    print(f"[API] Sound mute toggled: is_muted={muted_status}", flush=True)
    return {"muted": muted_status}


@app.post("/api/camera_frame")
async def receive_camera_frame(request: Request):
    """Receives in-memory base64 webcam frame from frontend (0 MB disk impact)."""
    try:
        data = await request.json()
        b64 = (data.get("frame") or data.get("image") or data.get("camera_frame") or "").strip()
        if b64:
            if "," in b64:
                b64 = b64.split(",", 1)[1]
            try:
                import cosmos_unified_mega_suite
                cosmos_unified_mega_suite.COSMOS_UNIFIED_STATE["camera_frame_b64"] = b64
                if hasattr(cosmos_unified_mega_suite, "cosmos_eyes"):
                    with cosmos_unified_mega_suite.cosmos_eyes._lock:
                        cosmos_unified_mega_suite.cosmos_eyes.latest_frame_b64 = b64
                        cosmos_unified_mega_suite.cosmos_eyes.is_active = True
            except Exception:
                pass
            return {"status": "ok", "bytes": len(b64)}
    except Exception as e:
        return {"status": "error", "error": str(e)}
    return {"status": "empty"}


@app.post("/api/command")
@app.post("/api/query")
async def execute_query(request: Request):
    """Processes typed text query from the frontend side-chat or external API."""
    global has_greeted_initial, last_transcript, last_response, is_sleeping
    try:
        data = await request.json()
    except Exception:
        try:
            body = await request.body()
            data = json.loads(body.decode("utf-8", errors="ignore"))
        except Exception:
            data = {}
    query = (data.get("query") or data.get("command") or data.get("text") or "").strip()
    if not query:
        return {"response": ""}

    camera_frame = (data.get("camera_frame") or data.get("frame") or "").strip()
    if camera_frame:
        if "," in camera_frame:
            camera_frame = camera_frame.split(",", 1)[1]
        try:
            import cosmos_unified_mega_suite
            cosmos_unified_mega_suite.COSMOS_UNIFIED_STATE["camera_frame_b64"] = camera_frame
            if hasattr(cosmos_unified_mega_suite, "cosmos_eyes"):
                with cosmos_unified_mega_suite.cosmos_eyes._lock:
                    cosmos_unified_mega_suite.cosmos_eyes.latest_frame_b64 = camera_frame
                    cosmos_unified_mega_suite.cosmos_eyes.is_active = True
        except Exception:
            pass

    with state_lock:
        last_transcript = query
        has_greeted_initial = True
    add_chat_message("user", query)

    # Check for close command
    if jarvis_voice.is_close_command(query):
        is_sleeping = True
        reply = "Ok boss, I will wait for you, until your next order."
        def _speak_then_close():
            speak_cosmos(reply)
            close_cosmos_window()
        threading.Thread(target=_speak_then_close, daemon=True).start()
        return {"response": reply}

    # If user interacts with UI, wake up
    if is_sleeping:
        is_sleeping = False

    # Check for screen inspection request
    screen_info = None
    try:
        import jarvis_screen
        if jarvis_screen.should_capture_screen(query):
            screen_info = jarvis_screen.capture_screen_text(query)
    except Exception as scr_err:
        print(f"[Screen OCR Note]: {scr_err}", flush=True)

    # Execute action or council
    try:
        reply = jarvis_actions.try_action(query)
        if not reply:
            reply = jarvis_actions.try_hermes_action(query)
        if not reply:
            if screen_info:
                reply = jarvis_brain.think(
                    query + f"\n\n[USER SCREEN CONTENT EXTRACTED VIA OCR]:\n{screen_info}",
                    screen_context=True
                )
            else:
                reply = jarvis_brain.think(query)
            if not reply:
                try:
                    import cosmos_unified_mega_suite
                    reply = cosmos_unified_mega_suite.cosmos_unified_dispatch(query)
                except Exception as mega_err:
                    print(f"[COSMOS Mega Suite Router Note]: {mega_err}", flush=True)
            if not reply:
                is_coding_request = any(k in query.lower() for k in ("code", "function", "class", "script", "debug", "fix this", "syntax", "refactor", "algorithm", "python", "javascript", "sql"))
                if is_coding_request:
                    reply = cosmos_master_solve(query)
            if not reply:
                reply = "I'm right here with you, Charan. I'm listening closely--tell me what's on your mind."
            try:
                import cosmos_emotional_solace
                reply = cosmos_emotional_solace.sanitize_robotic_helpline(reply, user_prompt=query)
            except Exception:
                pass
    except Exception as e:
        reply = f"Error: {e}"

    threading.Thread(target=speak_cosmos, args=(reply,), daemon=True).start()
    log_everything_to_score(query, reply)
    return {"response": reply}


# ═══════════════════════════════════════════════════════════════════════
#  MOUNT FRONTEND AS PRIMARY UI ROOT
# ═══════════════════════════════════════════════════════════════════════
@app.get("/")
async def serve_index():
    global is_sleeping
    is_sleeping = False
    index_file = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(
            index_file,
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
    return JSONResponse({"status": "Frontend index.html not found", "dir": FRONTEND_DIR})

if os.path.exists(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")


# ═══════════════════════════════════════════════════════════════════════
#  SERVER STARTUP SEQUENCE
# ═══════════════════════════════════════════════════════════════════════
def initial_greeting_delayed():
    global has_greeted_initial
    time.sleep(2.5)
    with state_lock:
        if not has_greeted_initial:
            has_greeted_initial = True
    speak_cosmos("Namaste boss, welcome to your world again.")


def main():
    print("=" * 70, flush=True)
    print("  C.O.S.M.O.S. UNIFIED MULTI-BRAIN & 3D HUMANOID ENGINE", flush=True)
    print("  Architected & Deployed by Sri Charan Tirumaladasu", flush=True)
    print("  Serving Primary UI: http://127.0.0.1:8080", flush=True)
    print("=" * 70, flush=True)

    # 0. Free ports 8080 and 8765 from any previous stale processes
    free_ports(8080, 8765)
    time.sleep(0.5)

    # 1. Start Extended Voice Listener Thread (PyAudioWPatch powered)
    listener_thread = threading.Thread(target=extended_listener_worker, daemon=True)
    listener_thread.start()

    # 2. Start Windows Global Alt / Alt+Space Hotkey Thread
    start_global_hotkey_thread()

    # 3. Launch Dedicated 3D Humanoid Standalone Window automatically
    threading.Thread(target=lambda: (time.sleep(0.3), launch_humanoid_window()), daemon=True).start()

    # 4. Speak Fresh Wake Greeting
    threading.Thread(target=initial_greeting_delayed, daemon=True).start()

    # 5. Run Uvicorn Server on 127.0.0.1:8080
    config = uvicorn.Config(app, host="127.0.0.1", port=8080, log_level="info")
    server = uvicorn.Server(config)
    server.run()


if __name__ == "__main__":
    main()
