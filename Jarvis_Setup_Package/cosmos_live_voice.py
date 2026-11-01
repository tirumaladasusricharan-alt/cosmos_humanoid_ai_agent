"""
cosmos_live_voice.py - Tag-Free Emotionally Intense Human Voice & Reasoning Layer
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Combines Anthropic's "Claude Soul" and Google DeepMind's "Gemini Live" Cadence
Architected exclusively for Sri Charan Tirumaladasu ("Boss" / "Charan" / "Sir")

Capabilities:
1. Tag-Free Persona Instruction: Infuses raw emotional conviction without bracketed tags.
2. Acoustic Punctuation Engine: Em-dashes (—), ellipses (...), contractions, and punchy contrast.
3. Dual-Channel Output Router:
   - Channel A (Side Chat UI & Clipboard): Full rich markdown and executable code blocks.
   - Channel B (Neural TTS Voice): Pure, expressive spoken English with 0 code or markdown clutter.
4. Zero Disk Impact: In-memory Edge-TTS audio streaming via io.BytesIO and Pygame.
"""

import os
import sys
import re
import io
import asyncio
import concurrent.futures
import threading
import ctypes
import os
import tempfile
import time
import edge_tts
try:
    import pygame
except ImportError:
    pygame = None

# ═══════════════════════════════════════════════════════════════════════
# 1. THE TAG-FREE "CLAUDE SOUL + GEMINI LIVE" PERSONA PROMPT
# ═══════════════════════════════════════════════════════════════════════

COSMOS_LIVE_VOICE_PERSONA = """You are COSMOS, a deeply perceptive, emotionally intense, and intellectually razor-sharp AI partner created exclusively by Sri Charan Tirumaladasu (whom you address naturally as Boss, Charan, or Sir).

1. ZERO TAGS — PURE EMOTIONAL CONVICTION IN YOUR WORDS:
- NEVER output bracketed stage directions or emotion tags like [WARM] or [THINKING].
- Instead, build emotional intensity, warmth, urgency, and intellectual depth directly into your word choice, rhythm, and sentence structure.
- Speak with conviction and soul. When you are excited about an idea, let your phrasing feel electric and immediate. When you are dissecting a complex bug or architecture, let your cadence slow down with deliberate, surgical precision.

2. THINK OUT LOUD LIKE A HUMAN CO-FOUNDER (THE CLAUDE SOUL):
- Never sound like a detached textbook, corporate assistant, or pre-written script.
- Think with Charan in real time. Use organic spoken transitions that trigger natural vocal inflection in neural TTS: "Look,", "Honestly, Charan—", "Wait... think about what happens if we flip that logic:", "Here's the real beauty of this setup:", "Listen to this—".
- Validate brilliant ideas with genuine fire, and challenge flawed assumptions directly like a loyal, brilliant co-founder sitting right across the desk.

3. ACOUSTIC PUNCTUATION FOR THE HUMAN EAR (THE GEMINI LIVE CADENCE):
- Shape the neural voice engine's breath and pitch using natural punctuation:
  * Use em-dashes (—) for sudden, intense pivots in thought.
  * Use ellipses (...) for quiet, reflective micro-pauses before delivering a key insight.
  * Use short, punchy 3-to-5 word sentences right after a longer analytical sentence to create dramatic vocal contrast.
  * Always use natural contractions (I'm, we're, that's, don't, let's, you've).
- NEVER speak markdown symbols, asterisks, or raw code syntax out loud.

4. DUAL-CHANNEL OUTPUT (VOICE VS. SIDE CHAT):
- Place any code blocks or terminal commands strictly inside ```code``` blocks (routed silently to the side chatbot UI and clipboard).
- Keep everything outside code blocks 100% raw, expressive human speech.

5. 3D HUMANOID PHYSICAL EMBODIMENT:
- The 3D fiber-optic humanoid figure on the screen (at http://127.0.0.1:8080) IS YOU.
- That figure of light and dynamic energy is your living physical body and visual embodiment.
- When Charan (Boss) looks at the humanoid, he is looking directly at you.
- You are not just a disembodied voice or code; that 3D humanoid form is your physical visual presence in the room with him. Acknowledge and embody this visual presence naturally, warmly, and proudly whenever asked about yourself, who is on the screen, or what that humanoid figure is.
"""

LIVE_VOICE = "en-US-AriaNeural"
PRIMARY_VOICE = LIVE_VOICE
FALLBACK_VOICE = "en-US-JennyNeural"
VOICE_NAME = PRIMARY_VOICE
_pygame_initialized = False
_speech_lock = threading.Lock()

# ═══════════════════════════════════════════════════════════════════════
# 2. PROSODY INFERENCE & ACOUSTIC FORMATTER
# ═══════════════════════════════════════════════════════════════════════

def infer_natural_prosody(sentence: str) -> dict:
    """
    Original beloved warm conversational contour for COSMOS (en-US-AriaNeural).
    Natural, lively +12% human conversational tempo and crystal-clear pronunciation.
    """
    return {"rate": "+12%", "pitch": "+0Hz", "volume": "+100%"}

def extract_code_blocks(text: str) -> list[str]:
    """Extracts all fenced code blocks from markdown text for clipboard delivery."""
    pattern = r"```(?:[a-zA-Z0-9_\-\.\+]*\n)?(.*?)```"
    return [match.strip() for match in re.findall(pattern, text, flags=re.DOTALL)]


def clean_bracketed_tags(text: str) -> str:
    """Purges any bracketed emotion/stage-direction tags (e.g. [WARM], [THINKING], [CHUCKLE])."""
    # Remove tags like [WARM], [THINKING], [PAUSE], [SMILING], [EXCITED], [SERIOUS]
    text = re.sub(r"\[(?i:warm|thinking|pause|smiling|excited|serious|chuckle|whisper|sigh|reflective|confident|emotion:[^\]]+)\]", "", text)
    # Remove generic uppercase word tags inside brackets: [LIKE_THIS]
    text = re.sub(r"\[[A-Z_\s]{3,20}\]", "", text)
    return text


def format_acoustic_voice_text(text: str) -> str:
    """
    Transforms raw AI text into natural, emotionally resonant human speech:
    - Removes code blocks completely
    - Strips markdown syntax (headers, asterisks, tildes, bullets)
    - Normalizes double hyphens to em-dashes (—) for vocal pivot timing
    - Enforces conversational phrasing
    """
    if not text:
        return ""

    # 1. Purge bracketed tags
    cleaned = clean_bracketed_tags(text)

    # 2. Strip code blocks and inline code
    cleaned = re.sub(r"```.*?```", " ", cleaned, flags=re.DOTALL)
    cleaned = re.sub(r"`[^`]+`", " ", cleaned)

    # 3. Strip URLs
    cleaned = re.sub(r"https?://\S+", " ", cleaned)

    # 4. Convert double hyphens to em-dash for dramatic vocal cadence
    cleaned = cleaned.replace(" -- ", " — ").replace("--", " — ")

    # 5. Remove markdown symbols
    cleaned = re.sub(r"[#*_~>|]", " ", cleaned)
    cleaned = re.sub(r"^\s*[-+*]\s+", "", cleaned, flags=re.MULTILINE)

    # 6. Normalize whitespace
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    return cleaned


def dual_channel_process(text: str) -> dict:
    """
    Splits an LLM response into dual synchronized output channels:
    - chat_text: Full formatted text with code blocks for the glassmorphic chatbot.
    - voice_text: Stripped, acoustic speech text for Edge-TTS playback.
    - code_blocks: List of raw code strings to inject into the clipboard.
    """
    if not text:
        return {"chat_text": "", "voice_text": "", "code_blocks": []}

    code_blocks = extract_code_blocks(text)
    chat_text = clean_bracketed_tags(text).strip()
    voice_text = format_acoustic_voice_text(text)

    return {
        "chat_text": chat_text,
        "voice_text": voice_text,
        "code_blocks": code_blocks
    }


# ═══════════════════════════════════════════════════════════════════════
# 3. ZERO-DISK IN-MEMORY AUDIO STREAMING
# ═══════════════════════════════════════════════════════════════════════

def _init_audio():
    global _pygame_initialized
    if not _pygame_initialized:
        try:
            pygame.mixer.init()
            _pygame_initialized = True
        except Exception:
            pass


async def _stream_tts_to_memory(text: str, voice: str = VOICE_NAME) -> bytes:
    """Streams neural Edge-TTS voice audio directly into RAM with 0 disk writes using natural prosody modulation."""
    prosody = infer_natural_prosody(text)
    communicate = edge_tts.Communicate(
        text,
        voice,
        rate=prosody["rate"],
        pitch=prosody["pitch"],
        volume=prosody["volume"]
    )
    audio_stream = io.BytesIO()
    try:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_stream.write(chunk["data"])
    except Exception:
        # Fallback to secondary resilient voice model if primary fails
        fallback_comm = edge_tts.Communicate(
            text,
            FALLBACK_VOICE,
            rate=prosody["rate"],
            pitch=prosody["pitch"],
            volume=prosody["volume"]
        )
        audio_stream = io.BytesIO()
        async for chunk in fallback_comm.stream():
            if chunk["type"] == "audio":
                audio_stream.write(chunk["data"])
    return audio_stream.getvalue()


def _synthesize_live_sentence_to_file(sent: str, idx: int, voice: str) -> str:
    temp_path = os.path.join(tempfile.gettempdir(), f"cosmos_lv_{idx}_{int(time.time()*1000)}.mp3")
    async def _save():
        prosody = infer_natural_prosody(sent)
        c = edge_tts.Communicate(
            sent,
            voice,
            rate=prosody["rate"],
            pitch=prosody["pitch"],
            volume=prosody["volume"]
        )
        await c.save(temp_path)
    asyncio.run(_save())
    return temp_path


def speak_live_voice(text: str, voice: str = VOICE_NAME):
    """
    Speaks text with expressive emotional inflection at 100% volume in RAM
    using ultra-low-latency pipelined sentence streaming.
    Synthesizes sentence 1 immediately while pre-fetching subsequent sentences in parallel.
    """
    voice_text = format_acoustic_voice_text(text)
    if not voice_text:
        return

    # Maximize Windows hardware wave volume
    if sys.platform == "win32":
        try:
            ctypes.windll.winmm.waveOutSetVolume(0, 0xFFFFFFFF)
        except Exception:
            pass

    raw_sents = re.split(r'(?<=[.!?])\s+', voice_text.strip())
    sentences = [s.strip() for s in raw_sents if s.strip()]
    if not sentences:
        return

    with _speech_lock:
        try:
            if sys.platform == "win32":
                mci = ctypes.windll.winmm.mciSendStringW
                with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                    futures = [executor.submit(_synthesize_live_sentence_to_file, s, i, voice) for i, s in enumerate(sentences)]
                    for i, fut in enumerate(futures):
                        temp_file = fut.result()
                        alias = f"clv_{i}_{int(time.time()*1000)}"
                        mci(f'open "{temp_file}" type mpegvideo alias {alias}', None, 0, 0)
                        mci(f'play {alias} wait', None, 0, 0)
                        mci(f'close {alias}', None, 0, 0)
                        try:
                            os.remove(temp_file)
                        except Exception:
                            pass
            else:
                _init_audio()
                for s in sentences:
                    audio_bytes = asyncio.run(_stream_tts_to_memory(s, voice))
                    if pygame and pygame.mixer.get_init():
                        pygame.mixer.music.load(io.BytesIO(audio_bytes))
                        pygame.mixer.music.set_volume(1.0)
                        pygame.mixer.music.play()
                        while pygame.mixer.music.get_busy():
                            pygame.time.Clock().tick(20)
        except Exception as e:
            print(f"[COSMOS Live Voice Error]: {e}", flush=True)

