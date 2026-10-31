# 🌌 COSMOS - Autonomous 3D Humanoid AI Agent

> **Architected & Built by Sri Charan Tirumaladasu**  
> *An OS-level, voice-first autonomous executive AI assistant featuring a real-time WebGL 3D Humanoid avatar, multi-brain dual reasoning (Council Mode with DeepSeek-R1 + Qwen2.5-Coder), ultra-fast cloud failover, and hardware-level automation.*

---

## 🌟 Key Features

- **3D WebGL Humanoid Avatar:**
  - Interactive, dynamic particles-to-body assembly.
  - Luminescence and head/face glow reactive to oral speech (`talking`, `listening`, `idle`).
  - Seamless, camouflaged glassmorphism HUD chat with wake-word instant summon.

- **Multi-Brain & Dual Reasoning (Council Mode):**
  - **Local Ollama Inference:** Auto-discovers local models (`deepseek-r1:8b`, `qwen2.5-coder:7b`, `qwen2.5:latest`).
  - **Council Mode:** Pass 1 architectural logic & blueprinting via DeepSeek-R1; Pass 2 verified polyglot implementation via Qwen2.5-Coder.
  - **Ultra-Fast Cloud Failover:** Groq integration delivering ~1.2s sub-second responses with zero token crashes and anti-fragmentation guards.

- **Voice & Auditory Intelligence:**
  - High-sensitivity oral listener (`pause_threshold = 0.5s`) detecting whisper, conversational, and soft speech.
  - Direct Indian English (`en-IN`) single-pass Google STT with multi-language fallback.
  - Crisp, natural speech output via Edge-TTS neural voice (`rate="+12%"`, `volume="+100%"`).

- **Full OS Automation & Productivity:**
  - Desktop application launch and termination via native Windows APIs.
  - Real-time zero-cost web search and browser ground truth extraction.
  - Phone Link, WhatsApp automation, system audio controls, OCR screen inspection.

---

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.10 - 3.14
- (Optional) [Ollama](https://ollama.ai) installed with `deepseek-r1:8b` or `qwen2.5-coder:7b` for offline council mode.

### 2. Setup & Installation
```bash
# Clone the repository
git clone https://github.com/tirumaladasusricharan-alt/cosmos_humanoid_ai_agent.git
cd cosmos_humanoid_ai_agent/Jarvis_Setup_Package

# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\activate

# Install required dependencies
pip install -r requirements.txt

# Configure your free Groq API key in .env
cp .env.example .env
# Edit .env and paste: GROQ_API_KEY=your_key_here
```

### 3. Launch COSMOS
Double-click `start_jarvis.bat` or run:
```cmd
start_jarvis.bat
```
COSMOS will initialize on `http://127.0.0.1:8080` and open the 3D Humanoid HUD!

---

## 🎙️ Spoken Wake Words & Hotkeys

- **Spoken Wake Words:** *"COSMOS"*, *"Hey COSMOS"*, *"OK COSMOS"*
- **Global Hotkey:** `Alt` or `Alt + Space` to summon COSMOS to the foreground instantly.
- **Close Command:** *"close yourself"* or *"minimize"*
- **Settings:** *"open sound settings"* or *"microphone sensitivity"*

---

## 🛡️ License & Authorship
Created by **Sri Charan Tirumaladasu** (Co-founder, Garuda Software Solutions).  
Protected under the MIT License.
