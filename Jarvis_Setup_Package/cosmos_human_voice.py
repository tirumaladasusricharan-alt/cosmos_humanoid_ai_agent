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

VOICE = "en-US-EmmaMultilingualNeural"
RATE = "+20%"
PITCH = "+0Hz"
WINDOWS_VOLUME_BOOST = 1.2
MAX_WINDOWS_VOLUME = round(0xFFFF * 0.7)

_playback_lock = threading.Lock()
_synthesis_executor = ThreadPoolExecutor(max_workers=2)


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
    communicator = edge_tts.Communicate(
        text,
        VOICE,
        rate=RATE,
        pitch=PITCH,
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
        if not pygame.mixer.get_init():
            pygame.mixer.init()
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

    previous_output_volume = None
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        import jarvis_voice

        if not preloaded:
            pygame.mixer.music.load(audio, namehint="mp3")
        if sys.platform == "win32":
            previous_output_volume = jarvis_voice._get_windows_output_volume()
            left = previous_output_volume & 0xFFFF
            right = (previous_output_volume >> 16) & 0xFFFF
            left = max(
                left, min(MAX_WINDOWS_VOLUME, int(left * WINDOWS_VOLUME_BOOST))
            )
            right = max(
                right, min(MAX_WINDOWS_VOLUME, int(right * WINDOWS_VOLUME_BOOST))
            )
            jarvis_voice._set_windows_output_volume(left | (right << 16))
        pygame.mixer.music.set_volume(1.0)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.05)
    finally:
        try:
            try:
                pygame.mixer.music.stop()
            finally:
                if previous_output_volume is not None:
                    jarvis_voice._set_windows_output_volume(previous_output_volume)
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
