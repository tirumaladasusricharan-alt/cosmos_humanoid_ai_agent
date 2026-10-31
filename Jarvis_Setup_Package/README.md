# ⚡ COSMOS AI Personal Assistant - Complete Setup

> **A real voice-controlled AI executive assistant for your computer.**
> Features voice app launching, YouTube playback, WhatsApp automation, email briefings, live stock market analysis (Buy/Sell calls), rate-limit failover, and a 3D holographic Iron Man HUD!

---

## 🚀 Quick Start (In 60 Seconds)

### On Windows:
Run these commands from the project folder:
```cmd
py -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
start_jarvis.bat
```

---

## 🎙️ Voice Commands Cheat-Sheet

| What You Say | What COSMOS Does |
| :--- | :--- |
| `"COSMOS, open VS Code"` | Launches Visual Studio Code instantly |
| `"COSMOS, open Antigravity"` | Launches local Antigravity IDE/CLI with browser fallback |
| `"COSMOS, open [site] in browser"` | Smart resolution for any website (known platforms, spoken dot, or lucky launch) |
| `"COSMOS, open [app name]"` | Launches a matching installed Start Menu app |
| `"COSMOS, close Chrome"` | Closes the matching app window; say "force close" to terminate it |
| `"Search the web for [topic]"` | Opens a Google search in your default browser |
| `"Open example.com"` | Opens the website in your default browser |
| `"Play lofi on YouTube"` | Opens YouTube and starts playing lofi music |
| `"Stock market report"` | Analyzes Nifty, Sensex, Reliance, Nvidia & crypto |
| `"Should I buy Reliance?"` | Checks moving averages and gives Buy/Sell advice |
| `"Check my unread emails"` | Reads your unread mail and provides a 30s briefing |
| `"Send WhatsApp message to Pallavi"` | Opens WhatsApp Web and drafts a message |
| `"Volume up" / "Mute"` | Adjusts your system volume hands-free |

### Screen and voice controls

- **SCREEN** captures the primary display and runs local Windows OCR. A
  screen-related question such as "can you see my screen?" also triggers OCR.
  The overlay shows `[SCREEN OCR READ ... CHARACTERS]` after text is extracted.
  Extracted text is sent with the question to Groq and is not saved to chat
  history.
- Voice input starts automatically when COSMOS launches. Say **"COSMOS"**,
  **"Hey COSMOS"**, or **"OK COSMOS"** to bring up the overlay, or say one of
  those wake phrases followed by a command to open it and
  run that command. Voice close commands hide the overlay while leaving
  voice wake active, so you can say **"COSMOS"** to open it again.
- **MIC OFF / MIC ON** disables or enables voice wake and voice commands. While
  enabled, the listener stays active across commands and speech playback and
  retries transient recognition or microphone errors. Speech recognition uses
  Google's online recognizer; replies use the Emma Edge neural voice at a
  20% faster rate, with synthesis completed before the reply is displayed when
  it finishes within four seconds. Playback
  volume is boosted on Windows and the previous system volume is restored
  afterward. Local text-to-speech uses a female voice as a fallback. Run
  `.venv\Scripts\python.exe cosmos_human_voice.py` to play a voice check.
- App launching uses installed Start Menu apps, shortcuts, or known app aliases;
  web searches and addresses open in the default browser. Windows app launch
  and close requests use hidden, parameterized PowerShell; COSMOS does not run
  arbitrary Command Prompt or PowerShell commands. Requests to close protected
  Windows processes or the COSMOS process are blocked.
- COSMOS response messages include a **COPY** action. Fenced or recognized
  multiline technical output is shown in a code container with **COPY CODE**.
  Use **COPY LAST** or `Ctrl+Shift+C` to copy the latest response.
- `start_jarvis.bat` restarts existing COSMOS overlay instances so code updates
  are loaded when the launcher is run.

---

## 🛡️ Best Part: Hybrid Failover (Zero Crashes)
When cloud LLMs hit daily token limits or rate limits (HTTP 429), standard assistants crash and give error messages. 
COSMOS has an **Automatic Cooldown & Local Fallback Engine**:
- Detects the exact rate-limit duration.
- Switches instantly to offline local code.
- Executes your commands locally without interruption!

---

## 🌐 Holographic Iron Man HUD
Double click `jarvis_workplace.html` in your browser to experience the glowing cyber reactor core, animated globe, live voice audio visualizer, and live market quotes.
