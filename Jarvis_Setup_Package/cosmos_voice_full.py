"""
cosmos_voice_full.py - Complete Voice, Extended Listener, Browser & Multi-Brain Suite
Architected exclusively for Sri Charan Tirumaladasu ("Boss" / "Sir")

Capabilities:
1. Neural TTS Output (cosmos_speak): Edge-TTS + Pygame in-memory streaming
2. Full-Statement Voice Recorder (cosmos_listen_full_statement): 4.0s pause tolerance
3. Free Live Browser Search & Scraper (cosmos_live_web_search): DuckDuckGo HTML + BeautifulSoup
4. Multi-Model Ollama Council + Clipboard Polyglot Coder (cosmos_master_solve):
   DeepSeek-R1 (Architect) + Qwen2.5-Coder (Builder) with AST validation
"""

import ast
import asyncio
from datetime import datetime
import io
import json
import os
import re
import sys
import threading
import tkinter as tk
import urllib.parse
import urllib.request
from bs4 import BeautifulSoup
import edge_tts
import pygame
import requests

if sys.platform == "win32":
    import pyaudiowpatch as pyaudio
    sys.modules.setdefault("pyaudio", pyaudio)
else:
    import pyaudio

import speech_recognition as sr

# =====================================================================
# 1. VOICE OUTPUT ENGINE (EDGE-TTS + PYGAME IN-MEMORY STREAMING)
# =====================================================================

VOICE_NAME = "en-US-AriaNeural"
_pygame_initialized = False
_speech_lock = threading.Lock()


def _init_audio():
    global _pygame_initialized
    if not _pygame_initialized:
        try:
            pygame.mixer.init()
            _pygame_initialized = True
        except Exception:
            pass


def _clean_text_for_speech(text: str) -> str:
    """Strips code blocks and markdown symbols so COSMOS speaks naturally."""
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    text = re.sub(r"`[^`]+`", " ", text)
    text = re.sub(r"[#*_~>|]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


async def _stream_tts_to_memory(text: str) -> bytes:
    # Set volume gain to +100% for maximum audio clarity and loudness, rate=+12% for crisp real-time response
    communicate = edge_tts.Communicate(text, VOICE_NAME, rate="+12%", volume="+100%")
    audio_stream = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_stream.write(chunk["data"])
    return audio_stream.getvalue()


def cosmos_speak(text: str):
    """Speaks text out loud using 100% free Edge-TTS in-memory streaming at maximum volume."""
    clean_msg = _clean_text_for_speech(text)
    if not clean_msg:
        return
    print(f"\n[COSMOS VOICE]: {clean_msg}")
    try:
        # Maximize Windows hardware wave volume to 100%
        if sys.platform == "win32":
            try:
                ctypes.windll.winmm.waveOutSetVolume(0, 0xFFFFFFFF)
            except Exception:
                pass

        _init_audio()
        if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
        audio_bytes = asyncio.run(_stream_tts_to_memory(clean_msg))
        with _speech_lock:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            pygame.mixer.music.load(io.BytesIO(audio_bytes))
            pygame.mixer.music.set_volume(1.0)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(15)
    except Exception as e:
        print(f"[Voice Engine Error]: {e}")
        # Local fallback if edge-tts network drops
        try:
            import jarvis_voice
            jarvis_voice.speak(clean_msg)
        except Exception:
            pass


# =====================================================================
# 2. FULL-STATEMENT VOICE RECORDER (FIXES 2-3 LINE CUTOFF + SAVES AUDIO)
# =====================================================================

RECORDINGS_DIR = os.path.join(os.environ.get("TEMP", "C:\\temp"), "cosmos_ram_voice")
SESSION_SCORE_FILE = os.path.join(os.path.dirname(__file__), "cosmos_session_score.json")
# Zero disk accumulation in OneDrive - keep in temporary RAM directory only if ever needed
try:
    os.makedirs(RECORDINGS_DIR, exist_ok=True)
except Exception:
    pass


def log_everything_to_score(user_text: str, cosmos_reply: str, audio_path: str = ""):
    """Records every spoken command, audio file path, and AI response into a master score file."""
    try:
        history = []
        if os.path.exists(SESSION_SCORE_FILE):
            with open(SESSION_SCORE_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
        history.append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "boss_voice_text": user_text,
            "recorded_wav_file": audio_path,
            "cosmos_response": cosmos_reply[:1500]
        })
        with open(SESSION_SCORE_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)
    except Exception:
        pass


def cosmos_listen_full_statement(save_wav: bool = False) -> str:
    """Listens to your complete multi-sentence statement without cutting off after 2-3 lines."""
    recognizer = sr.Recognizer()

    # CRITICAL FIX: Wait 4 full seconds of silence before ending phrase, and remove time limits
    recognizer.pause_threshold = 4.0
    recognizer.non_speaking_duration = 0.8
    recognizer.dynamic_energy_threshold = True

    with sr.Microphone() as source:
        print("\n[COSMOS LISTENING]: Speak freely, Boss (4s pause tolerance active)...")
        recognizer.adjust_for_ambient_noise(source, duration=0.6)
        try:
            # phrase_time_limit=None ensures she NEVER cuts off long paragraphs
            audio_data = recognizer.listen(source, timeout=15, phrase_time_limit=None)

            wav_path = ""
            if save_wav:
                stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                wav_path = os.path.join(RECORDINGS_DIR, f"boss_voice_{stamp}.wav")
                with open(wav_path, "wb") as f:
                    f.write(audio_data.get_wav_data())

            text = recognizer.recognize_google(audio_data)
            print(f"[BOSS SAID]: {text}")
            return text
        except sr.WaitTimeoutError:
            return ""
        except sr.UnknownValueError:
            return ""
        except Exception as e:
            print(f"[Listener Error]: {e}")
            return ""


# =====================================================================
# 3. FREE LIVE BROWSER SEARCH & SCRAPER (ZERO API KEYS)
# =====================================================================

def cosmos_live_web_search(query: str, max_results: int = 4) -> str:
    """Searches the live web for free using DuckDuckGo HTML scraping."""
    url = "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote_plus(query)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            soup = BeautifulSoup(resp.read().decode("utf-8", "ignore"), "html.parser")
        snippets = []
        for res in soup.find_all("div", class_="result__body")[:max_results]:
            title = res.find("a", class_="result__a")
            snip = res.find("a", class_="result__snippet")
            if title and snip:
                snippets.append(f"- {title.get_text(strip=True)}: {snip.get_text(strip=True)}")
        return "\n".join(snippets) if snippets else "No live browser results found."
    except Exception as e:
        return f"Browser lookup error: {e}"


# =====================================================================
# 4. MULTI-MODEL OLLAMA COUNCIL + CLIPBOARD POLYGLOT CODER
# =====================================================================

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
ARCHITECT_MODEL = "deepseek-r1:8b"
CODER_MODEL = "qwen2.5-coder:7b"
HYBRID_MODEL = "qwen3:8b"


def _call_ollama(model: str, prompt: str) -> str:
    try:
        resp = requests.post(
            OLLAMA_URL,
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.2}
            },
            timeout=3.5
        )
        resp.raise_for_status()
        return resp.json().get("response", "")
    except Exception as err:
        print(f"[Ollama Call Error ({model})]: {err}")
        # Failover to cloud if local model offline
        try:
            import cosmos_multi_brain
            cloud_res = cosmos_multi_brain.query_groq_failover(prompt)
            if cloud_res:
                return cloud_res
        except Exception:
            pass
        return ""


def cosmos_master_solve(user_input: str) -> str:
    """Combines Clipboard, Live Browser, DeepSeek-R1 Logic, and Qwen2.5-Coder."""
    cosmos_speak("Processing your full request with my local council and live browser, Boss.")

    context_parts = []
    # Check Clipboard
    if any(k in user_input.lower() for k in ["clipboard", "copied", "fix this", "debug this"]):
        try:
            root = tk.Tk()
            root.withdraw()
            context_parts.append(f"CLIPBOARD CODE:\n```\n{root.clipboard_get()[:4000]}\n```")
            root.destroy()
        except Exception:
            pass

    # Check Live Browser
    if any(k in user_input.lower() for k in ["latest", "search", "news", "docs", "documentation", "browser", "2026"]):
        web_info = cosmos_live_web_search(user_input[:120])
        context_parts.append(f"LIVE BROWSER DATA:\n{web_info}")

    extra_ctx = "\n\n".join(context_parts)

    # Stage 1: DeepSeek-R1 Logical Blueprint
    logic_prompt = (
        f"You are COSMOS's Lead Architect ({ARCHITECT_MODEL}), created by Sri Charan Tirumaladasu.\n"
        f"Analyze the logic, bugs, and step-by-step plan for:\n{user_input}\n\n{extra_ctx}"
    )
    blueprint = _call_ollama(ARCHITECT_MODEL, logic_prompt)
    clean_blueprint = re.sub(r"<think>.*?</think>", "", blueprint, flags=re.DOTALL).strip()

    # Stage 2: Qwen2.5-Coder Verified Build
    code_prompt = (
        f"You are COSMOS ({CODER_MODEL}), created by Sri Charan Tirumaladasu.\n"
        f"Using this logical blueprint:\n{clean_blueprint}\n\n"
        f"Provide the complete solution and code for:\n{user_input}\n\n{extra_ctx}\n"
        f"End with SPOKEN_SUMMARY: followed by 1-2 plain-English sentences for the Boss."
    )
    raw_answer = _call_ollama(CODER_MODEL, code_prompt)

    # AST Syntax Check for Python blocks
    for py_block in re.findall(r"```python\s*(.*?)```", raw_answer, re.DOTALL):
        try:
            ast.parse(py_block)
        except SyntaxError as err:
            raw_answer = _call_ollama(
                CODER_MODEL,
                f"Fix this SyntaxError ({err}) and keep SPOKEN_SUMMARY::\n{raw_answer}"
            )
            break

    clean_final = re.sub(r"<think>.*?</think>", "", raw_answer, flags=re.DOTALL).strip()
    spoken_match = re.search(r"SPOKEN_SUMMARY:\s*(.+)", clean_final, re.DOTALL)
    if spoken_match:
        spoken_summary = spoken_match.group(1).strip()
        visual_output = clean_final.split("SPOKEN_SUMMARY:")[0].strip()
    else:
        spoken_summary = "Boss, I have completed the analysis, logged the session, and displayed the full code on your screen."
        visual_output = clean_final

    print("\n" + "=" * 70)
    print("[COSMOS MASTER OUTPUT]")
    print("=" * 70)
    print(visual_output)
    print("=" * 70 + "\n")

    cosmos_speak(spoken_summary)
    log_everything_to_score(user_input, visual_output)
    return visual_output
