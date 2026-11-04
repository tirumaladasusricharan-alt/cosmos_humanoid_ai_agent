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

# te-IN-ShrutiNeural handles pure Telugu; en-IN-NeerjaNeural handles Telugu-English mix fluently
VOICE_TELUGU = "te-IN-ShrutiNeural"
VOICE_BILINGUAL_IN = "en-IN-NeerjaNeural"


def detect_language_and_select_voice(text: str) -> str:
    """Automatically detects if the text contains Telugu script or bilingual mix."""
    # Check if text contains Telugu Unicode characters (U+0C00 to U+0C7F)
    if re.search(r"[\u0c00-\u0c7f]", text):
        return VOICE_TELUGU
    return VOICE_BILINGUAL_IN


async def synth_bilingual_ram(text: str) -> bytes:
    voice = detect_language_and_select_voice(text)
    comm = edge_tts.Communicate(
        text, voice, rate="-1%", pitch="+0Hz", volume="+4%"
    )
    buf = io.BytesIO()
    async for chunk in comm.stream():
        if chunk["type"] == "audio":
            buf.write(chunk["data"])
    return buf.getvalue()
