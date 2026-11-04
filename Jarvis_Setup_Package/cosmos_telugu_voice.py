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

TELUGU_WORDS = {
    # Pronouns & People
    'nenu', 'nuvvu', 'nuvva', 'meeru', 'manam', 'atanu', 'aame', 'vaaru', 'vaallu', 'aadu',
    'idi', 'adi', 'evi', 'avi', 'evaru', 'emiti', 'enti', 'endi', 'emi', 'em',
    # Question words
    'ela', 'elaa', 'ekkada', 'eppudu', 'enduku', 'enni', 'enta', 'edhi',
    # Common verbs & states
    'unnav', 'vunnav', 'unnaru', 'vunnaru', 'unna', 'unnanu', 'undhi', 'undi', 'unnayi',
    'cheppu', 'cheppandi', 'cheppava', 'cheppave', 'cheppanu', 'cheppali',
    'chestunnav', 'chesthunnav', 'chestunnavu', 'chestunnam', 'cheddam', 'cheyyali', 'cheyali',
    'chesanu', 'chey', 'cheyyi', 'chudu', 'chudandi', 'vinu', 'vinandi',
    'ravali', 'ravadam', 'vellu', 'vellandi', 'poyi', 'ivvu', 'ivvandi', 'tesuko',
    'telsu', 'telusu', 'teliyadu', 'raadu', 'ledu', 'vaddu', 'kavali',
    # Well-being, greetings & markers
    'bagunnava', 'bagunara', 'bagunnanu', 'baagundi', 'bagundi', 'manchidi', 'manchide',
    'sare', 'avunu', 'kaadu', 'kadu', 'ayithe', 'avuna', 'visheshalu', 'sangathi', 'sangathulu',
    'namaste', 'namaskaram', 'ivvala', 'repu', 'ninna', 'ippudu', 'eppudu', 'chala', 'koncham',
    'malli', 'inka', 'kuda', 'gurinchi', 'ante', 'ani', 'kikiki', 'ra', 'andi', 'garu',
    'ayya', 'amma', 'anna', 'thammudu', 'akki', 'babu'
}


def is_telugu_query(text: str) -> bool:
    """Detects whether Sri Charan Tirumaladasu spoke or typed in Telugu."""
    if not text:
        return False
    # 1. Telugu Unicode characters (U+0C00 - U+0C7F)
    if re.search(r'[\u0c00-\u0c7f]', text):
        return True
    # 2. Match Telugu Romanized words / tokens
    words = re.findall(r'[a-zA-Z]+', text.lower())
    return sum(1 for w in words if w in TELUGU_WORDS) >= 1


def detect_language_and_select_voice(text: str, default_voice: str = VOICE_DEFAULT_ENGLISH) -> str:
    """If text is in Telugu (script or words), select te-IN-ShrutiNeural so she pronounces Telugu fluently!
    Otherwise, use the beloved previous English voice.
    """
    if is_telugu_query(text):
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
