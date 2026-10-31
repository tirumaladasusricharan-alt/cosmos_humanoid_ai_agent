"""
cosmos_power_updates.py - Root Bridge
"""
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
PKG_DIR = os.path.join(BASE, "Jarvis_Setup_Package")
if PKG_DIR not in sys.path:
    sys.path.insert(0, PKG_DIR)

from cosmos_power_updates import (
    copy_code_to_clipboard,
    verify_ast_syntax,
    verify_and_self_heal_python,
    prewarm_ram_models
)
