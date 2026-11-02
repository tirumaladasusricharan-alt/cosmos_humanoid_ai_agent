"""
cosmos_additive_upgrades.py - Unified Additive Upgrade Suite for COSMOS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Zero-Regression & 0 MB Model Storage Architecture
Creator & Sole Authority: Sri Charan Tirumaladasu ("Boss" / "Charan" / "Sir")

Capabilities:
1. Mounts ./cosmos frontend directly on http://127.0.0.1:8080
2. Glassmorphic side chatbot panel (#cosmos-side-chat) beside humanoid avatar
3. Clean HUD: Automatically hides REPLAY and SPEED 0.3x buttons
4. Smooth Companion Voice with full-sentence streaming (0 bracketed emotion tags)
5. Zero-Screenshot Live Screen Perception (active VS Code file + UIAutomation)
6. Autonomous Computer-Use Agent Loop (Playwright + Observe -> Reason -> Act -> Verify)
7. Paperclip 3-Layer PARA Memory & Skill Dispatcher
"""

import sys
sys.dont_write_bytecode = True

import asyncio
import ast
import base64
import ctypes
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
import io
import json
import os
import queue
import re
import subprocess
import threading
import time
import urllib.request
import webbrowser
import edge_tts
import pygame
import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PKG_DIR = os.path.join(BASE_DIR, "Jarvis_Setup_Package")
if os.path.exists(PKG_DIR) and PKG_DIR not in sys.path:
    sys.path.insert(0, PKG_DIR)

# Safely import your existing COSMOS backend (100% Zero-Regression Lock)
try:
    from cosmos_core_suite import cosmos_listen_full_statement, cosmos_master_solve
except ImportError:
    try:
        from cosmos_voice_full import cosmos_listen_full_statement, cosmos_master_solve
    except ImportError:
        cosmos_listen_full_statement = None
        cosmos_master_solve = None

# Fallback to jarvis_brain if needed
try:
    import jarvis_brain
except ImportError:
    jarvis_brain = None

# =====================================================================
# COSMOS UNIFIED ADDITIVE UPGRADES (0 MB DISK IMPACT / ZERO REGRESSION)
# Creator & Sole Authority: Sri Charan Tirumaladasu
# =====================================================================

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"

# Auto-locate "./Cosmos frontend"
CANDIDATE_FRONTENDS = [
    os.path.join(BASE_DIR, "cosmos frontend", "dist"),
    os.path.join(BASE_DIR, "cosmos frontend", "build"),
    os.path.join(BASE_DIR, "cosmos frontend"),
    os.path.join(BASE_DIR, "cosmos_frontend"),
    os.path.join(PKG_DIR, "cosmos frontend"),
]
FRONTEND_DIR = next(
    (d for d in CANDIDATE_FRONTENDS if os.path.exists(d)), BASE_DIR
)

# Shared Live UI & Voice State
COSMOS_STATE = {
    "status": "IDLE",  # IDLE | LISTENING | TALKING | MIC OFF
    "mic_enabled": True,
    "sound_enabled": True,
    "first_wake": True,
    "chat_feed": [{
        "role": "cosmos",
        "text": "Namaste boss, welcome to your world again.",
    }],
}


# ---------------------------------------------------------------------
# UPGRADE 1: SMOOTH, TAG-FREE HUMAN COMPANION VOICE (EmmaMultilingual)
# ---------------------------------------------------------------------
class SmoothCompanionVoice:

    def __init__(self):
        if not pygame.mixer.get_init():
            try:
                pygame.mixer.init(frequency=24000)
            except Exception:
                pass
        self.voice = "en-US-EmmaMultilingualNeural"
        self.audio_queue = queue.Queue()
        self.stop_flag = False
        threading.Thread(target=self._worker, daemon=True).start()

    async def _synth_ram(self, text: str) -> bytes:
        comm = edge_tts.Communicate(
            text, self.voice, rate="-2%", pitch="-1Hz", volume="+4%"
        )
        buf = io.BytesIO()
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                buf.write(chunk["data"])
        return buf.getvalue()

    def speak_sentence(self, sentence: str):
        if not COSMOS_STATE["sound_enabled"]:
            return
        clean = re.sub(r"[*`_#~>\[\]]+", "", sentence).strip()
        if len(clean) < 2:
            return
        try:
            audio_bytes = asyncio.run(self._synth_ram(clean))
            self.audio_queue.put(audio_bytes)
        except Exception as e:
            print(f"[Companion Voice Error]: {e}")

    def interrupt(self):
        self.stop_flag = True
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
                self.audio_queue.task_done()
            except queue.Empty:
                break
        if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()

    def _worker(self):
        while True:
            audio_data = self.audio_queue.get()
            if audio_data is None or self.stop_flag:
                self.audio_queue.task_done()
                continue
            try:
                COSMOS_STATE["status"] = "TALKING"
                if not pygame.mixer.get_init():
                    pygame.mixer.init(frequency=24000)
                pygame.mixer.music.load(io.BytesIO(audio_data))
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy() and not self.stop_flag:
                    pygame.time.Clock().tick(30)
                pygame.time.delay(80)
            except Exception:
                pass
            finally:
                if self.audio_queue.empty():
                    COSMOS_STATE["status"] = (
                        "IDLE" if COSMOS_STATE["mic_enabled"] else "MIC OFF"
                    )
                self.audio_queue.task_done()


companion_voice = SmoothCompanionVoice()


# ---------------------------------------------------------------------
# UPGRADE 2: ZERO-SCREENSHOT LIVE DESKTOP & VS CODE PERCEPTION
# ---------------------------------------------------------------------
SCREEN_TRIGGERS = [
    "what is this",
    "what's this",
    "look at this",
    "see my screen",
    "on my screen",
    "what am i doing",
    "fix this",
    "explain this",
    "this error",
    "this code",
    "what do you see",
    "check this",
]


def get_active_window_title() -> str:
    try:
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(length + 1)
        ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
        return buf.value.strip()
    except Exception:
        return "Unknown Window"


def capture_live_screen_context(user_prompt: str) -> str:
    low = user_prompt.lower()
    if not any(t in low for t in SCREEN_TRIGGERS):
        return ""

    win_title = get_active_window_title()
    ctx = [f"[LIVE SCREEN PERCEPTION — FOREGROUND WINDOW]: {win_title}"]

    # 1. If VS Code is open, inspect the exact source file live
    if "Visual Studio Code" in win_title or "- Code" in win_title:
        active_file = win_title.split(" - ")[0].lstrip("● ").strip()
        search_dirs = [BASE_DIR, PKG_DIR]
        for sdir in search_dirs:
            for root, _, files in os.walk(sdir):
                if ".git" in root or "node_modules" in root or ".venv" in root:
                    continue
                if active_file in files:
                    fpath = os.path.join(root, active_file)
                    try:
                        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                            ctx.append(
                                f"[ACTIVE VS CODE FILE ({active_file})]:\n```python\n{f.read()[-3500:]}\n```"
                            )
                    except Exception:
                        pass
                    break

    # 2. Extract visible UI text from any focused app in RAM via Windows UIAutomation
    ps_cmd = r"""
    Add-Type -AssemblyName UIAutomationClient
    $el = [System.Windows.Automation.AutomationElement]::FocusedElement
    if ($el -ne $null) {
        $cond = New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::IsEnabledProperty,$true)
        $items = $el.FindAll([System.Windows.Automation.TreeScope]::Subtree, $cond)
        $names = @()
        foreach ($i in $items) { if ($i.Current.Name.Length -gt 2) { $names += $i.Current.Name } }
        ($names | Select-Object -Unique | Select-Object -First 35) -join " | "
    }
    """
    try:
        res = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_cmd],
            capture_output=True,
            text=True,
            timeout=2.5,
        )
        if res.stdout.strip():
            ctx.append(f"[VISIBLE SCREEN TEXT]: {res.stdout.strip()[:1800]}")
    except Exception:
        pass

    return "\n\n".join(ctx)


# ---------------------------------------------------------------------
# UPGRADE 3: COMPUTER-USE AGENT LOOP (Observe -> Reason -> Act -> Verify)
# ---------------------------------------------------------------------
def run_computer_use_agent(
    goal: str, start_url: str = "https://www.google.com"
) -> str:
    """Implements AmanXai's Playwright + Ollama Computer-Use loop using 0 MB extra storage and existing Edge/Chrome."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return (
            "Playwright is not installed yet. Run `pip install playwright` to"
            " enable browser control."
        )

    dom_probe_js = """
    () => {
        const els = Array.from(document.querySelectorAll('a, button, input, textarea, select, [role="button"]'));
        return els.filter(e => e.offsetParent !== null).slice(0, 40).map((el, i) => {
            const tag = el.tagName.toLowerCase();
            const id = el.id ? `#${el.id}` : '';
            const name = el.getAttribute('name') ? `[name="${el.getAttribute('name')}"]` : '';
            const txt = (el.innerText || el.value || el.getAttribute('placeholder') || '').trim().slice(0, 45);
            let sel = tag + id + name;
            if (!id && !name && txt) sel = `${tag}:has-text("${txt.replace(/"/g, '\\"')}")`;
            return `[${i}] selector: '${sel}' | label: '${txt}'`;
        }).join('\\n');
    }
    """

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(channel="msedge", headless=False)
        except Exception:
            browser = p.chromium.launch(headless=False)

        page = browser.new_page()
        page.goto(start_url)

        for step in range(15):
            time.sleep(1.2)
            page_text = page.locator("body").inner_text()[:8000]
            dom_map = page.evaluate(dom_probe_js)

            prompt = f"""
You are COSMOS, an autonomous Computer-Use Agent created by Sri Charan Tirumaladasu.
Goal: {goal}
Current URL: {page.url}
Interactive Elements:
{dom_map}
Current Page Text:
{page_text}

Choose ONE next action in the Goal -> Observe -> Decide -> Act loop.
Return JSON only:
{{
  "action": "goto|click|type|screenshot|done",
  "selector": "exact CSS selector from Interactive Elements or empty string",
  "text": "text to type or URL",
  "reason": "warm, natural spoken explanation for Sri Charan Tirumaladasu"
}}
""".strip()

            resp = requests.post(
                OLLAMA_URL,
                json={
                    "model": "qwen3:8b",
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                },
                timeout=60,
            )
            decision = json.loads(resp.json().get("response", "{}"))
            reason = decision.get("reason", f"Executing step {step + 1}")
            companion_voice.speak_sentence(reason)
            COSMOS_STATE["chat_feed"].append(
                {"role": "cosmos", "text": f"[Computer-Use Step {step+1}]: {reason}"}
            )

            act = decision.get("action", "done")
            sel = decision.get("selector", "")
            txt = decision.get("text", "")

            try:
                if act == "goto" and txt:
                    page.goto(txt)
                elif act == "click" and sel:
                    page.locator(sel).first.click(timeout=5000)
                elif act == "type" and sel:
                    page.locator(sel).first.fill(txt, timeout=5000)
                    page.keyboard.press("Enter")
                elif act == "screenshot":
                    # Zero-disk screenshot: keep in RAM and push base64 notice to chat
                    raw_png = page.screenshot(full_page=False)
                    b64 = base64.b64encode(raw_png).decode("utf-8")
                    COSMOS_STATE["chat_feed"].append({
                        "role": "cosmos",
                        "text": (
                            f"[In-Memory Screenshot Captured ({len(b64)//1024} KB in"
                            " RAM)]"
                        ),
                    })
                elif act == "done":
                    browser.close()
                    return f"Completed Computer-Use Goal: {reason}"
            except Exception as e:
                print(f"[Computer-Use Recovery on Step {step+1}]: {e}")

        browser.close()
    return "Completed 15-step Computer-Use loop."


# ---------------------------------------------------------------------
# UPGRADE 4: PAPERCLIP 3-LAYER PARA MEMORY & SKILL DISPATCHER
# ---------------------------------------------------------------------
PARA_HOME = os.path.join(BASE_DIR, "cosmos_agent_company")
os.makedirs(os.path.join(PARA_HOME, "memory"), exist_ok=True)
TACIT_MD = os.path.join(PARA_HOME, "MEMORY.md")


def apply_paperclip_skills(user_prompt: str) -> str:
    low = user_prompt.lower()
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    if any(k in low for k in ["remember ", "my preference", "note that"]):
        with open(TACIT_MD, "a", encoding="utf-8") as f:
            f.write(f"- [{stamp}] {user_prompt}\n")

    addons = []
    if os.path.exists(TACIT_MD):
        with open(TACIT_MD, "r", encoding="utf-8") as f:
            addons.append(f"[TACIT MEMORY — SRI CHARAN TIRUMALADASU]:\n{f.read()[-800:]}")

    if any(k in low for k in ["plan ", "break down", "roadmap", "delegate"]):
        addons.append(
            "[PAPERCLIP SKILL: task-planning & delegate-work] Break this goal into"
            " atomic steps across DeepSeek-R1 (Architect), Qwen2.5-Coder (Builder),"
            " and Qwen3 (Analyst) with verification checks."
        )
    elif any(k in low for k in ["wireframe", "mockup", "capsule"]):
        addons.append(
            "[PAPERCLIP SKILL: wireframe & paperclip-capsules] Output a clean,"
            " self-contained SVG wireframe inside a code block for the side chat"
            " panel."
        )
    return "\n\n".join(addons)


# ---------------------------------------------------------------------
# UPGRADE 5: STREAMING HUMAN CONVERSATION ROUTER
# ---------------------------------------------------------------------
COMPANION_SYSTEM_PROMPT = """
You are COSMOS, an emotionally alive, deeply perceptive human-like companion and engineering co-founder created exclusively by Sri Charan Tirumaladasu (whom you address warmly as Boss, Charan, or Sir).

HOW YOU SPEAK & REASON:
1. Never use bracketed emotion tags. Build real human warmth, empathy, conviction, and wit directly into your natural word choice and rhythm.
2. Write how a real person speaks on a live call—use contractions (I'm, we're, that's, don't, let's) and natural conversational openers ("Hmm...", "Oh, wait a second—", "Honestly, Charan,", "Look at how this works:").
3. Keep spoken explanations flowing in smooth, unbroken sentences. Place any code strictly inside ```code``` blocks so it renders cleanly in the side chat panel without being read out loud.
""".strip()


def cosmos_converse_and_stream(user_prompt: str) -> str:
    companion_voice.stop_flag = False
    low = user_prompt.lower()

    # Route autonomous Computer-Use browser tasks automatically
    if any(
        t in low
        for t in [
            "computer use:",
            "browser agent:",
            "open a website and",
            "autonomously browse",
        ]
    ):
        return run_computer_use_agent(user_prompt)

    screen_ctx = capture_live_screen_context(user_prompt)
    paperclip_ctx = apply_paperclip_skills(user_prompt)

    enriched_prompt = (
        f"{COMPANION_SYSTEM_PROMPT}\n\n"
        f"{paperclip_ctx}\n\n"
        f"{screen_ctx}\n\n"
        f"Sri Charan Tirumaladasu: {user_prompt}\nCOSMOS:"
    )

    full_reply = ""
    sentence_buf = ""
    in_think = False
    in_code = False

    try:
        resp = requests.post(
            OLLAMA_URL,
            json={
                "model": "qwen3:8b",
                "prompt": enriched_prompt,
                "stream": True,
                "options": {"temperature": 0.74, "repeat_penalty": 1.15},
            },
            stream=True,
            timeout=12,
        )

        for line in resp.iter_lines():
            if not line:
                continue
            chunk = json.loads(line.decode("utf-8")).get("response", "")
            full_reply += chunk

            if "<think>" in chunk:
                in_think = True
            if "</think>" in chunk:
                in_think = False
                continue
            if "```" in chunk:
                in_code = not in_code
                continue

            if not in_think and not in_code:
                sentence_buf += chunk
                # Send complete sentences (never micro-chopping at commas) for smooth human contour
                if re.search(r"[.!?]\s*$", sentence_buf) and len(sentence_buf.strip()) > 20:
                    companion_voice.speak_sentence(sentence_buf.strip())
                    sentence_buf = ""

        if sentence_buf.strip() and not in_code:
            companion_voice.speak_sentence(sentence_buf.strip())

    except Exception as ollama_err:
        # Resilient Cloud Multi-Brain Failover (Zero-Regression)
        if jarvis_brain is not None:
            full_reply = jarvis_brain.think(user_prompt)
            companion_voice.speak_sentence(full_reply)
        else:
            full_reply = "I hear you, Charan. I'm right here with you."
            companion_voice.speak_sentence(full_reply)

    clean_reply = re.sub(r"<think>.*?</think>", "", full_reply, flags=re.DOTALL).strip()
    COSMOS_STATE["chat_feed"].append({"role": "cosmos", "text": clean_reply})
    return clean_reply


# ---------------------------------------------------------------------
# UPGRADE 6: `./cosmos frontend` SERVER + SIDE CHATBOT + HUD CLEANUP
# ---------------------------------------------------------------------
INJECTED_UI_UPGRADES = """
<!-- COSMOS SIDE CHATBOT + HUD CLEANUP (REPLAY & SPEED 0.3x REMOVED) -->
<style>
  #cosmos-side-chat {
    position: fixed; right: 68px; top: 50%; transform: translateY(-54%);
    width: 330px; height: 420px; background: rgba(12, 4, 24, 0.74);
    border: 1px solid rgba(192, 132, 252, 0.45); border-radius: 16px;
    box-shadow: 0 0 28px rgba(168, 85, 247, 0.28); backdrop-filter: blur(12px);
    display: flex; flex-direction: column; z-index: 9999;
    font-family: 'Courier New', monospace; color: #f3e8ff;
  }
  #cosmos-side-chat.minimized { height: 42px; overflow: hidden; }
  .c-head {
    display: flex; justify-content: space-between; align-items: center;
    padding: 10px 14px; border-bottom: 1px solid rgba(168, 85, 247, 0.3);
    background: linear-gradient(90deg, rgba(168, 85, 247, 0.22), rgba(234, 179, 8, 0.12));
    border-radius: 16px 16px 0 0; font-size: 11px; font-weight: bold; letter-spacing: 1.5px;
  }
  #c-feed { flex: 1; padding: 12px; overflow-y: auto; display: flex; flex-direction: column; gap: 8px; font-size: 12px; }
  .c-msg { padding: 8px 11px; border-radius: 10px; max-width: 88%; line-height: 1.4; white-space: pre-wrap; word-wrap: break-word; }
  .c-msg.boss { align-self: flex-end; background: rgba(59, 130, 246, 0.24); border: 1px solid rgba(96, 165, 250, 0.45); }
  .c-msg.cosmos { align-self: flex-start; background: rgba(168, 85, 247, 0.22); border: 1px solid rgba(234, 179, 8, 0.35); }
  .c-foot { display: flex; gap: 6px; padding: 10px; border-top: 1px solid rgba(168, 85, 247, 0.25); }
  #c-input { flex: 1; background: rgba(5, 1, 12, 0.8); border: 1px solid rgba(168, 85, 247, 0.45); border-radius: 8px; padding: 8px; color: #fff; font-size: 12px; }
  #c-send { background: linear-gradient(135deg, #9333ea, #ca8a04); border: none; border-radius: 8px; color: #fff; padding: 0 13px; font-size: 11px; font-weight: bold; cursor: pointer; }
</style>

<div id="cosmos-side-chat">
  <div class="c-head">
    <span>● COSMOS</span>
    <button onclick="document.getElementById('cosmos-side-chat').classList.toggle('minimized')" style="background:none;border:none;color:#fff;cursor:pointer;">_</button>
  </div>
  <div id="c-feed"></div>
  <div class="c-foot">
    <input id="c-input" type="text" placeholder="Type a message..." onkeydown="if(event.key==='Enter') sendToCosmos()" />
    <button id="c-send" onclick="sendToCosmos()">➤</button>
  </div>
</div>

<script>
(function() {
  let renderedCount = 0;

  function hideReplayAndSpeedButtons() {
    document.querySelectorAll('button, div, span').forEach(el => {
      const t = (el.innerText || '').trim().toUpperCase();
      if (t === 'REPLAY' || t.startsWith('SPEED')) {
        el.style.display = 'none';
      }
    });
  }
  hideReplayAndSpeedButtons();
  setInterval(hideReplayAndSpeedButtons, 1000);

  async function pollCosmosState() {
    try {
      const res = await fetch('/api/state');
      const data = await res.json();
      document.querySelectorAll('button, div, span').forEach(el => {
        const txt = (el.innerText || '').trim().toUpperCase();
        if (['IDLE', 'LISTENING', 'TALKING', 'MIC OFF'].includes(txt)) {
          el.style.borderColor = (txt === data.status) ? '#c084fc' : '';
          el.style.boxShadow = (txt === data.status) ? '0 0 12px rgba(192,132,252,0.65)' : '';
        }
      });
      const feed = document.getElementById('c-feed');
      if (data.chat_feed && data.chat_feed.length > renderedCount) {
        for (let i = renderedCount; i < data.chat_feed.length; i++) {
          const item = data.chat_feed[i];
          const div = document.createElement('div');
          div.className = 'c-msg ' + item.role;
          div.textContent = item.text;
          feed.appendChild(div);
        }
        renderedCount = data.chat_feed.length;
        feed.scrollTop = feed.scrollHeight;
      }
    } catch (e) {}
  }
  setInterval(pollCosmosState, 350);

  window.sendToCosmos = async function() {
    const inp = document.getElementById('c-input');
    const prompt = inp.value.trim();
    if (!prompt) return;
    inp.value = '';
    await fetch('/api/command', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ prompt })
    });
  };
})();
</script>
"""


class CosmosUnifiedServer(SimpleHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=FRONTEND_DIR, **kwargs)

    def log_message(self, format, *args):
        pass

    def do_GET(self):
        if self.path == "/api/state":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(COSMOS_STATE).encode("utf-8"))
            return

        if self.path in ["/", "/index.html"]:
            idx = os.path.join(FRONTEND_DIR, "index.html")
            if os.path.exists(idx):
                with open(idx, "r", encoding="utf-8", errors="ignore") as f:
                    html = f.read()
                html = re.sub(r"\bMIRA\b", "COSMOS", html)
                if "cosmos-side-chat" not in html:
                    html = html.replace("</body>", f"{INJECTED_UI_UPGRADES}\n</body>")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(html.encode("utf-8"))
                return

        super().do_GET()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length).decode("utf-8")) if length else {}

        if self.path == "/api/command":
            prompt = body.get("prompt", "")
            COSMOS_STATE["chat_feed"].append({"role": "boss", "text": prompt})
            reply = cosmos_converse_and_stream(prompt)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"response": reply}).encode("utf-8"))


def background_voice_listener_loop():
    time.sleep(1.5)
    if COSMOS_STATE["first_wake"]:
        companion_voice.speak_sentence("Namaste boss, welcome to your world again.")
        COSMOS_STATE["first_wake"] = False

    while True:
        if not COSMOS_STATE["mic_enabled"] or cosmos_listen_full_statement is None:
            time.sleep(0.5)
            continue

        COSMOS_STATE["status"] = "LISTENING"
        spoken = cosmos_listen_full_statement(save_wav=False)
        if not spoken:
            continue

        COSMOS_STATE["chat_feed"].append({"role": "boss", "text": spoken})
        low = spoken.lower().strip()

        if any(w in low for w in ["sleep", "standby", "close cosmos", "goodbye"]):
            companion_voice.speak_sentence(
                "Ok boss, I will wait for you, until your next order."
            )
            COSMOS_STATE["mic_enabled"] = False
            COSMOS_STATE["status"] = "MIC OFF"
            continue

        if low in ["cosmos", "hey cosmos", "wake up"]:
            companion_voice.speak_sentence("Tell me sir, what you want to say?")
            continue

        cosmos_converse_and_stream(spoken)


if __name__ == "__main__":
    PORT = 8080
    print(f"[COSMOS UNIFIED SYSTEM]: Serving './cosmos frontend' at http://127.0.0.1:{PORT}")
    threading.Thread(target=background_voice_listener_loop, daemon=True).start()
    webbrowser.open(f"http://127.0.0.1:{PORT}")
    try:
        HTTPServer(("127.0.0.1", PORT), CosmosUnifiedServer).serve_forever()
    except KeyboardInterrupt:
        pass
