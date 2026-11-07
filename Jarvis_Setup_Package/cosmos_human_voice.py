"""Human-sounding COSMOS speech using Edge neural TTS and in-memory playback."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
import re
import sys
import threading
import time

import edge_tts
import pygame

VOICE = "en-US-AvaNeural"
RATE = "+0%"
PITCH = "+0Hz"
VOICE_VOLUME = "+100%"
WINDOWS_VOLUME_BOOST = 1.0
MAX_WINDOWS_VOLUME = 0xFFFF

_playback_lock = threading.Lock()
_synthesis_executor = ThreadPoolExecutor(max_workers=2)


def _init_audio():
    """Initializes pygame mixer at 24000 Hz to match Edge-TTS native output."""
    if not pygame.mixer.get_init():
        try:
            pygame.mixer.init(frequency=24000, size=-16, channels=2, buffer=2048)
        except Exception:
            try:
                pygame.mixer.init()
            except Exception:
                pass


def ensure_windows_audio_master(min_volume: float = 0.90):
    """
    Disabled by creator order: COSMOS strictly respects user's manual Windows audio settings.
    Never alters, unmutes, or overrides the user's master volume slider or mute state.
    """
    pass


def humanize_spoken_text(text):
    """Remove formatting and normalize text for natural spoken delivery."""
    text = re.sub(r"```[\s\S]*?```", " ", text)
    text = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"<https?://[^>]+>", " ", text)
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)
    text = re.sub(r"(?m)^\s{0,3}#{1,6}\s*", "", text)
    text = re.sub(r"(?m)^\s*(?:[-*+]|\d+[.)])\s+", "", text)
    text = re.sub(r"[*_`#~]+", "", text)
    text = re.sub(r"[<>|{}\[\]]", " ", text)
    text = re.sub(r"[:;]\s*", ", ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\s*\n\s*", ". ", text)
    text = re.sub(r"(?:\.\s*){3,}", "... ", text)
    text = re.sub(r"\s+([,.!?])", r"\1", text)
    text = re.sub(r"([,.!?])(?=\S)", r"\1 ", text)
    return text.strip(" ,.")


async def _synthesize(text):
    audio = BytesIO()
    voice_to_use = VOICE
    try:
        from cosmos_telugu_voice import detect_language_and_select_voice
        voice_to_use = detect_language_and_select_voice(text)
    except Exception:
        pass
    communicator = edge_tts.Communicate(
        text,
        voice_to_use,
        rate=RATE,
        pitch=PITCH,
        volume=VOICE_VOLUME,
    )
    async for chunk in communicator.stream():
        if chunk["type"] == "audio":
            audio.write(chunk["data"])
    if not audio.getbuffer().nbytes:
        raise RuntimeError("Edge TTS returned no audio.")
    audio.seek(0)
    return audio


def prepare_speech(text):
    """Begin neural speech generation while the UI prepares the reply."""
    spoken_text = humanize_spoken_text(text)
    if not spoken_text:
        return None
    return _synthesis_executor.submit(_synthesize_and_load, spoken_text)


def _synthesize_and_load(text):
    audio = asyncio.run(_synthesize(text))
    _playback_lock.acquire()
    try:
        _init_audio()
        pygame.mixer.music.load(audio, namehint="mp3")
    except Exception:
        _playback_lock.release()
        raise
    return audio


def _speak_with_edge_tts(text, prepared_audio=None):
    preloaded = prepared_audio is not None
    if preloaded:
        prepared_audio.result()
    else:
        audio = asyncio.run(_synthesize(text))
        _playback_lock.acquire()

    try:
        _init_audio()
        if not preloaded:
            pygame.mixer.music.load(audio, namehint="mp3")
        pygame.mixer.music.set_volume(1.0)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.05)
    finally:
        try:
            pygame.mixer.music.stop()
        finally:
            _playback_lock.release()


def cosmos_speak(text, prepared_audio=None):
    """Speak COSMOS text with Edge TTS, falling back to the existing local TTS."""
    spoken_text = humanize_spoken_text(text)
    if not spoken_text:
        return
    try:
        _speak_with_edge_tts(spoken_text, prepared_audio)
    except Exception as error:
        print(f"[COSMOS VOICE ERROR] Edge TTS failed; using local speech: {error}")
        import jarvis_voice

        jarvis_voice.speak(spoken_text)


def cosmos_vibe_check():
    """Play a short, conversational voice test."""
    cosmos_speak(
        "Hey, Charan... COSMOS is online, feeling sharp, and right here with you. "
        "How's the vibe? Everything's running smooth, so let's make today count."
    )


if __name__ == "__main__":
    cosmos_vibe_check()
