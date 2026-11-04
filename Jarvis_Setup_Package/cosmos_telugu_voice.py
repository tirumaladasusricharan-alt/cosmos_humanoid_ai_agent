"""
cosmos_telugu_voice.py - Bilingual Telugu + English Voice Engine for COSMOS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Zero-Regression & 0 MB Model Storage Architecture
Creator & Sole Authority: Sri Charan Tirumaladasu ("Boss" / "Charan" / "Sir")
"""

import sys
sys.dont_write_bytecode = True

import asyncio
import io
import re
import edge_tts
import pygame

# =====================================================================
# COSMOS TELUGU + ENGLISH BILINGUAL VOICE ENGINE (0 MB DISK USAGE)
# Creator: Sri Charan Tirumaladasu
# =====================================================================

# te-IN-ShrutiNeural handles native Telugu; en-US-AvaNeural is the beloved natural English voice
VOICE_TELUGU = "te-IN-ShrutiNeural"
VOICE_DEFAULT_ENGLISH = "en-US-AvaNeural"


def detect_language_and_select_voice(text: str, default_voice: str = VOICE_DEFAULT_ENGLISH) -> str:
    """Automatically selects native Telugu voice for Telugu script, keeping the beloved previous English voice for everything else."""
    # Check if text contains Telugu Unicode characters (U+0C00 to U+0C7F)
    if re.search(r"[\u0c00-\u0c7f]", text):
        return VOICE_TELUGU
    return default_voice or VOICE_DEFAULT_ENGLISH


async def synth_bilingual_ram(text: str, default_voice: str = VOICE_DEFAULT_ENGLISH) -> bytes:
    voice = detect_language_and_select_voice(text, default_voice)
    comm = edge_tts.Communicate(
        text, voice, rate="+0%", pitch="+0Hz", volume="+0%"
    )
    buf = io.BytesIO()
    async for chunk in comm.stream():
        if chunk["type"] == "audio":
            buf.write(chunk["data"])
    return buf.getvalue()
