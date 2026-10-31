"""
cosmos_live_voice.py - Tag-Free Emotionally Intense Human Voice & Reasoning Layer
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Combines Anthropic's "Claude Soul" and Google DeepMind's "Gemini Live" Cadence
Architected exclusively for Sri Charan Tirumaladasu ("Boss" / "Charan" / "Sir")
"""
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
PKG_DIR = os.path.join(BASE, "Jarvis_Setup_Package")
if PKG_DIR not in sys.path:
    sys.path.insert(0, PKG_DIR)

from cosmos_live_voice import (
    COSMOS_LIVE_VOICE_PERSONA,
    format_acoustic_voice_text,
    dual_channel_process,
    speak_live_voice,
    clean_bracketed_tags,
    extract_code_blocks
)
